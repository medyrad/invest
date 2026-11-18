"""Historical reverse regression; destructive operations are test-PostgreSQL only."""

import importlib
from decimal import Decimal

import pytest
from django.apps import apps
from django.conf import settings
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder
from django.db.models.deletion import ProtectedError

from apps.catalog.models import FieldDefinition, MoneyValue, Quantity, ReturnMetric, UnitDefinition
from tests.test_values import basis, payload

V4 = ("catalog", "0004_basis_integrity")
V5 = ("catalog", "0005_project_fields")
V6 = ("catalog", "0006_project_capacity_units")
pytestmark = pytest.mark.django_db(transaction=True)


def migrate(target):
    assert settings.INVEST_ENV == "test"
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    return MigrationExecutor(connection).migrate([target])


def recorded():
    return set(MigrationRecorder(connection).applied_migrations())


def rows(model):
    return list(model.objects.order_by("pk").values())


def guards():
    with connection.cursor() as cursor:
        cursor.execute("""SELECT c.relname,t.tgname,t.tgenabled
            FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
            WHERE NOT t.tgisinternal AND c.relname LIKE 'catalog_%'
            ORDER BY c.relname,t.tgname""")
        return cursor.fetchall()


def assert_immutable(expected):
    assert guards() == expected
    for table in ["catalog_fielddefinition", "catalog_unitdefinition"]:
        with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table} SET version=version WHERE id=(SELECT min(id) FROM {table})"
            )
    assert guards() == expected


@pytest.fixture(autouse=True)
def isolated_current_schema():
    assert settings.INVEST_ENV == "test"
    assert connection.vendor == "postgresql" and connection.settings_dict["NAME"].startswith(
        "test_"
    )
    targets = MigrationExecutor(connection).loader.graph.leaf_nodes()
    MigrationExecutor(connection).migrate(targets)
    # TransactionTestCase flush removes migration seed rows between tests.
    if not UnitDefinition.objects.exists():
        importlib.import_module("apps.catalog.migrations.0003_value_definitions").seed(apps, None)
    if not FieldDefinition.objects.filter(key="deposit").exists():
        importlib.import_module("apps.catalog.migrations.0005_project_fields").seed(apps, None)
    if not FieldDefinition.objects.filter(key="metric_quantity", version=2).exists():
        importlib.import_module("apps.catalog.migrations.0006_project_capacity_units").seed(
            apps, None
        )
    yield
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS catalog_reverse_external_consumer")
    MigrationExecutor(connection).migrate(targets)


def old_values():
    money = MoneyValue.from_payload(payload("budget", "TOMAN", "2"))
    quantity = Quantity.from_payload(payload("area", "SQUARE_METRE", "3.25", namespace="sale"))
    returns = ReturnMetric.from_payload(payload("irr", "PERCENT", "10", basis=basis()))
    for value in [money, quantity, returns]:
        value.save()
    return {model: rows(model) for model in [MoneyValue, Quantity, ReturnMetric]}


def assert_old_values(snapshot):
    for model, data in snapshot.items():
        assert rows(model) == data


@pytest.mark.parametrize("version,previous", [(V6, V5), (V5, V4)])
def test_reverse_forward_each_preserves_old_records_and_guards(version, previous):
    migrate(V4)
    old_units, old_fields = rows(UnitDefinition), rows(FieldDefinition)
    values = old_values()
    migrate(version)
    before = guards()
    migrate(previous)
    assert version not in recorded() and previous in recorded()
    assert_old_values(values)
    assert (
        list(
            UnitDefinition.objects.filter(pk__in=[r["id"] for r in old_units])
            .order_by("pk")
            .values()
        )
        == old_units
    )
    assert (
        list(
            FieldDefinition.objects.filter(pk__in=[r["id"] for r in old_fields])
            .order_by("pk")
            .values()
        )
        == old_fields
    )
    assert_immutable(before)
    migrate(version)
    assert version in recorded()
    assert_old_values(values)
    assert_immutable(before)


