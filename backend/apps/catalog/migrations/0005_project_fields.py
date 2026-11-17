from decimal import Decimal

from django.db import migrations

FIELDS = [
    {
        "key": "metric_quantity",
        "label": "مقدار ظرفیت",
        "kind": "quantity",
        "section": "general",
        "when": "always",
        "options": None,
        "unit": "ITEM",
        "required": False,
        "source": "src/types/index.ts:Opportunity.metric",
    },
    {
        "key": "working_capital_min",
        "label": "نقدینگی اجرای پیمان",
        "kind": "money",
        "section": "money",
        "when": "contractor",
        "options": None,
        "unit": "BILLION_TOMAN",
        "required": True,
        "source": "src/types/index.ts:Opportunity.working_capital_min",
    },
    {
        "key": "purchase_price",
        "label": "قیمت خرید",
        "kind": "money",
        "section": "money",
        "when": "buyer",
        "options": None,
        "unit": "BILLION_TOMAN",
        "required": True,
        "source": "src/types/index.ts:Opportunity.purchase_price",
    },
    {
        "key": "deposit",
        "label": "ودیعه",
        "kind": "money",
        "section": "money",
        "when": "lessee",
        "options": None,
        "unit": "BILLION_TOMAN",
        "required": True,
        "source": "src/types/index.ts:Opportunity.deposit",
    },
    {
        "key": "lump_rent",
        "label": "اجاره یکجای دوره",
        "kind": "money",
        "section": "money",
        "when": "lessee",
        "options": None,
        "unit": "BILLION_TOMAN",
        "required": True,
        "source": "src/types/index.ts:Opportunity.lump_rent",
    },
    {
        "key": "payback_downside_years",
        "label": "بازگشت بدبینانه",
        "kind": "quantity",
        "section": "money",
        "when": "participation",
        "options": None,
        "unit": "YEAR",
        "required": False,
        "source": "src/types/index.ts:Opportunity.payback_downside_years",
    },
    {
        "key": "lockup_months",
        "label": "قفل سرمایه",
        "kind": "quantity",
        "section": "money",
        "when": "participation",
        "options": None,
        "unit": "MONTH",
        "required": False,
        "source": "src/types/index.ts:Opportunity.lockup_months",
    },
    {
        "key": "first_income_months",
        "label": "اولین دریافت",
        "kind": "quantity",
        "section": "money",
        "when": "participation",
        "options": None,
        "unit": "MONTH",
        "required": False,
        "source": "src/types/index.ts:Opportunity.first_income_months",
    },
    {
        "key": "duration_years",
        "label": "مدت کل طرح / اجاره",
        "kind": "quantity",
        "section": "money",
        "when": "duration",
        "options": None,
        "unit": "YEAR",
        "required": True,
        "source": "src/types/index.ts:Opportunity.duration_years",
    },
    {
        "key": "heritage_years",
        "label": "مدت بهره\u200cبرداری میراث",
        "kind": "quantity",
        "section": "money",
        "when": "heritage_years",
        "options": None,
        "unit": "YEAR",
        "required": True,
        "source": "src/types/index.ts:Opportunity.heritage_years",
    },
    {
        "key": "partner_share",
        "label": "سهم شریک",
        "kind": "quantity",
        "section": "terms",
        "when": "participation",
        "options": None,
        "unit": "SHARE_PERCENT",
        "required": True,
        "source": "src/types/index.ts:Opportunity.partner_share",
    },
    {
        "key": "government_share",
        "label": "سهم دولت",
        "kind": "quantity",
        "section": "terms",
        "when": "contractor",
        "options": None,
        "unit": "SHARE_PERCENT",
        "required": True,
        "source": "src/types/index.ts:Opportunity.government_share",
    },
]


def seed(apps, schema_editor):
    Unit = apps.get_model("catalog", "UnitDefinition")
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit.objects.create(
        code="SHARE_PERCENT",
        version=1,
        kind="quantity",
        base_code="SHARE_PERCENT",
        base_version=1,
        currency="",
        factor=Decimal("1"),
    )
    for f in FIELDS:
        unit = Unit.objects.get(code=f["unit"], version=1)
        allowed = (
            ["TOMAN", "MILLION_TOMAN", "BILLION_TOMAN"]
            if f["kind"] == "money"
            else (
                ["ITEM", "KILOGRAM", "SQUARE_METRE"]
                if f["key"] == "metric_quantity"
                else [f["unit"]]
            )
        )
        Field.objects.create(
            namespace="invest.opportunity.project",
            key=f["key"],
            version=1,
            label=f["label"],
            kind=f["kind"],
            unit=unit,
            allowed_units=[{"code": x, "version": 1} for x in allowed],
            minimum=Decimal("0"),
            maximum=Decimal("100")
            if f["unit"] == "SHARE_PERCENT"
            else Decimal("999999999999999999999999.999999999"),
            decimal_places=9,
            source_path="src/types/index.ts",
            source_locator=f["source"],
            meaning=f["label"] + "؛ مستقل مطابق D31",
            visibility_rule=f["when"],
            inactive_effect="exclude",
        )


def unseed(apps, schema_editor):
    # Used only for explicit migration rollback. Referenced definitions fail FK checks;
    # normal application writes keep immutable-definition guards unchanged.
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit = apps.get_model("catalog", "UnitDefinition")
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("ALTER TABLE catalog_fielddefinition DISABLE TRIGGER immutable_field")
        cursor.execute("ALTER TABLE catalog_unitdefinition DISABLE TRIGGER immutable_unit")
        Field.objects.filter(
            namespace="invest.opportunity.project", version=1, key__in=[f["key"] for f in FIELDS]
        ).delete()
        Unit.objects.filter(code="SHARE_PERCENT", version=1).delete()
        cursor.execute("ALTER TABLE catalog_fielddefinition ENABLE TRIGGER immutable_field")
        cursor.execute("ALTER TABLE catalog_unitdefinition ENABLE TRIGGER immutable_unit")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_basis_integrity")]
    operations = [migrations.RunPython(seed, unseed)]
