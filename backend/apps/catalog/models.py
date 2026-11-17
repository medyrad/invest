from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import F, Q

from .decimal_field import ExactDecimalField
from .values import MAX_VALUE, ValueErrorDetail, decimal_string, input_from_dto, normalize


class SourceRow(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    name = models.CharField(max_length=200)
    source_version = models.CharField(max_length=80)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["position", "id"]


class Group(SourceRow):
    metadata = models.JSONField(default=dict)


class Subtype(SourceRow):
    group = models.ForeignKey(Group, on_delete=models.PROTECT, related_name="subtypes")
    raw_id = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict)

    class Meta(SourceRow.Meta):
        constraints = [
            models.UniqueConstraint(fields=["group", "raw_id"], name="catalog_group_subtype_unique")
        ]


class Province(SourceRow):
    pass


class County(SourceRow):
    province = models.ForeignKey(Province, on_delete=models.PROTECT, related_name="counties")

    class Meta(SourceRow.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["province", "name"], name="catalog_province_county_unique"
            )
        ]


class City(SourceRow):
    county = models.ForeignKey(County, on_delete=models.PROTECT, related_name="cities")

    class Meta(SourceRow.Meta):
        constraints = [
            models.UniqueConstraint(fields=["county", "name"], name="catalog_county_city_unique")
        ]


KINDS = [("money", "مبلغ"), ("quantity", "مقدار"), ("return", "بازده")]


class ImmutableDefinition(models.Model):
    version = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("تعریف منتشرشده تغییر نمی‌کند؛ نسخه تازه بسازید.")
        self.full_clean()
        return super().save(*args, **kwargs)


class UnitDefinition(ImmutableDefinition):
    code = models.CharField(max_length=80)
    kind = models.CharField(max_length=10, choices=KINDS)
    base_code = models.CharField(max_length=80)
    base_version = models.PositiveIntegerField(default=1)
    currency = models.CharField(max_length=16, blank=True)
    factor = ExactDecimalField()

    class Meta:
        ordering = ["code", "version"]
        constraints = [
            models.UniqueConstraint(fields=["code", "version"], name="catalog_unit_version_unique"),
            models.CheckConstraint(
                condition=Q(
                    version__gte=1, version__lte=9999, base_version__gte=1, base_version__lte=9999
                ),
                name="catalog_unit_versions",
            ),
            models.CheckConstraint(
                condition=Q(factor__gt=0, factor__lte=MAX_VALUE, factor__scale__lte=9),
                name="catalog_unit_exact_factor",
            ),
            models.CheckConstraint(
                condition=Q(kind="money", base_code=F("currency"))
                | Q(kind__in=["quantity", "return"], currency=""),
                name="catalog_unit_currency",
            ),
        ]

    def clean(self):
        if self.kind == "money" and (not self.currency or self.base_code != self.currency):
            raise ValidationError("ارز اصلی حفظ می‌شود؛ تبدیل ارز خودکار مجاز نیست.")

    def as_dict(self):
        return {
            "code": self.code,
            "version": self.version,
            "kind": self.kind,
            "base_code": self.base_code,
            "base_version": self.base_version,
            "currency": self.currency or None,
            "factor": decimal_string(self.factor),
        }


