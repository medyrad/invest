import importlib
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate as validate_openapi

from apps.catalog.models import (
    FieldDefinition,
    Group,
    MoneyValue,
    Quantity,
    ReturnMetric,
    UnitDefinition,
)
from apps.catalog.values import MAX_VALUE, ValueErrorDetail, compare, normalize, parse_number

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def definitions():
    if not UnitDefinition.objects.exists():
        from django.apps import apps

        importlib.import_module("apps.catalog.migrations.0003_value_definitions").seed(apps, None)


def payload(
    key="min_capital",
    unit="BILLION_TOMAN",
    source="1.5",
    namespace="project",
    status="known",
    basis=None,
):
    return {
        "field": {"namespace": "invest.opportunity." + namespace, "key": key, "version": 1},
        "unit": {"code": unit, "version": 1},
        "status": status,
        "source_value": source,
        "basis": basis,
    }


def basis(**changes):
    return {
        "version": 1,
        "metric_type": "irr",
        "period": "annual",
        "horizon": {"value": "5", "unit": {"code": "YEAR", "version": 1}},
        "basis_date": "2026-11-17",
        "price_basis": "nominal",
        "scope": "investor",
        "observation": "claimed",
        "source": "fixture:explicit-source-v1",
        **changes,
    }


@pytest.mark.parametrize(
    "text,expected",
    [
        ("۱٫۵", "1.5"),
        ("١٫٥", "1.5"),
        ("1.5", "1.5"),
        ("۱٬۵۰۰", "1500"),
        ("١٬٥٠٠", "1500"),
        ("1,500", "1500"),
        (" ۰ ", "0"),
        ("۱٬۲۳۴٫۵۶", "1234.56"),
        ("1,234.56", "1234.56"),
    ],
)
def test_unambiguous_digit_grammar(text, expected):
    assert parse_number(text) == Decimal(expected)


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "1,5",
        "۱،۵",
        "1 500",
        "1_500",
        "1,00",
        "1,000٬000",
        "1٫5.0",
        ".5",
        "1.",
        "+1",
        "1e9",
        "NaN",
        "Infinity",
        True,
        1.5,
        1,
        None,
        "1/2",
        "1٪",
        "1.0000000000",
        "0.0000000001",
        "9" * 101,
    ],
)
def test_ambiguous_or_inexact_input_is_rejected(text):
    with pytest.raises(ValueErrorDetail):
        parse_number(text)


def test_exact_billion_million_and_storage_contract_roundtrip():
    a, b = normalize(payload(source="۱٫۵")), normalize(payload(unit="MILLION_TOMAN", source="۱۵۰۰"))
    assert a["value"] == b["value"] == "1500000000"
    assert a["conversion_factor"] == "1000000000" and b["conversion_factor"] == "1000000"
    assert a["source_value"] == "1.5" and b["source_value"] == "1500"
    assert a["base_unit"] == "TOMAN" and compare(a, b) == {
        "comparable": True,
        "reason": None,
        "relation": "equal",
    }
    row = MoneyValue.from_payload(payload(source="۱٫۵"))
    row.save()
    row.refresh_from_db()
    assert isinstance(row.value, Decimal) and row.value == Decimal("1500000000")
    assert row.as_dict() == a


@pytest.mark.parametrize(
    "status,source,value",
    [("known", "0", "0"), ("unknown", None, None), ("not_applicable", None, None)],
)
@pytest.mark.parametrize("kind", ["money", "quantity", "return"])
def test_zero_unknown_not_applicable_roundtrip(kind, status, source, value):
    p = payload(source=source, status=status)
    model = MoneyValue
    if kind == "quantity":
        p = payload("area", "SQUARE_METRE", source, namespace="sale", status=status)
        model = Quantity
    if kind == "return":
        p = payload(
            "irr", "PERCENT", source, status=status, basis=basis() if status == "known" else None
        )
        model = ReturnMetric
    dto = normalize(p)
    row = model.from_payload(p)
    row.save()
    row.refresh_from_db()
    assert dto == row.as_dict() and dto["value"] == value and dto["status"] == status
    if status != "known":
        assert compare(dto, dto)["comparable"] is False
        p["source_value"] = "0"
        with pytest.raises(ValueErrorDetail, match="نامعلوم|نامربوط"):
            normalize(p)


