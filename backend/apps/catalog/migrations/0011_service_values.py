import json
from decimal import Decimal
from pathlib import Path

from django.db import migrations
from django.db.models import Q
from django.db.models.deletion import ProtectedError

FIELDS = json.loads((Path(__file__).parents[2] / "services/value-fields-v1.json").read_text())


def seed(apps, schema_editor):
    Unit = apps.get_model("catalog", "UnitDefinition")
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit.objects.create(
        code="PERCENTAGE", version=1, kind="quantity", base_code="PERCENTAGE", factor=Decimal("1")
    )
    for code in ["SERVICE_HOUR", "SESSION"]:
        Unit.objects.create(
            code=code, version=1, kind="quantity", base_code=code, factor=Decimal("1")
        )
    for f in FIELDS:
        unit = f["unit"]
        units = ["TOMAN", "MILLION_TOMAN", "BILLION_TOMAN"] if f["kind"] == "money" else [unit]
        if f.get("unit_options"):
            units = list(f["unit_options"])
        if f["key"] == "noncash_period":
            units = ["DAY", "MONTH", "YEAR"]
        Field.objects.create(
            namespace=f["namespace"],
            key=f["key"],
            version=1,
            label=f["label"][:200],
            kind=f["kind"],
            unit=Unit.objects.get(code=unit, version=1),
            allowed_units=[{"code": u, "version": 1} for u in units],
            minimum=Decimal(f.get("minimum") or "0"),
            maximum=Decimal(f.get("maximum") or "999999999999999999999999.999999999"),
            decimal_places=0 if f.get("integer") else 9,
            required=f["required"],
            source_path="public/engine/advisor.html",
            source_locator=str(f["source"])[:300],
            meaning=f["label"],
            visibility_rule=json.dumps(f.get("when"), ensure_ascii=False)[:300],
            inactive_effect="exclude",
        )


def unseed(apps, schema_editor):
    Field = apps.get_model("catalog", "FieldDefinition")
    Unit = apps.get_model("catalog", "UnitDefinition")
    predicate = Q(pk__in=[])
    for f in FIELDS:
        predicate |= Q(namespace=f["namespace"], key=f["key"], version=1)
    targets = Field.objects.filter(predicate)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        cursor.execute("ALTER TABLE catalog_fielddefinition DISABLE TRIGGER immutable_field")
        cursor.execute("ALTER TABLE catalog_unitdefinition DISABLE TRIGGER immutable_unit")
        targets.delete()  # PROTECT retains definitions with value consumers.
        for code in ["PERCENTAGE", "SERVICE_HOUR", "SESSION"]:
            remaining = Field.objects.filter(allowed_units__contains=[{"code": code, "version": 1}])
            if remaining.exists():
                raise ProtectedError("Unit has retained consumers", remaining)
        Unit.objects.filter(code__in=["PERCENTAGE", "SERVICE_HOUR", "SESSION"], version=1).delete()
        cursor.execute("ALTER TABLE catalog_fielddefinition ENABLE TRIGGER immutable_field")
        cursor.execute("ALTER TABLE catalog_unitdefinition ENABLE TRIGGER immutable_unit")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0010_operator_work_period")]
    operations = [migrations.RunPython(seed, unseed)]