def test_complete_reverse_chain_and_forward_matches_schema():
    initial_units = rows(UnitDefinition)
    initial_fields = rows(FieldDefinition)
    values = old_values()
    unit_refs = {row["id"]: (row["code"], row["version"]) for row in initial_units}
    before = guards()
    migrate(V5)
    assert (FieldDefinition.objects.count(), UnitDefinition.objects.count()) == (20, 12)
    assert not FieldDefinition.objects.filter(key="metric_quantity", version=2).exists()
    assert_immutable(before)
    migrate(V4)
    assert (FieldDefinition.objects.count(), UnitDefinition.objects.count()) == (8, 11)
    assert V5 not in recorded() and V6 not in recorded()
    assert "workspace_draft" not in connection.introspection.table_names()
    assert_old_values(values)
    assert_immutable(before)
    migrate(V6)

    # Auto IDs of removed definitions are not promised to be reused; all semantics remain.
    def semantic(data, unit_refs=None):
        result = []
        for row in data:
            row = dict(row)
            row.pop("id")
            if "unit_id" in row:
                row["unit"] = unit_refs[row.pop("unit_id")]
            result.append(row)
        return sorted(result, key=lambda r: repr(sorted(r.items())))

    assert semantic(rows(UnitDefinition)) == semantic(initial_units)
    # Old unit IDs are preserved; replaced definitions default only to those old units.
    assert semantic(
        rows(FieldDefinition), {r["id"]: (r["code"], r["version"]) for r in rows(UnitDefinition)}
    ) == semantic(initial_fields, unit_refs)
    assert_old_values(values)
    assert_immutable(before)


def new_field_value(version):
    if version == V6:
        data = payload("metric_quantity", "MEGAWATT", "2")
        data["field"]["version"] = 2
        row = Quantity.from_payload(data)
    else:
        row = MoneyValue.from_payload(payload("deposit", "TOMAN", "3"))
    row.save()
    return row


@pytest.mark.parametrize("version,previous", [(V6, V5), (V5, V4)])
def test_actual_value_consumer_rejects_reverse_without_data_or_guard_loss(version, previous):
    migrate(version)
    row = new_field_value(version)
    before = {
        model: rows(model) for model in [FieldDefinition, UnitDefinition, MoneyValue, Quantity]
    }
    guard_before = guards()
    with pytest.raises(ProtectedError):
        migrate(previous)
    assert version in recorded()
    for model, data in before.items():
        assert rows(model) == data
    row.refresh_from_db()
    assert row.value in [Decimal("2"), Decimal("3")]
    assert_immutable(guard_before)
    # A migration that succeeded earlier in the chain is not rolled back by a later failure.
    if version == V5:
        assert ("workspace", "0001_initial") not in recorded()
        assert "workspace_draft" not in connection.introspection.table_names()


@pytest.mark.parametrize("version,previous,unit_code", [(V6, V5, "BED"), (V5, V4, "SHARE_PERCENT")])
def test_unit_consumer_rejection_rolls_back_already_deleted_definitions(
    version, previous, unit_code
):
    migrate(version)
    unit = UnitDefinition.objects.get(code=unit_code, version=1)
    dependent = FieldDefinition.objects.create(
        namespace="invest.rollback",
        key="dependent",
        version=1,
        label="مصرف‌کننده مصنوعی",
        kind="quantity",
        unit=unit,
        allowed_units=[{"code": unit_code, "version": 1}],
        source_path="synthetic",
        source_locator="rollback test",
        meaning="مصرف‌کننده واقعی واحد",
    )
    before_units, before_fields, guard_before = (
        rows(UnitDefinition),
        rows(FieldDefinition),
        guards(),
    )
    with pytest.raises(ProtectedError):
        migrate(previous)
    assert version in recorded()
    assert rows(UnitDefinition) == before_units and rows(FieldDefinition) == before_fields
    dependent.refresh_from_db()
    assert dependent.unit_id == unit.pk
    assert_immutable(guard_before)