def test_precision_boundaries_and_local_decimal_context():
    for value in ["0.000000001", str(MAX_VALUE), "999999999999999999999999"]:
        p = payload(unit="TOMAN", source=value)
        row = MoneyValue.from_payload(p)
        row.save()
        row.refresh_from_db()
        assert row.value == Decimal(value)
        assert row.as_dict() == normalize(p)
    with pytest.raises(ValueErrorDetail):
        normalize(payload(unit="TOMAN", source="1000000000000000000000000"))
    with pytest.raises(ValueErrorDetail):
        normalize(payload(source=str(MAX_VALUE)))
    with pytest.raises(ValueErrorDetail):
        normalize(payload(source="-1"))
    p = payload("irr", "PERCENT", "-1.123456789", basis=basis())
    assert normalize(p)["value"] == "-1.123456789"


@pytest.mark.parametrize(
    "change",
    [
        {"unit": {"code": "RIAL", "version": 1}},
        {"unit": {"code": "TOMAN", "version": 99}},
        {"unit": {"code": "MONTH", "version": 1}},
        {"field": {"namespace": "invest.opportunity.project", "key": "min_capital", "version": 2}},
        {"unit": {"code": "TOMAN", "version": True}},
        {"source_value": 1.5},
        {"source_value": None},
        {"conversion_factor": "1"},
        {"value": "1"},
    ],
)
def test_versions_units_and_client_supplied_computed_values_are_rejected(change):
    with pytest.raises(ValueErrorDetail):
        normalize({**payload(), **change})


def custom_field(key, units, kind="money", places=9, version=1):
    default = UnitDefinition.objects.get(code=units[0]["code"], version=units[0]["version"])
    return FieldDefinition.objects.create(
        namespace="test.contract",
        key=key,
        version=version,
        label="فقط fixture آزمون",
        kind=kind,
        unit=default,
        allowed_units=units,
        minimum=Decimal(0),
        maximum=MAX_VALUE,
        decimal_places=places,
        source_path="test fixture",
        source_locator="test fixture",
        meaning="قرارداد مصنوعی مستقل؛ نگاشت محصول نیست",
    )


def test_currency_unit_and_definition_versions_never_create_false_comparison():
    f = custom_field("external", [{"code": "TOMAN", "version": 1}, {"code": "USD", "version": 1}])
    p = payload(unit="USD", source="10")
    p["field"] = f.reference()
    dollar = normalize(p)
    p["unit"]["code"] = "TOMAN"
    toman = normalize(p)
    assert dollar["base_unit"] == "USD" and dollar["value"] == "10"
    assert not compare(dollar, toman)["comparable"]
    u2 = UnitDefinition.objects.create(
        code="TOMAN",
        version=2,
        kind="money",
        base_code="TOMAN",
        base_version=2,
        currency="TOMAN",
        factor=Decimal("2"),
    )
    f2 = custom_field("external", [{"code": u2.code, "version": 2}], version=2)
    p["field"] = f2.reference()
    p["unit"]["version"] = 2
    assert not compare(toman, normalize(p))["comparable"]
    assert normalize(payload())["conversion_factor"] == "1000000000"


def test_different_meanings_are_not_aliases():
    min_capital = normalize(payload())
    budget = normalize(payload("budget"))
    fund = normalize(payload("minimum_investment", "MILLION_TOMAN", "1500", namespace="fund"))
    assert not compare(min_capital, budget)["comparable"]
    assert not compare(min_capital, fund)["comparable"]


def test_quantity_units_stay_explicit_and_count_is_integral():
    f = custom_field(
        "duration", [{"code": u, "version": 1} for u in ["MONTH", "DAY", "YEAR"]], kind="quantity"
    )
    p = payload("execution_months", "MONTH", "2", basis={"start_basis": "contract_start"})
    p["field"] = f.reference()
    month = normalize(p)
    p["unit"]["code"] = "DAY"
    p["source_value"] = "60"
    day = normalize(p)
    assert month["value"] == "2" and day["value"] == "60" and not compare(month, day)["comparable"]
    p["unit"]["code"] = "MONTH"
    p["basis"] = {"start_basis": "unspecified"}
    unknown = normalize(p)
    assert not compare(unknown, unknown)["comparable"]
    p["basis"] = None
    with pytest.raises(ValueErrorDetail):
        normalize(p)
    f = custom_field("count", [{"code": "ITEM", "version": 1}], kind="quantity")
    p = payload(unit="ITEM", source="1.5")
    p["field"] = f.reference()
    with pytest.raises(ValueErrorDetail):
        normalize(p)


