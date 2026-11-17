from decimal import Decimal

from django.db import migrations

# Frozen v1 definitions: never import the live registry into a historical migration.
UNITS = [
    ("TOMAN", "money", "TOMAN", "TOMAN", "1"),
    ("MILLION_TOMAN", "money", "TOMAN", "TOMAN", "1000000"),
    ("BILLION_TOMAN", "money", "TOMAN", "TOMAN", "1000000000"),
    ("USD", "money", "USD", "USD", "1"),
    ("SQUARE_METRE", "quantity", "SQUARE_METRE", "", "1"),
    ("KILOGRAM", "quantity", "KILOGRAM", "", "1"),
    ("ITEM", "quantity", "ITEM", "", "1"),
    ("MONTH", "quantity", "MONTH", "", "1"),
    ("YEAR", "quantity", "YEAR", "", "1"),
    ("DAY", "quantity", "DAY", "", "1"),
    ("PERCENT", "return", "PERCENT", "", "1"),
]
FIELDS = [
    (
        "project",
        "min_capital",
        "money",
        "BILLION_TOMAN",
        "Opportunity.minCapital; types/index.ts:41-42; lib/listings.ts:20-21",
        "حداقل سرمایه ورود پروژه؛ با نیاز مالی کل طرح یکی نیست.",
        True,
    ),
    (
        "project",
        "budget",
        "money",
        "BILLION_TOMAN",
        "Opportunity.budget; types/index.ts:43-44; lib/listings.ts:20-21",
        "نیاز مالی کل طرح؛ fallback نمایش به alias داده تبدیل نمی\u200cشود.",
        False,
    ),
    (
        "project",
        "monthly_rent",
        "money",
        "MILLION_TOMAN",
        "Opportunity.monthlyRent; types/index.ts:81-82",
        "اجاره ماهانه به میلیون تومان؛ با ودیعه یا قیمت کل جمع/معادل نمی\u200cشود.",
        False,
    ),
    (
        "fund",
        "minimum_investment",
        "money",
        "MILLION_TOMAN",
        "Fund.minimumMillion; types/index.ts:95-98; lib/listings.ts:55-57",
        "حداقل سرمایه ورود صندوق؛ معنای مستقل از ورود پروژه دارد.",
        True,
    ),
    (
        "project",
        "execution_months",
        "quantity",
        "MONTH",
        "Opportunity.executionMonths; types/index.ts:45; lib/listings.ts:26-27",
        "مدت اجرا به ماه؛ مبنای شروع منبع مشخص نیست، حدس زده نمی\u200cشود.",
        False,
    ),
    (
        "project",
        "payback_years",
        "quantity",
        "YEAR",
        "Opportunity.paybackYears; types/index.ts:46; lib/listings.ts:24-25",
        "دوره بازگشت به سال؛ درصد سود یا IRR نیست.",
        True,
    ),
    (
        "sale",
        "area",
        "quantity",
        "SQUARE_METRE",
        "SaleItem.area; types/index.ts:103-104; lib/listings.ts:84",
        "مساحت مورد فروش به مترمربع؛ معادل خودکار مساحت عرصه فیلتر نیست.",
        False,
    ),
    (
        "project",
        "irr",
        "return",
        "PERCENT",
        "ProjectTerms.irr; types/index.ts:86-87; data/fields.ts:24-26",
        "IRR اعلام\u200cشده؛ ثبت known نیازمند مبنای کامل است که منبع فعلی کامل ندارد.",
        False,
    ),
]


def seed(apps, schema_editor):
    Unit = apps.get_model("catalog", "UnitDefinition")
    Field = apps.get_model("catalog", "FieldDefinition")
    units = {}
    for code, kind, base, currency, factor in UNITS:
        units[code] = Unit.objects.create(
            code=code,
            version=1,
            kind=kind,
            base_code=base,
            base_version=1,
            currency=currency,
            factor=Decimal(factor),
        )
    maximum = Decimal("999999999999999999999999.999999999")
    for suffix, key, kind, unit, locator, meaning, required in FIELDS:
        allowed = ["TOMAN", "MILLION_TOMAN", "BILLION_TOMAN"] if kind == "money" else [unit]
        Field.objects.create(
            namespace="invest.opportunity." + suffix,
            key=key,
            version=1,
            label=meaning.split("؛")[0],
            return_type="irr" if kind == "return" else "",
            kind=kind,
            unit=units[unit],
            allowed_units=[{"code": c, "version": 1} for c in allowed],
            minimum=maximum.copy_negate() if kind == "return" else Decimal("0"),
            maximum=maximum,
            decimal_places=9,
            required=required,
            allow_unknown=True,
            allow_not_applicable=True,
            source_path="src/types/index.ts",
            source_locator=locator,
            meaning=meaning,
            visibility_rule="future-form-owned",
            inactive_effect="exclude",
        )


