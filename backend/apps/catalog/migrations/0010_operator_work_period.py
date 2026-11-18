from decimal import Decimal

from django.db import migrations


def seed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit = apps.get_model("catalog", "UnitDefinition")
    Field.objects.create(
        namespace="invest.opportunity.project",
        key="operator_work_period",
        version=1,
        kind="quantity",
        label="دوره کار بهره‌برداری",
        unit=Unit.objects.get(code="MONTH", version=1),
        allowed_units=[{"code": u, "version": 1} for u in ["DAY", "MONTH", "YEAR"]],
        minimum=Decimal("0"),
        maximum=Decimal("999999999999999999999999.999999999"),
        decimal_places=9,
        source_path="src/data/routes.ts",
        source_locator="operator; routeSteps.operator; F09; PROGRAMMER-CORE-FIX-01",
        meaning="دوره ارائه خدمت بهره‌برداری و نگهداری؛ مستقل از مدت اجرا و بازگشت سرمایه",
        visibility_rule="operator",
        inactive_effect="exclude",
    )


def unseed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    targets = Field.objects.filter(
        namespace="invest.opportunity.project", key="operator_work_period", version=1
    )
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("ALTER TABLE catalog_fielddefinition DISABLE TRIGGER immutable_field")
        targets.delete()
        cursor.execute("ALTER TABLE catalog_fielddefinition ENABLE TRIGGER immutable_field")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0009_signed_fund_returns")]
    operations = [migrations.RunPython(seed, unseed)]
