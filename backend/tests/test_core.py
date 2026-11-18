import uuid
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.db import DatabaseError, transaction
from django.utils import timezone

from apps.core import cases, discovery, personal
from apps.core import publication as pub
from apps.core.models import Opportunity, Report, Submission
from apps.identity.models import User
from apps.identity.sessions import mint_session
from apps.workspace import other_schema
from apps.workspace import service as ws
from apps.workspace.models import PrivateFile, RepresentationRequest
from apps.workspace.schema import Fault

pytestmark = pytest.mark.django_db


def key():
    return str(uuid.uuid4())


def session(user):
    return mint_session(user, timezone.now(), sensitive=user.role in ["admin", "expert"])[0]


@pytest.fixture
def team(db):
    users = [
        User.objects.create_user(mobile="+12025550" + str(i).zfill(3), role=r)
        for i, r in enumerate(["owner", "admin", "user", "expert", "expert"])
    ]
    return [session(u) for u in users]


def number(kind, k, value, unit, status="known", basis=None):
    return {
        "field": {"namespace": "invest.opportunity." + kind, "key": k, "version": 1},
        "unit": {"code": unit, "version": 1},
        "status": status,
        "source_value": value,
        "basis": basis,
    }


def draft(s, kind="project", values=None):
    d = ws.create_draft(
        s.user, {"key": key(), "kind": kind, "schema_version": 1, "owner": {"kind": "personal"}}
    )
    route = "fund" if kind == "fund" else "buyer" if kind == "sale" else "investor"
    raw = {
        f["key"]: (
            number(
                kind,
                f["key"],
                None,
                f["unit"],
                "unknown",
                {"start_basis": "unspecified"} if f["unit"] in ["MONTH", "YEAR"] else None,
            )
            if f["unit"]
            else "unknown"
        )
        for f in other_schema.definition(kind)["fields"]
    }
    raw.update(
        {
            "title": "فرصت مصنوعی",
            "category": "land",
            "fund_kind": "fund",
            "fund_type": "fixed",
            "price_mode": "total",
            "bank_exists": "no",
        }
    )
    raw = {k: v for k, v in raw.items() if k in other_schema.fields(kind)}
    raw.update(values or {})
    return ws.save_draft(
        s.user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": [route],
            "heritage_enabled": False,
            "values": raw,
        },
    )


def publish(team, kind="project", values=None):
    o, a, *_ = team
    d = draft(o, kind, values)
    s = pub.submit(o, d["id"], {"key": key(), "version": d["version"]})
    pub.review(
        a,
        s["id"],
        {"key": key(), "decision": "approved", "reason": "بررسی مصنوعی مستقل", "public_files": []},
    )
    return d, Opportunity.objects.get(pk=s["opportunity_id"])


def case_action(c, s, act, **kw):
    return cases.action(
        s,
        c["id"],
        {
            "key": key(),
            "version": c["version"],
            "action": act,
            "text": "پیام انسانی آزمون",
            "next_action": "گام بعد آزمون",
            "next_followup_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "expert": None,
            "recipient": None,
            "kind": None,
            "files": [],
            **kw,
        },
    )


@pytest.mark.parametrize("kind", ["project", "fund", "sale"])
def test_kinds_publish_and_immutable(team, kind):
    d, op = publish(team, kind)
    public = discovery.public_dto(op)
    assert public["kind"] == kind and public["accepting_requests"]
    assert "raw" not in public and "mobile" not in public
    with pytest.raises(DatabaseError), transaction.atomic():
        Submission.objects.filter(pk=op.public_revision_id).update(snapshot={})
    assert Submission.objects.get(pk=op.public_revision_id).snapshot["title"] == "فرصت مصنوعی"


def test_edit_keeps_public_until_approval_and_replay(team):
    d, op = publish(team)
    before = op.public_revision_id
    o, a, *_ = team
    d = ws.save_draft(
        o.user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": ["investor"],
            "heritage_enabled": False,
            "values": {"title": "اصلاح مصنوعی"},
        },
    )
    payload = {"key": key(), "version": d["version"]}
    s = pub.submit(o, d["id"], payload)
    assert pub.submit(o, d["id"], payload)["id"] == s["id"]
    op.refresh_from_db()
    assert op.public_revision_id == before
    with pytest.raises(Fault):
        pub.review(
            o,
            s["id"],
            {"key": key(), "decision": "approved", "reason": "خودتأییدی", "public_files": []},
        )
    pub.review(
        a, s["id"], {"key": key(), "decision": "approved", "reason": "مستقل", "public_files": []}
    )
    op.refresh_from_db()
    assert op.public_revision_id != before