@pytest.mark.parametrize(
    "change",
    [
        {"period": "total"},
        {"horizon": {"value": "60", "unit": {"code": "MONTH", "version": 1}}},
        {"basis_date": "2026-11-18"},
        {"price_basis": "real"},
        {"scope": "project"},
        {"observation": "observed"},
        {"source": "different-documented-source"},
    ],
)
def test_return_basis_mismatch_is_not_comparable(change):
    p = payload("irr", "PERCENT", "20", basis=basis())
    a = normalize(p)
    p["basis"] = basis(**change)
    b = normalize(p)
    assert not compare(a, b)["comparable"]
    assert compare(a, a)["comparable"]


@pytest.mark.parametrize(
    "bad",
    [
        None,
        {},
        {"version": 1},
        basis(horizon={"value": 5, "unit": {"code": "YEAR", "version": 1}}),
        basis(basis_date="2026-02-30"),
        basis(source=""),
        basis(version=2),
        basis(metric_type="ROI/year"),
    ],
)
def test_incomplete_or_invented_return_basis_rejected(bad):
    with pytest.raises(ValueErrorDetail):
        normalize(payload("irr", "PERCENT", "20", basis=bad))


def test_no_irr_is_derived_and_tampered_snapshots_reject():
    dto = normalize(payload())
    forged = {**dto, "value": "3"}
    with pytest.raises(ValueErrorDetail):
        compare(dto, forged)
    with pytest.raises(ValueErrorDetail):
        normalize({**payload("irr", "PERCENT", "20", basis=basis()), "roi": "100"})
    assert (
        normalize(payload("payback_years", "YEAR", "5", basis={"start_basis": "unspecified"}))[
            "kind"
        ]
        == "quantity"
    )


def test_database_rejects_overprecision_invalid_state_factors_and_immutable_definitions():
    row = MoneyValue.from_payload(payload(unit="TOMAN", source="1"))
    row.save()
    for patch in [
        {"value": Decimal("0.0000000001"), "source_value": Decimal("0.0000000001")},
        {"status": "unknown"},
        {"conversion_factor": Decimal("2")},
        {"value": Decimal("1.0000000000"), "source_value": Decimal("1.0000000000")},
    ]:
        with pytest.raises(IntegrityError), transaction.atomic():
            MoneyValue.objects.filter(pk=row.pk).update(**patch)
    for model in [UnitDefinition, FieldDefinition]:
        obj = model.objects.first()
        with pytest.raises(ValidationError):
            obj.save()
        with pytest.raises(IntegrityError), transaction.atomic():
            model.objects.filter(pk=obj.pk).update(version=99)
    row.value = Decimal("2")
    with pytest.raises(ValidationError):
        row.save()
    row.refresh_from_db()
    assert row.value == Decimal("1")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT numeric_scale FROM information_schema.columns "
            "WHERE table_name='catalog_moneyvalue' AND column_name='value'"
        )
        assert cursor.fetchone()[0] is None  # numeric without typmod, not a rounding column.