class FieldDefinition(ImmutableDefinition):
    namespace = models.CharField(max_length=120)
    key = models.CharField(max_length=80)
    label = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=KINDS)
    unit = models.ForeignKey(UnitDefinition, on_delete=models.PROTECT)
    return_type = models.CharField(max_length=20, blank=True)
    allowed_units = models.JSONField()
    minimum = ExactDecimalField(default=Decimal("0"))
    maximum = ExactDecimalField(default=MAX_VALUE)
    decimal_places = models.PositiveSmallIntegerField(default=9)
    required = models.BooleanField(default=False)
    allow_unknown = models.BooleanField(default=True)
    allow_not_applicable = models.BooleanField(default=True)
    source_path = models.CharField(max_length=300)
    source_locator = models.CharField(max_length=300)
    meaning = models.TextField()
    visibility_rule = models.CharField(max_length=300, default="future-form-owned")
    inactive_effect = models.CharField(max_length=16, default="exclude")

    class Meta:
        ordering = ["namespace", "key", "version"]
        constraints = [
            models.UniqueConstraint(
                fields=["namespace", "key", "version"], name="catalog_field_version_unique"
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1, version__lte=9999, decimal_places__lte=9),
                name="catalog_field_limits",
            ),
            models.CheckConstraint(
                condition=Q(
                    minimum__gte=MAX_VALUE.copy_negate(),
                    maximum__lte=MAX_VALUE,
                    minimum__lte=F("maximum"),
                    minimum__scale__lte=9,
                    maximum__scale__lte=9,
                ),
                name="catalog_field_range",
            ),
        ]

    def clean(self):
        import re

        try:
            _ = self.unit
        except ObjectDoesNotExist as exc:
            raise ValidationError("واحد تعریف فیلد را مشخص کنید.") from exc
        if self.minimum is None or self.maximum is None:
            raise ValidationError("حدود فیلد را صریح مشخص کنید.")

        if not re.fullmatch(
            r"[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*)+", self.namespace
        ) or not re.fullmatch(r"[a-z][a-z0-9_]*", self.key):
            raise ValidationError("namespace و کلید معنایی فیلد معتبر نیست.")
        if (
            self.kind == "return"
            and self.return_type not in ("irr", "simple_rate", "effective_rate")
            or self.kind != "return"
            and self.return_type
        ):
            raise ValidationError("نوع بازده باید با معنای فیلد تعریف شود.")
        if self.unit.kind != self.kind or self.inactive_effect != "exclude":
            raise ValidationError("نوع واحد یا اثر مقدار غیرفعال معتبر نیست.")
        if not isinstance(self.allowed_units, list) or not self.allowed_units:
            raise ValidationError("واحدهای مجاز را صریح مشخص کنید.")
        for ref in self.allowed_units:
            from .values import check_ref

            try:
                check_ref(ref, ("code", "version"), "allowed_units")
            except ValueErrorDetail as e:
                raise ValidationError(e.message) from e
            if not UnitDefinition.objects.filter(**ref, kind=self.kind).exists():
                raise ValidationError("واحد مجاز باید تعریف نسخه‌دار هم‌نوع داشته باشد.")
        if {"code": self.unit.code, "version": self.unit.version} not in self.allowed_units:
            raise ValidationError("واحد پیش‌فرض در واحدهای مجاز نیست.")
        if self.kind != "return" and self.minimum < 0:
            raise ValidationError("مبلغ یا مقدار این بسته غیرمنفی است.")

    def reference(self):
        return {"namespace": self.namespace, "key": self.key, "version": self.version}

    def as_dict(self):
        return {
            **self.reference(),
            "label": self.label,
            "kind": self.kind,
            "unit": {"code": self.unit.code, "version": self.unit.version},
            "allowed_units": self.allowed_units,
            "return_type": self.return_type or None,
            "minimum": decimal_string(self.minimum),
            "maximum": decimal_string(self.maximum),
            "decimal_places": self.decimal_places,
            "required": self.required,
            "allow_unknown": self.allow_unknown,
            "allow_not_applicable": self.allow_not_applicable,
            "source_path": self.source_path,
            "source_locator": self.source_locator,
            "meaning": self.meaning,
            "visibility_rule": self.visibility_rule,
            "inactive_effect": self.inactive_effect,
        }