def test_case_journey_consent_reassignment_clock(team):
    d, op = publish(team)
    o, a, c, e, e2 = team
    payload = {
        "key": key(),
        "opportunity": str(op.pk),
        "text": "پیگیری بدون شماره",
        "previous": None,
    }
    result = cases.create(c, payload)
    case = result["case"]
    assert cases.create(c, payload)["case"]["id"] == case["id"]
    assert cases.create(c, {**payload, "key": key()})["existing"]
    deadline = case["first_response_due"]
    case = case_action(case, a, "assign", expert=str(e.user_id))
    with pytest.raises(Fault):
        cases.contact(e, case["id"])
    case = case_action(case, c, "grant", recipient=str(e.user_id), kind="expert")
    assert cases.contact(e, case["id"])["mobile"] == c.user.mobile
    case = case_action(case, a, "assign", expert=str(e2.user_id))
    from datetime import datetime

    assert (
        datetime.fromisoformat(case["first_response_due"]) == datetime.fromisoformat(deadline)
        and not case["consents"]
    )
    with pytest.raises(Fault):
        cases.get_case(e, case["id"])
    with pytest.raises(Fault):
        cases.contact(e2, case["id"])
    case = case_action(case, e2, "answer")
    assert case["status"] == "answered"
    cases.jobs(timezone.now() + timedelta(days=6))
    assert cases.get_case(c, case["id"]).status == "answered"
    case = case_action(case, c, "message")
    cases.jobs(timezone.now() + timedelta(days=8))
    assert cases.get_case(c, case["id"]).status == "in_review"
    case = case_action(case, e2, "answer")
    cases.jobs(timezone.now() + timedelta(days=8))
    assert cases.get_case(c, case["id"]).status == "closed"
    with pytest.raises(Fault):
        case_action(cases.dto(cases.get_case(c, case["id"])), c, "message")
    follow = cases.create(c, {**payload, "key": key(), "previous": case["id"]})["case"]
    assert follow["previous"] == case["id"]
    assert "mobile" not in str(follow)


def test_pause_blocks_new_preserves_case(team):
    _, op = publish(team)
    o, a, c, e, _ = team
    case = cases.create(
        c, {"key": key(), "opportunity": str(op.pk), "text": "درخواست", "previous": None}
    )["case"]
    pub.availability(
        o,
        op.pk,
        {
            "key": key(),
            "version": op.version,
            "action": "owner_paused",
            "reason": "توقف فوری",
            "expires_at": None,
        },
    )
    op.refresh_from_db()
    assert not pub.active(op)
    assert cases.get_case(c, case["id"])
    with pytest.raises(Fault):
        cases.create(e, {"key": key(), "opportunity": str(op.pk), "text": "جدید", "previous": None})
    with pytest.raises(Fault):
        pub.availability(
            o,
            op.pk,
            {
                "key": key(),
                "version": op.version,
                "action": "active",
                "reason": "بازنشر",
                "expires_at": None,
            },
        )
    pub.availability(
        a,
        op.pk,
        {
            "key": key(),
            "version": op.version,
            "action": "active",
            "reason": "کنترل جاری",
            "expires_at": None,
        },
    )


def test_matching_fixed_denominator(team):
    expected = [
        ("25000000000", "tehran", "100", "100"),
        (
            "40000000000",
            "tehran",
            "33.3333333333333333333333333333333333333333333333333333333333",
            "100",
        ),
        ("25000000000", "isfahan", None, "100"),
        (None, "tehran", None, None),
        (None, None, "0", "0"),
    ]
    for amount, location, sc, cov in expected:
        v = {
            "min_capital": {"status": "known", "value": amount}
            if amount
            else {"status": "unknown"},
            "province": location,
        }
        s = SimpleNamespace(kind="project", snapshot=v)
        result = discovery.score(
            s, {"budget_max": "30000000000", "province": ["tehran"], "route": "investor"}
        )
        assert result["score"] == sc if sc is not None else Decimal(result["score"]) > 0
        if cov is not None:
            assert result["coverage"] == cov
    assert discovery.score(s, {})["score"] is None
    assert result["status"] == "insufficient_data"