def test_value_api_contract_csrf_no_storage_and_persian_errors(client):
    csrf = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    contract = client.get("/api/v1/schema").json()
    validate_openapi(contract)

    def validate(name, data):
        Draft202012Validator(
            {"$ref": "#/components/schemas/" + name, "components": contract["components"]}
        ).validate(data)

    definitions = client.get("/api/v1/catalog/value-definitions")
    assert definitions.status_code == 200 and len(definitions.json()["fields"]) == 20
    assert len(definitions.json()["units"]) == 12
    validate("ValueDefinitions", definitions.json())
    validate("ValueInput", payload(source="۱٫۵"))
    assert (
        client.post("/api/v1/catalog/values/normalize", payload(), format="json").status_code == 403
    )
    response = client.post(
        "/api/v1/catalog/values/normalize",
        payload(source="۱٫۵"),
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 200 and response.json()["value"] == "1500000000"
    validate("ExactValue", response.json())
    assert MoneyValue.objects.count() == 0
    for p in [
        payload(source="1,5"),
        payload(source="1.0000000001"),
        payload(source=1.5),
        payload("irr", "PERCENT", "20"),
    ]:
        response = client.post(
            "/api/v1/catalog/values/normalize", p, format="json", HTTP_X_CSRFTOKEN=csrf
        )
        assert response.status_code == 400 and response.json()["error"]["fields"]
        assert any("\u0600" <= c <= "\u06ff" for c in response.json()["error"]["message"])
        validate("Error", response.json())


@pytest.mark.django_db(transaction=True)
def test_catalog_migration_backward_forward_preserves_existing_taxonomy():
    marker = Group.objects.create(
        id="values-migration-sentinel", name="داده قبلی", source_version="test"
    )
    executor = MigrationExecutor(connection)
    final_targets = executor.loader.graph.leaf_nodes()
    try:
        executor.migrate([("catalog", "0001_initial")])
        assert Group.objects.filter(pk=marker.pk).exists()
        assert "catalog_moneyvalue" not in connection.introspection.table_names()
        executor = MigrationExecutor(connection)
        executor.migrate([("catalog", "0003_value_definitions")])
        assert Group.objects.filter(pk=marker.pk).exists()
        assert FieldDefinition.objects.count() == 8 and UnitDefinition.objects.count() == 11
        row = MoneyValue.from_payload(payload())
        row.save()
        row.refresh_from_db()
        assert row.value == Decimal("1500000000")
    finally:
        MigrationExecutor(connection).migrate(final_targets)


@pytest.mark.parametrize("kind,value", [("quantity", "12.123456789"), ("return", "-12.123456789")])
def test_nonzero_quantity_and_return_storage(kind, value):
    if kind == "quantity":
        p = payload("area", "SQUARE_METRE", value, namespace="sale")
        model = Quantity
    else:
        p = payload("irr", "PERCENT", value, basis=basis())
        model = ReturnMetric
    row = model.from_payload(p)
    row.save()
    row.refresh_from_db()
    assert row.value == Decimal(value)
    assert row.as_dict()["value"] == value
    assert row.as_dict()["basis"] == p["basis"]


def test_field_specific_precision_and_range_are_enforced():
    unit = UnitDefinition.objects.get(code="TOMAN", version=1)
    field = FieldDefinition.objects.create(
        namespace="test.contract",
        key="bounded",
        version=1,
        label="fixture",
        kind="money",
        unit=unit,
        allowed_units=[{"code": "TOMAN", "version": 1}],
        minimum=Decimal("0"),
        maximum=Decimal("10"),
        decimal_places=2,
        source_path="fixture",
        source_locator="fixture",
        meaning="آزمون حدود فنی",
    )
    p = payload(unit="TOMAN", source="10.00")
    p["field"] = field.reference()
    assert normalize(p)["value"] == "10"
    for bad in ["10.01", "0.001"]:
        p["source_value"] = bad
        with pytest.raises(ValueErrorDetail):
            normalize(p)
    p["source_value"] = "10"
    row = MoneyValue.from_payload(p)
    row.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        MoneyValue.objects.filter(pk=row.pk).update(value=Decimal("11"), source_value=Decimal("11"))


def test_all_three_api_value_kinds_and_missing_states(client):
    csrf = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    contract = client.get("/api/v1/schema").json()
    schema = {"$ref": "#/components/schemas/ExactValue", "components": contract["components"]}
    requests = [
        payload("area", "SQUARE_METRE", "۱۲٫۵", namespace="sale"),
        payload("irr", "PERCENT", "-12.5", basis=basis()),
        payload(source=None, status="unknown"),
        payload(source=None, status="not_applicable"),
    ]
    for p in requests:
        response = client.post(
            "/api/v1/catalog/values/normalize", p, format="json", HTTP_X_CSRFTOKEN=csrf
        )
        assert response.status_code == 200
        Draft202012Validator(schema).validate(response.json())
        assert response.json() == normalize(p)
    assert (
        MoneyValue.objects.count() == Quantity.objects.count() == ReturnMetric.objects.count() == 0
    )


def test_source_irr_field_cannot_be_reinterpreted_as_simple_rate():
    p = payload("irr", "PERCENT", "20", basis=basis(metric_type="simple_rate"))
    with pytest.raises(ValueErrorDetail, match="نوع بازده"):
        normalize(p)
    f = FieldDefinition.objects.create(
        namespace="test.contract",
        key="simple_rate",
        version=1,
        label="fixture",
        kind="return",
        return_type="simple_rate",
        unit=UnitDefinition.objects.get(code="PERCENT", version=1),
        allowed_units=[{"code": "PERCENT", "version": 1}],
        minimum=Decimal("0"),
        maximum=MAX_VALUE,
        decimal_places=9,
        source_path="fixture",
        source_locator="fixture",
        meaning="نرخ ساده صریح؛ IRR نیست",
    )
    p["field"] = f.reference()
    simple = normalize(p)
    irr = normalize(payload("irr", "PERCENT", "20", basis=basis()))
    assert not compare(irr, simple)["comparable"]


@pytest.mark.parametrize("model", [MoneyValue, FieldDefinition])
def test_incomplete_model_reports_validation_error_instead_of_crashing(model):
    with pytest.raises(ValidationError):
        model().save()
