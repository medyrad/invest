import uuid

import pytest
from django.utils import timezone

from apps.identity import sessions
from apps.workspace import service
from apps.workspace.models import Draft, Organization, Representation, RepresentationRequest

pytestmark = pytest.mark.django_db


def create(user, owner=None, key=None):
    return service.create_draft(
        user,
        {
            "key": key or str(uuid.uuid4()),
            "kind": "project",
            "schema_version": 1,
            "owner": owner or {"kind": "personal"},
        },
    )


def save(user, draft, values, routes=None, **kwargs):
    return service.save_draft(
        user,
        draft["id"],
        {
            "key": str(uuid.uuid4()),
            "version": draft["version"],
            "routes": routes or [],
            "heritage_enabled": False,
            "values": values,
            **kwargs,
        },
    )


def number(key, value="1.5", unit="BILLION_TOMAN", status="known", basis=None):
    return {
        "field": {"namespace": "invest.opportunity.project", "key": key, "version": 1},
        "unit": {"code": unit, "version": 1},
        "status": status,
        "source_value": value,
        "basis": basis,
    }


def test_retry_conflict_and_isolation(accounts):
    a, b = accounts
    key = str(uuid.uuid4())
    d = create(a, key=key)
    assert create(a, key=key)["id"] == d["id"]
    assert Draft.objects.count() == 1
    with pytest.raises(service.Fault):
        service.get_draft(b, d["id"])
    updated = save(a, d, {"title": "پروژه مصنوعی"})
    with pytest.raises(service.Fault) as exc:
        save(a, d, {"title": "قدیمی"})
    assert exc.value.status == 409
    assert service.get_draft(a, d["id"])["raw"]["title"] == "پروژه مصنوعی"
    assert updated["version"] == 2


def test_org_current_authority(accounts):
    a, b = accounts
    org = Organization.objects.create(name="مصنوعی", country="ایران", registration="TEST-1")
    app = RepresentationRequest.objects.create(organization=org, applicant=a, details={})
    d = create(a, {"kind": "organization", "request_id": str(app.id)})
    with pytest.raises(service.Fault):
        service.get_draft(b, d["id"])
    app.status = "approved"
    app.save()
    grant = Representation.objects.create(organization=org, user=a, status="active")
    assert service.get_draft(a, d["id"])["id"] == d["id"]
    grant.status = "revoked"
    grant.save()
    with pytest.raises(service.Fault):
        service.get_draft(a, d["id"])


def test_hidden_restore_and_independent_money(accounts):
    a = accounts[0]
    d = create(a)
    d = save(
        a,
        d,
        {
            "deposit": number("deposit"),
            "monthly_rent": number("monthly_rent", "2", "MILLION_TOMAN"),
        },
        ["lessee"],
    )
    assert d["effective"]["deposit"]["value"] == "1500000000"
    assert d["effective"]["monthly_rent"]["value"] == "2000000"
    d = save(a, d, {"deposit": number("deposit", "99")}, ["buyer"])
    assert "deposit" not in d["effective"]
    assert d["raw"]["deposit"]["source_value"] == "1.5"
    d = save(a, d, {}, ["lessee"])
    assert d["effective"]["deposit"]["value"] == "1500000000"


def test_heritage_fee_and_invalid_return(accounts):
    a = accounts[0]
    d = create(a)
    d = save(
        a,
        d,
        {
            "heritage_returns": ["lease"],
            "heritage_years": number("heritage_years", "0", "YEAR", basis={"start_basis": "تحویل"}),
        },
        ["heritage"],
        heritage_enabled=True,
    )
    assert d["effective"]["heritage_years"]["value"] == "0"
    d = save(a, d, {"heritage_returns": ["fee"]}, ["heritage"], heritage_enabled=True)
    assert "heritage_years" not in d["effective"]
    with pytest.raises(service.Fault):
        save(a, d, {"irr": number("irr", "10", "PERCENT")}, ["investor"])


@pytest.mark.parametrize(
    "value,status", [("0", "known"), (None, "unknown"), (None, "not_applicable")]
)
def test_exact_states(accounts, value, status):
    d = save(accounts[0], create(accounts[0]), {"budget": number("budget", value, status=status)})
    assert d["effective"]["budget"]["status"] == status


def test_no_authority_injection(accounts):
    for key in ["owner", "verified", "status", "public_revision", "irrCashflowsVerified"]:
        with pytest.raises(service.Fault):
            save(accounts[0], create(accounts[0]), {key: True})


def test_api_session_csrf_and_nul(client, accounts):
    _, token = sessions.mint_session(accounts[0], timezone.now())
    client.cookies["invest_session"] = token
    assert client.get("/api/v1/workspace/owners").status_code == 200
    assert client.post("/api/v1/workspace/drafts", {}, format="json").status_code == 403
    csrf = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    body = {
        "key": str(uuid.uuid4()),
        "kind": "project",
        "schema_version": 1,
        "owner": {"kind": "personal"},
    }
    r = client.post("/api/v1/workspace/drafts", body, format="json", HTTP_X_CSRFTOKEN=csrf)
    assert r.status_code == 200
    bad = {
        "key": str(uuid.uuid4()),
        "version": 1,
        "routes": [],
        "heritage_enabled": False,
        "values": {"title": "a\x00b"},
    }
    r = client.post(
        "/api/v1/workspace/drafts/" + r.json()["id"], bad, format="json", HTTP_X_CSRFTOKEN=csrf
    )
    assert r.status_code == 400 and r.json()["error"]["fields"]