@pytest.mark.parametrize("kind", ["fund", "sale"])
def test_inactive_values_not_effective(team, kind):
    d = draft(team[0], kind)
    assert ("bank_principal" if kind == "fund" else "scrap_type") not in d["effective"]
    if kind == "sale":
        bad = number("sale", "price_quantity", "0", "ITEM")
        with pytest.raises(Fault):
            ws.save_draft(
                team[0].user,
                d["id"],
                {
                    "key": key(),
                    "version": d["version"],
                    "routes": ["buyer"],
                    "heritage_enabled": False,
                    "values": {"price_mode": "per_unit", "price_quantity": bad},
                },
            )


def test_personal_isolation_report_no_case(team):
    _, op = publish(team)
    user = team[2].user
    data = {"key": key(), "action": "save", "id": str(op.pk), "value": True}
    personal.mutate(user, data)
    assert len(personal.state(user)["saved"]) == 1 and not personal.state(team[3].user)["saved"]
    result = personal.mutate(
        user, {"key": key(), "action": "report", "id": str(op.pk), "value": {}}
    )
    assert Report.objects.get(pk=result["report_id"]).snapshot["opportunity"]["revision"] == str(
        op.public_revision_id
    )
    from apps.core.models import Case

    assert not Case.objects.exists()
    with pytest.raises(Fault):
        personal.mutate(
            user, {"key": key(), "action": "profile", "id": None, "value": {"role": "admin"}}
        )


def test_organization_review_successor_hold_and_isolation(team):

    o, a, c, e, _ = team

    def app(user, reg):
        details = {
            "name": "سازمان مصنوعی",
            "country": "ایران",
            "organization_type": "نمونه",
            "registration": reg,
            "signatory": "امضا",
            "representative_name": "نماینده",
            "scope": "ثبت فرصت",
            "starts_on": "2026-01-01",
            "ends_on": None,
            "no_expiry": True,
        }
        row = ws.organization(user, {"key": key(), "details": details})
        req = RepresentationRequest.objects.get(pk=row["id"])
        for i in range(3):
            PrivateFile.objects.create(
                uploader=user,
                application=req,
                kind="document",
                name=f"fake-{i}.pdf",
                size=3,
                sha256="a" * 64,
                status="clean",
                attached=True,
                content=b"abc",
            )
        return req

    def review(req, decision="approved", actor=a):
        return pub.organization_review(
            actor,
            req.pk,
            {
                "key": key(),
                "version": req.version,
                "decision": decision,
                "reason": "بررسی مصنوعی",
                "source": "منبع مستقل آزمون",
                "result": "مقابله شد",
            },
        )

    first = app(o.user, "SYN-A")
    review(first)
    assert ws.grant(o.user, first.organization_id)
    second_org = app(o.user, "SYN-B")
    review(second_org)
    successor = app(c.user, "SYN-A")
    assert ws.grant(o.user, first.organization_id) and not ws.grant(c.user, first.organization_id)
    review(successor)
    assert not ws.grant(o.user, first.organization_id) and ws.grant(c.user, first.organization_id)
    assert ws.grant(o.user, second_org.organization_id)
    successor.refresh_from_db()
    review(successor, "hold")
    assert not ws.grant(c.user, first.organization_id) and ws.grant(
        o.user, second_org.organization_id
    )
    own_admin = app(a.user, "SYN-C")
    with pytest.raises(Fault):
        review(own_admin)


