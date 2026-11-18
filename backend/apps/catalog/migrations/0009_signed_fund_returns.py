from decimal import Decimal

from django.db import migrations


def seed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    for metric in ["irr", "simple_rate", "effective_rate"]:
        old = Field.objects.get(
            namespace="invest.opportunity.fund", key="forecast_" + metric, version=1
        )
        data = {f.attname: getattr(old, f.attname) for f in Field._meta.fields if not f.primary_key}
        data.update(version=2, minimum=Decimal("-999999999999999999999999.999999999"))
        Field.objects.create(**data)


def unseed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    targets = Field.objects.filter(
        namespace="invest.opportunity.fund",
        key__in=["forecast_irr", "forecast_simple_rate", "forecast_effective_rate"],
        version=2,
    )
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("ALTER TABLE catalog_fielddefinition DISABLE TRIGGER immutable_field")
        targets.delete()
        cursor.execute("ALTER TABLE catalog_fielddefinition ENABLE TRIGGER immutable_field")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0008_explicit_fund_return_types")]
    operations = [migrations.RunPython(seed, unseed)]
