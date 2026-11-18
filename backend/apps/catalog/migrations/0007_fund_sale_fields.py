from decimal import Decimal

from django.db import migrations

DEFINITIONS = [
    (
        "fund",
        {
            "key": "forecast",
            "label": "بازده ادعایی",
            "kind": "return",
            "unit": "PERCENT",
            "required": False,
            "when": "always",
            "options": None,
            "section": "money",
            "namespace": "invest.opportunity.fund",
            "source": "src/types/index.ts:Fund.forecast",
        },
    ),
    (
        "fund",
        {
            "key": "duration_months",
            "label": "مدت طرح",
            "kind": "quantity",
            "unit": "MONTH",
            "required": True,
            "when": "always",
            "options": None,
            "section": "money",
            "namespace": "invest.opportunity.fund",
            "source": "src/types/index.ts:Fund.duration_months",
        },
    ),
    (
        "sale",
        {
            "key": "price",
            "label": "قیمت عرضه",
            "kind": "money",
            "unit": "BILLION_TOMAN",
            "required": True,
            "when": "always",
            "options": None,
            "section": "money",
            "namespace": "invest.opportunity.sale",
            "source": "src/types/index.ts:SaleItem.price",
        },
    ),
    (
        "sale",
        {
            "key": "price_quantity",
            "label": "مقدار مبنای قیمت واحد",
            "kind": "quantity",
            "unit": "ITEM",
            "required": True,
            "when": "per_unit",
            "options": None,
            "section": "money",
            "namespace": "invest.opportunity.sale",
            "source": "src/types/index.ts:SaleItem.price_quantity",
        },
    ),
    (
        "sale",
        {
            "key": "land_area",
            "label": "مساحت عرصه",
            "kind": "quantity",
            "unit": "SQUARE_METRE",
            "required": False,
            "when": "property",
            "options": None,
            "section": "money",
            "namespace": "invest.opportunity.sale",
            "source": "src/types/index.ts:SaleItem.land_area",
        },
    ),
    (
        "sale",
        {
            "key": "quantity",
            "label": "مقدار کالای عرضه",
            "kind": "quantity",
            "unit": "ITEM",
            "required": True,
            "when": "scrap",
            "options": None,
            "section": "money",
            "namespace": "invest.opportunity.sale",
            "source": "src/types/index.ts:SaleItem.quantity",
        },
    ),
]


def seed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit = apps.get_model("catalog", "UnitDefinition")
    for kind, f in DEFINITIONS:
        unit = Unit.objects.get(code=f["unit"], version=1)
        allowed = (
            ["TOMAN", "MILLION_TOMAN", "BILLION_TOMAN"]
            if f["kind"] == "money"
            else (
                ["ITEM", "KILOGRAM", "SQUARE_METRE"]
                if f["key"] in ["quantity", "price_quantity"]
                else [f["unit"]]
            )
        )
        Field.objects.create(
            namespace="invest.opportunity." + kind,
            key=f["key"],
            version=1,
            kind=f["kind"],
            label=f["label"],
            unit=unit,
            allowed_units=[{"code": u, "version": 1} for u in allowed],
            minimum=Decimal("0"),
            maximum=Decimal("999999999999999999999999.999999999"),
            decimal_places=9,
            source_path="src/types/index.ts",
            source_locator=f["source"],
            meaning=f["label"] + "؛ مستقل طبق D31",
            visibility_rule=f["when"],
            inactive_effect="exclude",
            return_type="simple_rate" if f["kind"] == "return" else "",
        )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_project_capacity_units")]
    operations = [migrations.RunPython(seed)]
