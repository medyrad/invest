"""Completion guidance only: incomplete drafts remain writable."""

import uuid

import pytest
from django.utils import timezone

from apps.identity import sessions
from apps.workspace import service
from apps.workspace.schema import FIELDS
from tests.test_workspace import create, number, save

pytestmark = pytest.mark.django_db


def duration(status="known", value="0"):
    return number(
        "duration_years",
        value if status == "known" else None,
        "YEAR",
        status,
        {"start_basis": "unspecified"},
    )


def test_incomplete_create_save_and_reload_include_model_id(accounts):
    a = accounts[0]
    d = create(a)
    assert d["schema_version"] == 1 and "model_id" in d["missing"]
    d = save(a, d, {})
    assert d["version"] == 2 and "model_id" in service.get_draft(a, d["id"])["missing"]
    assert FIELDS["model_id"]["required"] is True


@pytest.mark.parametrize("value", ["unknown", "not_applicable", "مدل قراردادی مصنوعی"])
def test_model_id_explicit_state_or_text_removes_presence_gap(accounts, value):
    d = save(accounts[0], create(accounts[0]), {"model_id": value})
    assert d["raw"]["model_id"] == value and "model_id" not in d["missing"]
    d = save(accounts[0], d, {"model_id": None})
    assert "model_id" in d["missing"]


@pytest.mark.parametrize("value", ["", "   ", False, 0, [], {}, "x" * 4001, "a\x00b"])
def test_model_id_invalid_input_rejected_and_previous_draft_kept(accounts, value):
    a = accounts[0]
    d = save(a, create(a), {"model_id": "متن معتبر مصنوعی"})
    with pytest.raises(service.Fault):
        save(a, d, {"model_id": value})
    actual = service.get_draft(a, d["id"])
    assert actual["version"] == d["version"] and actual["raw"]["model_id"] == "متن معتبر مصنوعی"


@pytest.mark.parametrize(
    "routes,visible,required",
    [
        ([], False, False),
        (["investor"], True, False),
        (["heritage"], True, False),
        (["lessee"], True, True),
        (["investor", "heritage"], True, False),
        (["investor", "lessee"], True, True),
        (["heritage", "lessee"], True, True),
        (["contractor"], False, False),
        (["contractor", "lessee"], True, True),
    ],
)
def test_duration_visibility_and_presence_are_independent(accounts, routes, visible, required):
    a = accounts[0]
    d = save(a, create(a), {}, routes)
    assert ("duration_years" in d["missing"]) is required
    with_value = save(a, d, {"duration_years": duration()}, routes)
    assert ("duration_years" in with_value["effective"]) is visible
    assert "duration_years" not in with_value["missing"]
    if visible:
        assert with_value["effective"]["duration_years"]["value"] == "0"


@pytest.mark.parametrize(
    "routes",
    [["investor"], ["heritage"], ["lessee"], ["investor", "lessee"], ["heritage", "lessee"]],
)
@pytest.mark.parametrize("status", ["known", "unknown", "not_applicable"])
def test_duration_statuses_and_v1_values_keep_their_contract(accounts, routes, status):
    d = save(accounts[0], create(accounts[0]), {"duration_years": duration(status)}, routes)
    assert d["effective"]["duration_years"]["status"] == status
    assert d["effective"]["duration_years"]["field"]["version"] == 1
    assert d["schema_version"] == 1 and "duration_years" not in d["missing"]


def test_duration_route_return_and_hidden_injection_preserve_original(accounts):
    a = accounts[0]
    original = duration()
    d = save(a, create(a), {"duration_years": original}, ["lessee"])
    d = save(a, d, {}, ["investor"])
    assert d["raw"]["duration_years"] == original and "duration_years" in d["effective"]
    d = save(a, d, {"duration_years": duration(value="999")}, ["contractor"])
    assert d["raw"]["duration_years"] == original
    assert "duration_years" in d["inactive"] and "duration_years" not in d["missing"]
    assert "duration_years" not in d["effective"]
    d = save(a, d, {}, ["heritage", "lessee"])
    assert d["effective"]["duration_years"]["value"] == "0"
    d = save(a, d, {"duration_years": None}, ["investor"])
    assert "duration_years" not in d["missing"]
    d = save(a, d, {}, ["lessee"])
    assert "duration_years" in d["missing"]


def test_heritage_fee_and_execution_requirements_stay_independent(accounts):
    a = accounts[0]
    d = save(a, create(a), {}, ["heritage"])
    assert "execution_months" in d["missing"] and "duration_years" not in d["missing"]
    d = save(a, d, {"heritage_returns": ["fee"]}, ["heritage"], heritage_enabled=True)
    assert "heritage_years" not in d["missing"] and "execution_months" not in d["missing"]
    assert "duration_years" not in d["missing"]
    d = save(a, d, {"heritage_returns": ["lease"]}, ["heritage"], heritage_enabled=True)
    assert "heritage_years" in d["missing"] and "duration_years" not in d["missing"]
    d = save(a, d, {"heritage_returns": ["fee"]}, ["heritage", "lessee"], heritage_enabled=True)
    assert "duration_years" in d["missing"] and "heritage_years" not in d["missing"]
    d = save(a, d, {}, ["contractor"])
    assert "execution_months" in d["missing"] and "duration_years" not in d["missing"]


def test_schema_and_real_api_completion_contract(client, accounts):
    _, token = sessions.mint_session(accounts[0], timezone.now())
    client.cookies["invest_session"] = token
    csrf = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    schema = client.get("/api/v1/workspace/schema").json()
    assert schema["schema_version"] == 1
    f = {row["key"]: row for row in schema["fields"]}
    assert f["model_id"]["required"] is True
    assert f["duration_years"]["required"] is False
    assert f["duration_years"]["required_routes"] == ["lessee"]
    assert f["duration_years"]["when"] == "duration"
    body = {
        "key": str(uuid.uuid4()),
        "kind": "project",
        "schema_version": 1,
        "owner": {"kind": "personal"},
    }
    created = client.post("/api/v1/workspace/drafts", body, format="json", HTTP_X_CSRFTOKEN=csrf)
    assert created.status_code == 200 and "model_id" in created.json()["missing"]
    d = created.json()
    for routes, value in [
        (["lessee"], None),
        (["investor"], None),
        (["heritage", "lessee"], "unknown"),
        (["lessee"], "not_applicable"),
        (["lessee"], "متن معتبر"),
    ]:
        payload = {
            "key": str(uuid.uuid4()),
            "version": d["version"],
            "routes": routes,
            "heritage_enabled": False,
            "values": {"model_id": value},
        }
        response = client.post(
            "/api/v1/workspace/drafts/" + d["id"], payload, format="json", HTTP_X_CSRFTOKEN=csrf
        )
        assert response.status_code == 200
        d = response.json()
        assert ("model_id" in d["missing"]) is (value is None)
        assert ("duration_years" in d["missing"]) is ("lessee" in routes)