def unseed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit = apps.get_model("catalog", "UnitDefinition")
    for suffix, key, *_ in FIELDS:
        Field.objects.filter(namespace="invest.opportunity." + suffix, key=key, version=1).delete()
    Unit.objects.filter(version=1, code__in=[u[0] for u in UNITS]).delete()


IMMUTABLE = """
CREATE FUNCTION catalog_immutable_definition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Versioned catalog definitions are immutable; create a new version'
        USING ERRCODE='23514';
END; $$;
CREATE TRIGGER immutable_unit BEFORE UPDATE OR DELETE ON catalog_unitdefinition
FOR EACH ROW EXECUTE FUNCTION catalog_immutable_definition();
CREATE TRIGGER immutable_field BEFORE UPDATE OR DELETE ON catalog_fielddefinition
FOR EACH ROW EXECUTE FUNCTION catalog_immutable_definition();
"""
DROP_IMMUTABLE = """
DROP TRIGGER immutable_field ON catalog_fielddefinition;
DROP TRIGGER immutable_unit ON catalog_unitdefinition;
DROP FUNCTION catalog_immutable_definition();
"""

VALUE_GUARDS = """
CREATE FUNCTION catalog_validate_value() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE d catalog_fielddefinition%ROWTYPE; u catalog_unitdefinition%ROWTYPE;
BEGIN
    SELECT * INTO d FROM catalog_fielddefinition WHERE id=NEW.definition_id;
    SELECT * INTO u FROM catalog_unitdefinition WHERE id=NEW.unit_id;
    IF NOT FOUND THEN RETURN NEW; END IF;
    IF d.kind <> TG_ARGV[0] OR u.kind <> d.kind
       OR NOT d.allowed_units @>
           jsonb_build_array(jsonb_build_object('code',u.code,'version',u.version))
       OR NEW.base_unit <> u.base_code OR NEW.base_version <> u.base_version
       OR NEW.conversion_factor <> u.factor
       OR (NEW.status='known' AND d.kind='return'
            AND NEW.basis->>'metric_type' IS DISTINCT FROM d.return_type)
       OR (NEW.status='unknown' AND NOT d.allow_unknown)
       OR (NEW.status='not_applicable' AND NOT d.allow_not_applicable)
       OR (NEW.status='known' AND (NEW.value < d.minimum OR NEW.value > d.maximum
            OR scale(NEW.source_value) > d.decimal_places
            OR (u.base_code='ITEM' AND scale(NEW.source_value)>0))) THEN
        RAISE EXCEPTION 'Value violates its versioned field/unit definition' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END; $$;
CREATE TRIGGER money_definition_guard BEFORE INSERT OR UPDATE ON catalog_moneyvalue
FOR EACH ROW EXECUTE FUNCTION catalog_validate_value('money');
CREATE TRIGGER quantity_definition_guard BEFORE INSERT OR UPDATE ON catalog_quantity
FOR EACH ROW EXECUTE FUNCTION catalog_validate_value('quantity');
CREATE TRIGGER return_definition_guard BEFORE INSERT OR UPDATE ON catalog_returnmetric
FOR EACH ROW EXECUTE FUNCTION catalog_validate_value('return');
"""
DROP_VALUE_GUARDS = """
DROP TRIGGER return_definition_guard ON catalog_returnmetric;
DROP TRIGGER quantity_definition_guard ON catalog_quantity;
DROP TRIGGER money_definition_guard ON catalog_moneyvalue;
DROP FUNCTION catalog_validate_value();
"""


class Migration(migrations.Migration):
    dependencies = [("catalog", "0002_exact_values")]
    operations = [
        migrations.RunPython(seed, unseed),
        migrations.RunSQL(IMMUTABLE, DROP_IMMUTABLE),
        migrations.RunSQL(VALUE_GUARDS, DROP_VALUE_GUARDS),
    ]
