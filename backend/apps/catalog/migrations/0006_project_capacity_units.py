from decimal import Decimal

from django.db import migrations
from django.db.models.deletion import ProtectedError

# Exact labels from src/data/opportunities.ts metric.unit; no inferred conversion.
UNITS = {
    "ROOM": "اتاق",
    "STATION": "ایستگاه",
    "BARREL": "بشکه",
    "BED": "تخت",
    "TONNE": "تن",
    "STALL": "جایگاه",
    "VEHICLE": "خودرو",
    "ANIMAL_HEAD": "راس",
    "SITE": "سایت",
    "SEAT": "صندلی",
    "METRE": "متر",
    "SQUARE_METRE": "مترمربع",
    "CUBIC_METRE": "مترمکعب",
    "PASSENGER": "مسافر",
    "MEGAWATT": "مگاوات",
    "MEGAVOLT_AMPERE": "مگاولت\u200cآمپر",
    "MILLION_CUBIC_METRE": "میلیون مترمکعب",
    "PERSON": "نفر",
    "POINT": "نقطه",
    "HECTARE": "هکتار",
    "POLE": "پایه",
    "KILOMETRE": "کیلومتر",
}


def seed(apps, schema_editor):
    Unit = apps.get_model("catalog", "UnitDefinition")
    Field = apps.get_model("catalog", "FieldDefinition")
    for code in UNITS:
        if code != "SQUARE_METRE":
            Unit.objects.create(
                code=code,
                version=1,
                kind="quantity",
                base_code=code,
                base_version=1,
                currency="",
                factor=Decimal("1"),
            )
    Field.objects.create(
        namespace="invest.opportunity.project",
        key="metric_quantity",
        version=2,
        label="مقدار ظرفیت",
        kind="quantity",
        unit=Unit.objects.get(code="ITEM", version=1),
        allowed_units=[{"code": c, "version": 1} for c in ["ITEM", "KILOGRAM", *UNITS]],
        minimum=Decimal("0"),
        maximum=Decimal("999999999999999999999999.999999999"),
        decimal_places=9,
        source_path="src/data/opportunities.ts",
        source_locator="Opportunity.metric.value/unit; src/lib/facts.ts:44",
        meaning="ظرفیت با واحد صریح منبع؛ بدون تبدیل حدسی میان واحدها.",
        visibility_rule="always",
        inactive_effect="exclude",
    )


def unseed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit = apps.get_model("catalog", "UnitDefinition")
    with schema_editor.connection.cursor() as cursor:
        # Flush outstanding FK events and check subsequent deletes immediately before
        # changing triggers. This mode is local to this atomic migration transaction.
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("ALTER TABLE catalog_fielddefinition DISABLE TRIGGER immutable_field")
        cursor.execute("ALTER TABLE catalog_unitdefinition DISABLE TRIGGER immutable_unit")
        removed_fields = Field.objects.filter(
            namespace="invest.opportunity.project", key="metric_quantity", version=2
        )
        retained = Field.objects.exclude(pk__in=removed_fields.values("pk"))
        for code in UNITS:
            if code == "SQUARE_METRE":
                continue
            consumers = retained.filter(allowed_units__contains=[{"code": code, "version": 1}])
            if consumers.exists():
                raise ProtectedError(
                    "Rollback unit is referenced by retained definitions", consumers
                )
        removed_fields.delete()
        Unit.objects.filter(code__in=[c for c in UNITS if c != "SQUARE_METRE"], version=1).delete()
        cursor.execute("ALTER TABLE catalog_fielddefinition ENABLE TRIGGER immutable_field")
        cursor.execute("ALTER TABLE catalog_unitdefinition ENABLE TRIGGER immutable_unit")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_project_fields")]
    operations = [migrations.RunPython(seed, unseed)]
