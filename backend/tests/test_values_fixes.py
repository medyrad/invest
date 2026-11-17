"""S04-04: SQL-writer integrity; mutations/rollback only in isolated pytest PostgreSQL."""

import importlib

import pytest
from django.apps import apps
from django.db import IntegrityError, connection, models, transaction
from django.db.migrations.executor import MigrationExecutor

from apps.catalog.models import FieldDefinition, MoneyValue, Quantity, ReturnMetric, UnitDefinition
from apps.catalog.values import ValueErrorDetail, normalize

pytestmark = pytest.mark.django_db
LATEST = ("catalog", "0004_basis_integrity")


@pytest.fixture(autouse=True)
def isolated_definitions():
    assert connection.vendor == "postgresql" and connection.settings_dict["NAME"].startswith(
        "test_"
    )
    if not UnitDefinition.objects.exists():
        importlib.import_module("apps.catalog.migrations.0003_value_definitions").seed(apps, None)


def basis():
    return {
        "version": 1,
        "metric_type": "irr",
        "period": "annual",
        "horizon": {"value": "5", "unit": {"code": "YEAR", "version": 1}},
        "basis_date": "2026-11-17",
        "price_basis": "nominal",
        "scope": "investor",
        "observation": "claimed",
        "source": "synthetic source",
    }


def payload(kind="money", status="known"):
    key, code, namespace, data = {
        "money": ("min_capital", "TOMAN", "project", None),
        "duration": ("execution_months", "MONTH", "project", {"start_basis": "contract_signed"}),
        "area": ("area", "SQUARE_METRE", "sale", None),
        "return": ("irr", "PERCENT", "project", basis()),
    }[kind]
    return {
        "field": {"namespace": "invest.opportunity." + namespace, "key": key, "version": 1},
        "unit": {"code": code, "version": 1},
        "status": status,
        "source_value": "1" if status == "known" else None,
        "basis": data,
    }


def model_for(kind):
    return {"money": MoneyValue, "duration": Quantity, "area": Quantity, "return": ReturnMetric}[
        kind
    ]


@pytest.mark.parametrize(
    "kind,path",
    [
        ("money", "field.namespace"),
        ("money", "field.key"),
        ("money", "unit.code"),
        ("return", "basis.horizon.unit.code"),
        ("return", "basis.source"),
        ("duration", "basis.start_basis"),
    ],
)
def test_nul_rejected_before_lookup_with_contract_error(
    kind, path, client, django_assert_num_queries
):
    data = payload(kind)
    node = data
    parts = path.split(".")
    for key in parts[:-1]:
        node = node[key]
    node[parts[-1]] += "\x00"
    with django_assert_num_queries(0), pytest.raises(ValueErrorDetail) as exc:
        normalize(data)
    assert exc.value.code == "nul_not_allowed" and exc.value.field == path
    csrf = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    response = client.post(
        "/api/v1/catalog/values/normalize", data, format="json", HTTP_X_CSRFTOKEN=csrf
    )
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "nul_not_allowed" and path in error["fields"]
    assert any("\u0600" <= c <= "\u06ff" for c in error["message"])
    assert (
        MoneyValue.objects.count() == Quantity.objects.count() == ReturnMetric.objects.count() == 0
    )


def bad_bases():
    cases = []
    for kind in ["money", "area"]:
        cases += [(kind, x) for x in [{}, [], True, 1, "text", {"start_basis": "unexpected"}]]
    cases += [
        ("duration", x)
        for x in [
            None,
            "json-null",
            [],
            {},
            {"start_basis": None},
            {"start_basis": False},
            {"start_basis": 1},
            {"start_basis": ""},
            {"start_basis": " \t\u0085\u001c "},
            {"start_basis": "x" * 201},
            {"start_basis": " x "},
            {"start_basis": "x", "extra": 1},
        ]
    ]
    cases += [("return", x) for x in [None, "json-null", [], {}, {"metric_type": "irr"}]]
    for path, values in {
        "version": [None, True, "1", 1.0, 2],
        "metric_type": [None, 1, "simple_rate"],
        "period": [None, False, "daily"],
        "price_basis": [None, "other"],
        "scope": [None, "other"],
        "observation": [None, "other"],
        "basis_date": [None, 2026, "2026-02-30", "0000-01-01", "2026-1-01"],
        "source": [None, True, "", " \u0085\u001c ", "s" * 2001],
        "horizon": [None, [], {}, {"value": "5"}],
        "horizon.value": [
            None,
            5,
            True,
            "0",
            "-1",
            "NaN",
            "1e1",
            "1.0",
            "01",
            "0.0000000001",
            "1000000000000000000000000",
        ],
        "horizon.unit": [None, [], {}, {"code": "YEAR"}],
        "horizon.unit.code": [None, True, "TOMAN", "unknown"],
        "horizon.unit.version": [None, True, "1", 1.0, 0, 10000, 99],
    }.items():
        for value in values:
            candidate = basis()
            node = candidate
            parts = path.split(".")
            for key in parts[:-1]:
                node = node[key]
            node[parts[-1]] = value
            cases.append(("return", candidate))
    extra = basis()
    extra["extra"] = 1
    cases.append(("return", extra))
    return cases