@pytest.mark.parametrize(
    "version,previous,table,key",
    [
        (V6, V5, "catalog_fielddefinition", "metric_quantity"),
        (V5, V4, "catalog_fielddefinition", "deposit"),
        (V6, V5, "catalog_unitdefinition", "BED"),
        (V5, V4, "catalog_unitdefinition", "SHARE_PERCENT"),
    ],
)
def test_database_fk_consumer_rejects_reverse_and_deferral_resets(version, previous, table, key):
    migrate(version)
    if table == "catalog_unitdefinition":
        definition = UnitDefinition.objects.get(code=key, version=1)
    else:
        definition = FieldDefinition.objects.get(
            namespace="invest.opportunity.project", key=key, version=2 if version == V6 else 1
        )
    with connection.cursor() as cursor:
        cursor.execute(f"""CREATE TABLE catalog_reverse_external_consumer (
            id bigint PRIMARY KEY, definition_id bigint NOT NULL REFERENCES {table}(id)
            DEFERRABLE INITIALLY DEFERRED)""")
        cursor.execute(
            "INSERT INTO catalog_reverse_external_consumer VALUES (1,%s)", [definition.pk]
        )
    before_units, before_fields, guard_before = (
        rows(UnitDefinition),
        rows(FieldDefinition),
        guards(),
    )
    with pytest.raises(IntegrityError) as failure:
        migrate(previous)
    assert failure.value.__cause__.sqlstate == "23503"
    assert version in recorded()
    assert rows(UnitDefinition) == before_units and rows(FieldDefinition) == before_fields
    assert_immutable(guard_before)
    # SET CONSTRAINTS is transaction-local: a fresh transaction still defers this FK.
    inserted = False
    with pytest.raises(IntegrityError), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO catalog_reverse_external_consumer VALUES (2,-1)")
            inserted = True
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    assert inserted
    with connection.cursor() as cursor:
        cursor.execute("SELECT count(*) FROM catalog_reverse_external_consumer")
        assert cursor.fetchone()[0] == 1


@pytest.mark.parametrize(
    "version,previous,unit_code", [(V6, V5, "ROOM"), (V5, V4, "SHARE_PERCENT")]
)
def test_allowed_unit_consumer_without_default_fk_blocks_reverse(version, previous, unit_code):
    migrate(version)
    dependent = FieldDefinition.objects.create(
        namespace="invest.rollback",
        key="allowed_consumer",
        version=1,
        label="ارجاع مصنوعی واحد",
        kind="quantity",
        unit=UnitDefinition.objects.get(code="ITEM", version=1),
        allowed_units=[{"code": "ITEM", "version": 1}, {"code": unit_code, "version": 1}],
        source_path="synthetic",
        source_locator="rollback test",
        meaning="ارجاع بدون FK پیش‌فرض",
    )
    before_fields, before_units, guard_before = (
        rows(FieldDefinition),
        rows(UnitDefinition),
        guards(),
    )
    with pytest.raises(ProtectedError):
        migrate(previous)
    assert version in recorded()
    assert rows(FieldDefinition) == before_fields and rows(UnitDefinition) == before_units
    dependent.refresh_from_db()
    assert_immutable(guard_before)


@pytest.mark.parametrize("version,previous", [(V6, V5), (V5, V4)])
def test_fk_default_deferral_returns_after_successful_reverse(version, previous):
    migrate(version)
    budget = FieldDefinition.objects.get(
        namespace="invest.opportunity.project", key="budget", version=1
    )
    with connection.cursor() as cursor:
        cursor.execute("""CREATE TABLE catalog_reverse_external_consumer (
            id bigint PRIMARY KEY, definition_id bigint REFERENCES catalog_fielddefinition(id)
            DEFERRABLE INITIALLY DEFERRED)""")
        cursor.execute("INSERT INTO catalog_reverse_external_consumer VALUES(1,%s)", [budget.pk])
    guard_before = guards()
    migrate(previous)
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("INSERT INTO catalog_reverse_external_consumer VALUES(2,-1)")
        cursor.execute("DELETE FROM catalog_reverse_external_consumer WHERE id=2")
    assert_immutable(guard_before)


def test_failed_second_reverse_does_not_undo_successful_first_migration():
    row = new_field_value(V5)  # v6 is also applied; the consumer uses only a v5 definition.
    guard_before = guards()
    with pytest.raises(ProtectedError):
        migrate(V4)
    assert V6 not in recorded() and V5 in recorded()
    assert (FieldDefinition.objects.count(), UnitDefinition.objects.count()) == (20, 12)
    assert not FieldDefinition.objects.filter(key="metric_quantity", version=2).exists()
    assert ("workspace", "0001_initial") not in recorded()
    assert "workspace_draft" not in connection.introspection.table_names()
    row.refresh_from_db()
    assert row.value == Decimal("3")
    assert_immutable(guard_before)
