from decimal import Decimal

from django.db import migrations


def seed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit = apps.get_model("catalog", "UnitDefinition")
    for metric, label in [
        ("irr", "بازده داخلی"),
        ("simple_rate", "نرخ ساده"),
        ("effective_rate", "نرخ مؤثر"),
    ]:
        Field.objects.create(
            namespace="invest.opportunity.fund",
            key="forecast_" + metric,
            version=1,
            kind="return",
            label=label + " ادعایی صندوق",
            unit=Unit.objects.get(code="PERCENT", version=1),
            return_type=metric,
            allowed_units=[{"code": "PERCENT", "version": 1}],
            minimum=Decimal("0"),
            maximum=Decimal("999999999999999999999999.999999999"),
            decimal_places=9,
            source_path="src/types/index.ts",
            source_locator="Fund.forecast/rateBasis; explicit " + metric,
            meaning="ادعای بازده با نوع صریح؛ بدون استنباط نوع نرخ از نام forecast",
            visibility_rule="forecast_type=" + metric,
            inactive_effect="exclude",
        )


def unseed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    targets = Field.objects.filter(
        namespace="invest.opportunity.fund",
        key__in=["forecast_irr", "forecast_simple_rate", "forecast_effective_rate"],
        version=1,
    )
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("ALTER TABLE catalog_fielddefinition DISABLE TRIGGER immutable_field")
        targets.delete()
        cursor.execute("ALTER TABLE catalog_fielddefinition ENABLE TRIGGER immutable_field")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_fund_sale_fields")]
    operations = [migrations.RunPython(seed, unseed)]