@pytest.mark.parametrize("operation", ["insert", "update"])
@pytest.mark.parametrize("kind,invalid", bad_bases())
def test_sql_rejects_invalid_basis_structure_and_members(kind, invalid, operation):
    model = model_for(kind)
    row = model.from_payload(payload(kind))
    if operation == "update":
        row.save()
    invalid = (
        models.Value(None, output_field=models.JSONField()) if invalid == "json-null" else invalid
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        if operation == "update":
            model.objects.filter(pk=row.pk).update(basis=invalid)
        else:
            row.basis = invalid
            model.objects.bulk_create([row])
    if operation == "update":
        row.refresh_from_db()
        assert row.basis == payload(kind)["basis"]
    else:
        assert model.objects.count() == 0


@pytest.mark.parametrize("status", ["known", "unknown", "not_applicable"])
@pytest.mark.parametrize("kind", ["money", "area", "duration", "return"])
@pytest.mark.parametrize("operation", ["insert", "update"])
def test_valid_complete_basis_and_missing_states_are_still_writable(kind, status, operation):
    model = model_for(kind)
    row = model.from_payload(payload(kind, status))
    if operation == "update":
        row.save()
    new = payload(kind)["basis"]
    if kind == "duration":
        new = {"start_basis": "investment_started"}
    if kind == "return":
        new["basis_date"] = "2024-02-29"
    if operation == "update":
        model.objects.filter(pk=row.pk).update(basis=new)
    else:
        row.basis = new
        model.objects.bulk_create([row])
    row.refresh_from_db()
    row.full_clean()
    assert row.basis == new


@pytest.mark.parametrize(
    "kind,status",
    [
        ("money", "known"),
        ("money", "unknown"),
        ("money", "not_applicable"),
        ("area", "known"),
        ("area", "unknown"),
        ("area", "not_applicable"),
        ("return", "unknown"),
        ("return", "not_applicable"),
    ],
)
@pytest.mark.parametrize("json_null", [False, True])
def test_sql_null_and_json_null_are_accepted_only_where_contract_allows(kind, status, json_null):
    model = model_for(kind)
    row = model.from_payload(payload(kind, status))
    row.save()
    null = models.Value(None, output_field=models.JSONField()) if json_null else None
    model.objects.filter(pk=row.pk).update(basis=null)
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT basis IS NULL, jsonb_typeof(basis) FROM {model._meta.db_table} WHERE id=%s",
            [row.pk],
        )
        assert cursor.fetchone() == ((False, "null") if json_null else (True, None))
    row.refresh_from_db()
    row.full_clean()
    assert row.basis is None


@pytest.mark.parametrize("date_text", ["0001-01-01", "2024-02-29", "9999-12-31"])
@pytest.mark.parametrize("horizon", ["0.000000001", "999999999999999999999999.999999999"])
def test_valid_basis_boundary_dates_horizon_and_source_lengths(date_text, horizon):
    row = ReturnMetric.from_payload(payload("return"))
    row.save()
    data = basis()
    data["basis_date"] = date_text
    data["horizon"]["value"] = horizon
    data["source"] = "s" * 2000
    ReturnMetric.objects.filter(pk=row.pk).update(basis=data)
    row.refresh_from_db()
    row.full_clean()
    assert row.basis == data
    duration = Quantity.from_payload(payload("duration"))
    duration.save()
    Quantity.objects.filter(pk=duration.pk).update(basis={"start_basis": "x" * 200})
    duration.refresh_from_db()
    duration.full_clean()


@pytest.mark.django_db(transaction=True)
def test_incremental_migration_preflight_and_rollback_preserve_data():
    assert connection.settings_dict["NAME"].startswith("test_")
    MigrationExecutor(connection).migrate([LATEST])
    valid = MoneyValue.from_payload(payload())
    valid.save()
    original = valid.as_dict()
    try:
        MigrationExecutor(connection).migrate([("catalog", "0003_value_definitions")])
        MoneyValue.objects.filter(pk=valid.pk).update(basis={"unexpected": True})
        with pytest.raises(IntegrityError):
            MigrationExecutor(connection).migrate([LATEST])
        valid.refresh_from_db()
        assert valid.basis == {"unexpected": True}
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regprocedure('catalog_values_basis_valid(text,text,text,text,jsonb)')"
            )
            assert (
                cursor.fetchone()[0] is None
            )  # Failed migration is atomic, not partially installed.
        MoneyValue.objects.filter(pk=valid.pk).update(
            basis=None
        )  # Restore only the synthetic fixture.
        MigrationExecutor(connection).migrate([LATEST])
        valid.refresh_from_db()
        assert valid.as_dict() == original
        with pytest.raises(IntegrityError), transaction.atomic():
            MoneyValue.objects.filter(pk=valid.pk).update(basis={})
        MigrationExecutor(connection).migrate([("catalog", "0003_value_definitions")])
        valid.refresh_from_db()
        assert valid.as_dict() == original
        MigrationExecutor(connection).migrate([LATEST])
        valid.refresh_from_db()
        assert valid.as_dict() == original
        assert UnitDefinition.objects.count() == 11 and FieldDefinition.objects.count() == 8
    finally:
        MoneyValue.objects.filter(pk=valid.pk).update(basis=None)
        MigrationExecutor(connection).migrate([LATEST])


@pytest.mark.parametrize("kind,path", [("money", "unit.code"), ("return", "basis.source")])
def test_invalid_unicode_text_is_field_error_not_driver_or_renderer_error(
    kind, path, client, django_assert_num_queries
):
    import json

    data = payload(kind)
    node = data
    parts = path.split(".")
    for key in parts[:-1]:
        node = node[key]
    node[parts[-1]] += "\ud800"
    with django_assert_num_queries(0), pytest.raises(ValueErrorDetail) as exc:
        normalize(data)
    assert exc.value.code == "invalid_text" and exc.value.field == path
    csrf = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    response = client.post(
        "/api/v1/catalog/values/normalize",
        json.dumps(data),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 400 and path in response.json()["error"]["fields"]