def test_api_csrf_nul_public_role_and_data_boundaries(team, settings):
    from rest_framework.test import APIClient

    o, a, c, e, _ = team
    _, op = publish(team)
    api = APIClient(enforce_csrf_checks=True)
    result = api.get("/api/v1/core/opportunities").json()
    assert (
        result["total"] == 1 and "mobile" not in str(result) and "files" not in result["items"][0]
    )
    assert (
        api.post("/api/v1/core/local-roles", {"id": str(a.user_id)}, format="json").status_code
        == 403
    )
    settings.INVEST_ENV = "public"
    assert api.get("/api/v1/core/local-roles").status_code == 404
    settings.INVEST_ENV = "test"
    _, token = mint_session(c.user, timezone.now())
    api.cookies["invest_session"] = token
    csrf = api.get("/api/v1/auth/csrf").json()["csrfToken"]
    response = api.post(
        "/api/v1/core/personal",
        {
            "key": key(),
            "action": "search",
            "id": None,
            "value": {"name": "نویسه\0", "criteria": {}},
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf,
    )
    assert response.status_code == 400 and response.json()["error"]["fields"]
    assert (
        api.post(
            "/api/v1/core/review/" + str(op.public_revision_id),
            {"key": key(), "decision": "approved", "reason": "تزریق", "public_files": []},
            format="json",
            HTTP_X_CSRFTOKEN=csrf,
        ).status_code
        == 403
    )
    plain, _ = mint_session(a.user, timezone.now(), sensitive=False)
    with pytest.raises(Fault):
        pub.review(
            plain,
            str(op.public_revision_id),
            {"key": key(), "decision": "approved", "reason": "بدون احراز حساس", "public_files": []},
        )


def test_cursor_fixed_and_preferences_never_exclude(team):
    for i in range(13):
        publish(team, values={"title": f"فرصت مصنوعی {i}"})
    c = {"kind": "project", "budget_max": "0", "province": ["نامکان"]}
    first = discovery.listing(c)
    assert len(first["items"]) == 12 and first["total"] == 13
    second = discovery.listing(c, first["next"])
    assert len(second["items"]) == 1
    assert not ({x["id"] for x in first["items"]} & {x["id"] for x in second["items"]})
    with pytest.raises(Fault):
        discovery.listing({"kind": "fund"}, first["next"])
    assert all(Decimal(p["matching"]["score"]) == 0 for p in first["items"])
    assert discovery.listing({})["items"][0]["matching"]["score"] is None


def test_compare_units_basis_and_kinds(team):
    _, a = publish(team)
    _, b = publish(team)
    result = discovery.compare([str(a.pk), str(b.pk)])
    assert result["rows"] and not any(r["comparable"] for r in result["rows"])
    _, f = publish(team, "fund")
    with pytest.raises(Fault):
        discovery.compare([str(a.pk), str(f.pk)])
    with pytest.raises(Fault):
        discovery.compare([str(a.pk), str(a.pk)])


def test_file_reference_retained_and_private_snapshot(team):
    from apps.workspace.files import purge

    o, a, *_ = team
    d = draft(o)
    f = PrivateFile.objects.create(
        uploader=o.user,
        draft_id=d["id"],
        kind="document",
        name="synthetic.pdf",
        size=3,
        sha256="a" * 64,
        status="clean",
        attached=True,
        content=b"abc",
        received_at=timezone.now(),
    )
    s = pub.submit(o, d["id"], {"key": key(), "version": d["version"]})
    f.deleted_at = timezone.now() - timedelta(days=31)
    f.save()
    assert purge() == 0
    f.refresh_from_db()
    assert bytes(f.content) == b"abc"
    with pytest.raises(Fault):
        pub.review(
            a,
            s["id"],
            {
                "key": key(),
                "decision": "approved",
                "reason": "مدرک عمومی نشود",
                "public_files": [str(f.pk)],
            },
        )
    pub.review(
        a,
        s["id"],
        {"key": key(), "decision": "approved", "reason": "بدون انتشار مدرک", "public_files": []},
    )
    assert "files" not in discovery.public_dto(Opportunity.objects.get(pk=s["opportunity_id"]))


@pytest.mark.django_db(transaction=True)
def test_publication_concurrent_decisions_serialized(team):
    from concurrent.futures import ThreadPoolExecutor

    from django.db import close_old_connections

    o, a, *_ = team
    d = draft(o)
    s = pub.submit(o, d["id"], {"key": key(), "version": d["version"]})
    # Different administrator accounts force contention on the opportunity lock.
    admin2 = User.objects.create_user(mobile="+12025550999", role="admin")
    a2 = session(admin2)

    def decide(actor):
        close_old_connections()
        try:
            pub.review(
                actor,
                s["id"],
                {"key": key(), "decision": "approved", "reason": "رقابت بررسی", "public_files": []},
            )
            return "approved"
        except Fault:
            return "conflict"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(decide, [a, a2]))
    assert sorted(results) == ["approved", "conflict"]
    assert Opportunity.objects.get(pk=s["opportunity_id"]).public_revision_id == uuid.UUID(s["id"])