class ExactValue(models.Model):
    definition = models.ForeignKey(FieldDefinition, on_delete=models.PROTECT)
    unit = models.ForeignKey(UnitDefinition, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=16, choices=[(x, x) for x in ("known", "unknown", "not_applicable")]
    )
    value = ExactDecimalField(null=True, blank=True)
    source_value = ExactDecimalField(null=True, blank=True)
    conversion_factor = ExactDecimalField()
    base_unit = models.CharField(max_length=80)
    base_version = models.PositiveIntegerField()
    basis = models.JSONField(null=True, blank=True)

    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                condition=Q(status="known", value__isnull=False, source_value__isnull=False)
                | Q(
                    status__in=["unknown", "not_applicable"],
                    value__isnull=True,
                    source_value__isnull=True,
                ),
                name="%(class)s_state",
            ),
            models.CheckConstraint(
                condition=Q(value__isnull=True)
                | Q(
                    value__gte=MAX_VALUE.copy_negate(),
                    value__lte=MAX_VALUE,
                    value__scale__lte=9,
                    source_value__gte=MAX_VALUE.copy_negate(),
                    source_value__lte=MAX_VALUE,
                    source_value__scale__lte=9,
                    value=F("source_value") * F("conversion_factor"),
                ),
                name="%(class)s_exact",
            ),
            models.CheckConstraint(
                condition=Q(
                    conversion_factor__gt=0,
                    conversion_factor__lte=MAX_VALUE,
                    conversion_factor__scale__lte=9,
                    base_version__gte=1,
                ),
                name="%(class)s_factor",
            ),
        ]

    @classmethod
    def from_payload(cls, payload):
        dto = normalize(payload)
        definition = FieldDefinition.objects.get(**dto["field"])
        if definition.kind != cls.value_kind:
            raise ValidationError("نوع فیلد با نوع رکورد یکسان نیست.")
        return cls(
            definition=definition,
            unit=UnitDefinition.objects.get(**dto["unit"]),
            status=dto["status"],
            value=Decimal(dto["value"]) if dto["value"] is not None else None,
            source_value=Decimal(dto["source_value"]) if dto["source_value"] is not None else None,
            conversion_factor=Decimal(dto["conversion_factor"]),
            base_unit=dto["base_unit"],
            base_version=dto["base_version"],
            basis=dto["basis"],
        )

    def as_dict(self):
        return {
            "contract_version": 1,
            "kind": self.value_kind,
            "field": self.definition.reference(),
            "unit": {"code": self.unit.code, "version": self.unit.version},
            "status": self.status,
            "source_value": decimal_string(self.source_value)
            if self.source_value is not None
            else None,
            "value": decimal_string(self.value) if self.value is not None else None,
            "conversion_factor": decimal_string(self.conversion_factor),
            "base_unit": self.base_unit,
            "base_version": self.base_version,
            "basis": self.basis,
        }

    def clean(self):
        try:
            _ = self.definition
            _ = self.unit
        except ObjectDoesNotExist as exc:
            raise ValidationError("تعریف نسخه‌دار فیلد و واحد را مشخص کنید.") from exc
        if self.conversion_factor is None or not self.base_unit or self.base_version is None:
            raise ValidationError("مقدار را با قرارداد کامل و ضریب صریح ثبت کنید.")
        if self.definition.kind != self.value_kind:
            raise ValidationError("نوع رکورد با معنای فیلد یکسان نیست.")
        try:
            dto = self.as_dict()
            # Check precision before canonical formatting can remove trailing zeroes.
            if self.source_value is not None:
                source = self.source_value
                if not isinstance(source, Decimal):
                    raise ValidationError("مقدار ذخیره‌شده باید Decimal دقیق باشد.")
                dto["source_value"] = format(source, "f")
            expected = normalize(input_from_dto(dto))
            canonical = self.as_dict()
            if expected != canonical:
                raise ValidationError("مقدار یا ضریب ذخیره با تعریف نسخه‌دار سازگار نیست.")
        except ValueErrorDetail as e:
            raise ValidationError({e.field: e.message}) from e

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class MoneyValue(ExactValue):
    value_kind = "money"


class Quantity(ExactValue):
    value_kind = "quantity"


class ReturnMetric(ExactValue):
    value_kind = "return"
