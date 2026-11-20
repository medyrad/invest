import json
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, transaction
from django.utils import timezone

from apps.core import cases, discovery, personal
from apps.core import publication as pub
from apps.core.models import Opportunity, Report, Search, Submission
from apps.identity.models import User
from apps.identity.sessions import mint_session
from apps.services import advisories
from apps.workspace import other_schema
from apps.workspace import service as ws
from apps.workspace.models import PrivateFile, RepresentationRequest
from apps.workspace.schema import Fault

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def current_core_definitions(db):
    # Transaction tests flush migration data; restore only missing frozen seed packages.
    import importlib

    from django.apps import apps

    from apps.catalog.models import FieldDefinition, UnitDefinition

    if not UnitDefinition.objects.exists():
        importlib.import_module("apps.catalog.migrations.0003_value_definitions").seed(apps, None)
    packages = [
        ("0005_project_fields", "invest.opportunity.project", "working_capital_min", 1),
        ("0006_project_capacity_units", "invest.opportunity.project", "metric_quantity", 2),
        ("0007_fund_sale_fields", "invest.opportunity.fund", "duration_months", 1),
        ("0008_explicit_fund_return_types", "invest.opportunity.fund", "forecast_irr", 1),
        ("0009_signed_fund_returns", "invest.opportunity.fund", "forecast_irr", 2),
        ("0010_operator_work_period", "invest.opportunity.project", "operator_work_period", 1),
    ]
    for module, namespace, key, version in packages:
        if not FieldDefinition.objects.filter(
            namespace=namespace, key=key, version=version
        ).exists():
            importlib.import_module("apps.catalog.migrations." + module).seed(apps, None)


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


def test_d28_human_review_inputs_are_nonempty_and_unlabelled(team):
    for kind in ["project", "fund", "sale"]:
        publish(team, kind)
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/core/d28-human-review-inputs.json").read_text()
    )
    review = [s for s in fixture["scenarios"] if s["cohort"] == "human_review_nonempty"]
    assert len(review) == 40
    assert {s["route"] for s in review} == {"investor", "fund", "buyer"}
    for scenario in review:
        assert set(scenario["criteria"]) - {"route"}
        assert scenario["pre_result_human_label"] is None
        assert scenario["critical_misleading"] is None
        result = discovery.listing(scenario["criteria"])
        assert result["items"], scenario["id"]
        assert all("matching" in item for item in result["items"][:5])


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


def test_saved_search_update_is_atomic_and_report_redownload_is_readable(team):
    call_command("import_reference", verbosity=0)
    from apps.catalog.models import Subtype

    catalog_subtype = Subtype.objects.first()
    _, op = publish(
        team,
        values={"group": catalog_subtype.group_id, "subtype": catalog_subtype.pk},
    )
    user = team[2].user
    created = personal.mutate(
        user,
        {
            "key": key(),
            "action": "search",
            "id": None,
            "value": {"name": "شرایط اولیه", "criteria": {"route": "investor"}},
        },
    )
    search_id = created["searches"][0]["id"]
    personal.mutate(
        user,
        {
            "key": key(),
            "action": "search_update",
            "id": search_id,
            "value": {"name": "شرایط ویرایش‌شده", "criteria": {"route": "investor"}},
        },
    )
    assert Search.objects.get(pk=search_id).name == "شرایط ویرایش‌شده"
    with pytest.raises(Fault):
        personal.mutate(
            user,
            {
                "key": key(),
                "action": "search_update",
                "id": search_id,
                "value": {"name": "نباید اعمال شود", "criteria": {"route": "invalid"}},
            },
        )
    assert Search.objects.get(pk=search_id).name == "شرایط ویرایش‌شده"

    subtype = Subtype.objects.get(pk=discovery.public_dto(op)["fields"]["subtype"]).raw_id
    question = advisories.evaluate(subtype, {})["questions"][0]
    answer = question["options"][0]["value"]
    receipt = personal.mutate(
        user,
        {
            "key": key(),
            "action": "report",
            "id": str(op.pk),
            "value": {
                "criteria": {"route": "investor"},
                "guide_context": {
                    "mine": [["بودجه", "۳۰ میلیارد تومان"]],
                    "answers": {question["id"]: answer},
                    "checked": ["بررسی سند"],
                    "advisory_version": 1,
                },
            },
        },
    )
    report = Report.objects.get(pk=receipt["report_id"])
    rendered = report.snapshot["rendered_html"]
    assert "شرایط ثبت‌شده شما" in rendered
    assert "پاسخ‌های مؤثر ثبت‌شده" in rendered
    assert "کنترل‌های راهنمای مؤثر" in rendered
    assert report.snapshot["effective_advisory"]["version"] == 1
    assert "این دریافت پرونده یا درخواست تازه‌ای ایجاد نمی‌کند" in rendered
    assert receipt["download"].endswith(str(report.pk))


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


@pytest.mark.parametrize("metric", ["irr", "simple_rate", "effective_rate"])
def test_explicit_signed_fund_return_basis_and_hidden_effect(team, metric):
    s = team[0]
    d = draft(s, "fund")
    basis = {
        "version": 1,
        "metric_type": metric,
        "period": "annual",
        "horizon": {"value": "2", "unit": {"code": "YEAR", "version": 1}},
        "basis_date": "2026-11-18",
        "price_basis": "nominal",
        "scope": "investor",
        "observation": "claimed",
        "source": "ادعای مصنوعی با نوع نرخ صریح",
    }
    field = "forecast_" + metric
    v = number("fund", field, "-2.125", "PERCENT", basis=basis)
    v["field"]["version"] = 2
    d = ws.save_draft(
        s.user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": ["fund"],
            "heritage_enabled": False,
            "values": {"forecast_type": metric, field: v},
        },
    )
    assert d["effective"][field]["value"] == "-2.125"
    with pytest.raises(Fault):
        bad = {
            **v,
            "basis": {**basis, "metric_type": "simple_rate" if metric != "simple_rate" else "irr"},
        }
        ws.save_draft(
            s.user,
            d["id"],
            {
                "key": key(),
                "version": d["version"],
                "routes": ["fund"],
                "heritage_enabled": False,
                "values": {field: bad},
            },
        )
    d = ws.save_draft(
        s.user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": ["fund"],
            "heritage_enabled": False,
            "values": {"forecast_type": "unknown", field: v},
        },
    )
    assert field not in d["effective"] and d["raw"][field]["source_value"] == "-2.125"


def test_suspension_content_and_public_launch_gate(team, settings):
    _, op = publish(team)
    o, a, c, *_ = team
    pub.availability(
        a,
        op.pk,
        {
            "key": key(),
            "version": op.version,
            "action": "admin_suspended",
            "reason": "محتوای مورد اعتراض",
            "expires_at": None,
        },
    )
    op.refresh_from_db()
    assert discovery.public_dto(op)["fields"] == {"title": "این فرصت تعلیق شده است"}
    with pytest.raises(Fault):
        pub.availability(
            o,
            op.pk,
            {
                "key": key(),
                "version": op.version,
                "action": "owner_paused",
                "reason": "دورزدن",
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
            "reason": "رفع علت",
            "expires_at": None,
        },
    )
    settings.INVEST_ENV = "public"
    with pytest.raises(Fault) as exc:
        cases.create(
            c, {"key": key(), "opportunity": str(op.pk), "text": "نباید عرضه شود", "previous": None}
        )
    assert exc.value.status == 503


def test_matching_independent_expected_fractions_and_important_unknown():
    from fractions import Fraction

    fixtures = [
        ("25000000000", "tehran", Fraction(100), Fraction(100)),
        ("40000000000", "tehran", Fraction(100, 3), Fraction(100)),
        ("25000000000", "isfahan", Fraction(200, 3), Fraction(100)),
        (None, "tehran", Fraction(100, 3), Fraction(100, 3)),
        (None, None, Fraction(0), Fraction(0)),
    ]
    for value, location, score, coverage in fixtures:
        s = SimpleNamespace(
            kind="project",
            snapshot={
                "min_capital": {"status": "known", "value": value}
                if value is not None
                else {"status": "unknown"},
                "province": location,
            },
        )
        r = discovery.score(
            s,
            {
                "budget_max": "30000000000",
                "province": ["tehran"],
                "route": "investor",
                "important": ["amount", "location"],
            },
        )
        assert abs(Fraction(r["score"]) - score) < Fraction(1, 10**55)
        assert abs(Fraction(r["coverage"]) - coverage) < Fraction(1, 10**55)
        if value is None:
            assert r["warnings"]
    assert r["status"] == "insufficient_data"


def test_conditional_time_basis_and_version_prevent_comparison(team):
    _, a = publish(
        team,
        values={
            "payback_years": number(
                "project", "payback_years", "3", "YEAR", basis={"start_basis": "تحویل"}
            )
        },
    )
    _, b = publish(
        team,
        values={
            "payback_years": number(
                "project", "payback_years", "3", "YEAR", basis={"start_basis": "ورود سرمایه"}
            )
        },
    )
    r = discovery.compare([str(a.pk), str(b.pk)])
    row = next(x for x in r["rows"] if x["key"] == "payback_years")
    assert not row["comparable"]
    assert (
        discovery.score(a.public_revision, {"preferences": {"horizon": 3}, "route": "investor"})[
            "coverage"
        ]
        == "0"
    )
    assert (
        discovery.score(
            a.public_revision,
            {
                "preferences": {"horizon": 3, "basis:horizon": "تحویل"},
                "route": "investor",
            },
        )["score"]
        == "100"
    )
    assert (
        discovery.score(
            a.public_revision,
            {
                "preferences": {"horizon": 3, "basis:horizon": "ورود سرمایه"},
                "route": "investor",
            },
        )["coverage"]
        == "0"
    )
    unknown = SimpleNamespace(
        kind="project",
        snapshot={
            "payback_years": {
                "status": "known",
                "unit": {"code": "YEAR"},
                "source_value": "3",
                "basis": {"start_basis": "unspecified"},
            }
        },
    )
    assert discovery.score(unknown, {"preferences": {"horizon": 3}})["coverage"] == "0"


def test_hidden_search_preferences_not_scored_and_hierarchy_fixed():
    s = SimpleNamespace(kind="project", snapshot={"phase": "new", "sector": "public"})
    r = discovery.score(
        s,
        {
            "route": "investor",
            "preferences": {"phase": ["new"], "rehab": "yes", "notes": "متن شخصی خارج امتیاز"},
        },
    )
    assert r["score"] == "100" and len(r["checks"]) == 1
    s = SimpleNamespace(
        kind="project", snapshot={"province": "p", "city": "unknown", "county": "c"}
    )
    r = discovery.score(s, {"route": "investor", "province": ["p"], "county": ["c"], "city": ["x"]})
    assert r["score"] == "0" and r["coverage"] == "0" and len(r["checks"]) == 1


def test_owner_contact_not_case_membership_and_revocation(team):
    _, op = publish(team)
    o, a, c, e, _ = team
    case = cases.create(
        c, {"key": key(), "opportunity": str(op.pk), "text": "آزمون رضایت جدا", "previous": None}
    )["case"]
    case = case_action(case, c, "grant", recipient=str(o.user_id), kind="owner")
    assert cases.contact(o, case["id"])["mobile"] == c.user.mobile
    with pytest.raises(Fault):
        cases.get_case(o, case["id"])
    case_action(case, c, "revoke", recipient=str(o.user_id), kind="owner")
    with pytest.raises(Fault):
        cases.contact(o, case["id"])


def test_referenced_organization_evidence_retained_after_hold(team):
    # Retention follows recorded review, not the mutable latest request status.
    from apps.core.models import Event
    from apps.workspace.files import purge
    from apps.workspace.models import Organization

    o = team[0]
    org = Organization.objects.create(name="مصنوعی", country="IR", registration="retention-case")
    req = RepresentationRequest.objects.create(
        applicant=o.user, organization=org, details={}, status="needs_info"
    )
    f = PrivateFile.objects.create(
        uploader=o.user,
        application=req,
        kind="document",
        name="retained.pdf",
        size=3,
        sha256="a" * 64,
        status="clean",
        attached=True,
        content=b"abc",
        deleted_at=timezone.now() - timedelta(days=40),
    )
    Event.objects.create(
        target=org.pk, action="independent_review", data={"application": str(req.pk)}
    )
    assert purge() == 0
    f.refresh_from_db()
    assert bytes(f.content) == b"abc"


def test_per_unit_price_is_not_comparable_to_total_and_no_budget_total_inferred(team):
    _, a = publish(
        team,
        "sale",
        values={"price": number("sale", "price", "2", "BILLION_TOMAN"), "price_mode": "total"},
    )
    _, b = publish(
        team,
        "sale",
        values={
            "price": number("sale", "price", "2", "BILLION_TOMAN"),
            "price_mode": "per_unit",
            "price_quantity": number("sale", "price_quantity", "1", "KILOGRAM"),
        },
    )
    row = next(r for r in discovery.compare([str(a.pk), str(b.pk)])["rows"] if r["key"] == "price")
    assert not row["comparable"] and discovery.amount(b.public_revision, "buyer") is None


def test_unspecified_same_time_basis_not_comparable(team):
    _, a = publish(
        team,
        values={
            "payback_years": number(
                "project", "payback_years", "3", "YEAR", basis={"start_basis": "unspecified"}
            )
        },
    )
    _, b = publish(
        team,
        values={
            "payback_years": number(
                "project", "payback_years", "3", "YEAR", basis={"start_basis": "unspecified"}
            )
        },
    )
    assert not next(
        r for r in discovery.compare([str(a.pk), str(b.pk)])["rows"] if r["key"] == "payback_years"
    )["comparable"]


@pytest.mark.parametrize(
    "value",
    [
        {"budget_min": "5", "budget_max": "2"},
        {"return": {"minimum": "NaN", "basis": {}}},
        {"route": "unapproved-route"},
    ],
)
def test_invalid_search_contract_rejected(value):
    with pytest.raises(Fault):
        discovery.criteria(value)


def test_bank_claim_needs_independent_document_review(team):
    o, a, *_ = team
    d = draft(
        o,
        "fund",
        {
            "bank_exists": "yes",
            "bank_principal": "yes",
            "bank_profit": "yes",
            "bank_description": "ادعای مصنوعی بانک؛ بررسی مستقل الزامی",
        },
    )
    f = PrivateFile.objects.create(
        uploader=o.user,
        draft_id=d["id"],
        kind="document",
        name="bank-synthetic.pdf",
        size=3,
        sha256="a" * 64,
        status="clean",
        attached=True,
        content=b"abc",
    )
    sub = pub.submit(o, d["id"], {"key": key(), "version": d["version"]})
    s = Submission.objects.get(pk=sub["id"])
    assert (
        discovery.score(s, {"route": "fund", "preferences": {"bankGuarantee": "both"}})["coverage"]
        == "0"
    )
    with pytest.raises(Fault):
        pub.review(
            a,
            s.pk,
            {
                "key": key(),
                "decision": "approved",
                "reason": "بدون مدرک",
                "public_files": [],
                "verification": {"source": "منبع مستقل", "result": "بررسی دامنه", "files": []},
            },
        )
    assert pub.status(s) == "submitted"
    pub.review(
        a,
        s.pk,
        {
            "key": key(),
            "decision": "approved",
            "reason": "بررسی مصنوعی",
            "public_files": [],
            "verification": {
                "source": "منبع مستقل مصنوعی",
                "result": "اصل و سود طبق سند مصنوعی مقابله شد؛ تضمین سود واقعی نیست",
                "files": [str(f.pk)],
            },
        },
    )
    assert (
        discovery.score(s, {"route": "fund", "preferences": {"bankGuarantee": "both"}})["score"]
        == "100"
    )
    op = Opportunity.objects.get(pk=sub["opportunity_id"])
    assert discovery.public_dto(op)["verified"]["bank"]
    with pytest.raises(DatabaseError), transaction.atomic():
        s.review_set.first().reviewevidence.delete()


def test_public_contract_schema_and_private_snapshot_after_suspension(team, client):
    from jsonschema import Draft202012Validator
    from openapi_spec_validator import validate as validate_spec

    _, op = publish(team)
    c = team[2]
    case = cases.create(
        c, {"key": key(), "opportunity": str(op.pk), "text": "سند ثابت", "previous": None}
    )["case"]
    schema = client.get("/api/v1/schema").json()
    validate_spec(schema)
    data = client.get("/api/v1/core/opportunities").json()
    Draft202012Validator(
        {"$ref": "#/components/schemas/CoreFeed", "components": schema["components"]}
    ).validate(data)
    pub.availability(
        team[1],
        op.pk,
        {
            "key": key(),
            "version": op.version,
            "action": "admin_suspended",
            "reason": "حفظ snapshot خصوصی",
            "expires_at": None,
        },
    )
    snapshot = cases.dto(cases.get_case(c, case["id"]))
    assert snapshot["opportunity_snapshot"]["title"] == "فرصت مصنوعی"
    assert (
        "mobile" not in str(snapshot) and snapshot["opportunity_availability"] == "admin_suspended"
    )


def test_new_definition_reverse_protects_consumer_and_restores_guards():
    import importlib

    from django.apps import apps
    from django.db import connection
    from django.db.models.deletion import ProtectedError

    from apps.catalog.models import ReturnMetric

    basis = {
        "version": 1,
        "metric_type": "simple_rate",
        "period": "annual",
        "horizon": {"value": "1", "unit": {"code": "YEAR", "version": 1}},
        "basis_date": "2026-11-18",
        "price_basis": "nominal",
        "scope": "investor",
        "observation": "claimed",
        "source": "آزمون مصنوعی",
    }
    value = number("fund", "forecast_simple_rate", "-1", "PERCENT", basis=basis)
    value["field"]["version"] = 2
    row = ReturnMetric.from_payload(value)
    row.save()
    original = row.as_dict()
    with pytest.raises(ProtectedError), transaction.atomic():
        importlib.import_module("apps.catalog.migrations.0009_signed_fund_returns").unseed(
            apps, SimpleNamespace(connection=connection)
        )
    row.refresh_from_db()
    assert row.as_dict() == original
    with connection.cursor() as cur:
        cur.execute("SELECT tgenabled FROM pg_trigger WHERE tgname='immutable_field'")
        assert cur.fetchone()[0] == "O"


@pytest.mark.parametrize("unit", ["DAY", "MONTH", "YEAR"])
def test_operator_work_period_roundtrip_hidden_restore_public_and_report(team, unit):
    from apps.workspace.models import DraftValue

    owner, admin, customer, *_ = team
    d = draft(owner)
    d = ws.save_draft(
        owner.user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": ["operator"],
            "heritage_enabled": False,
            "values": {"description": "شرح خدمت نگهداری مصنوعی"},
        },
    )
    assert "operator_work_period" in d["missing"]
    assert not {"min_capital", "execution_months", "payback_years"} & set(d["effective"])
    with pytest.raises(Fault) as missing:
        pub.submit(owner, d["id"], {"key": key(), "version": d["version"]})
    assert missing.value.status == 400
    period = number(
        "project", "operator_work_period", "۱۸٫۵", unit, basis={"start_basis": "تحویل تاسیسات"}
    )
    d = ws.save_draft(
        owner.user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": ["operator"],
            "heritage_enabled": False,
            "values": {"operator_work_period": period},
        },
    )
    assert ws.get_draft(owner.user, d["id"])["effective"]["operator_work_period"]["value"] == "18.5"
    stored = DraftValue.objects.filter(key="operator_work_period").latest("id").quantity
    assert stored.value == Decimal("18.5") and stored.unit.code == unit
    assert stored.basis == {"start_basis": "تحویل تاسیسات"}
    d = ws.save_draft(
        owner.user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": ["contractor"],
            "heritage_enabled": False,
            "values": {},
        },
    )
    assert "operator_work_period" in d["raw"] and "operator_work_period" not in d["effective"]
    d = ws.save_draft(
        owner.user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": ["operator"],
            "heritage_enabled": False,
            "values": {},
        },
    )
    assert not d["missing"]
    submission = pub.submit(owner, d["id"], {"key": key(), "version": d["version"]})
    pub.review(
        admin,
        submission["id"],
        {
            "key": key(),
            "decision": "approved",
            "reason": "بررسی دوره خدمت مصنوعی",
            "public_files": [],
        },
    )
    op = Opportunity.objects.get(pk=submission["opportunity_id"])
    public = discovery.public_dto(op)
    assert public["fields"]["operator_work_period"] == d["effective"]["operator_work_period"]
    receipt = personal.mutate(
        customer.user,
        {
            "key": key(),
            "action": "report",
            "id": str(op.pk),
            "value": {"criteria": {}, "guide_context": {}},
        },
    )
    assert (
        Report.objects.get(pk=receipt["report_id"]).snapshot["opportunity"]["fields"][
            "operator_work_period"
        ]
        == public["fields"]["operator_work_period"]
    )


@pytest.mark.parametrize("status", ["unknown", "not_applicable"])
def test_operator_explicit_statuses_without_investor_budget(team, status):
    d = draft(team[0])
    d = ws.save_draft(
        team[0].user,
        d["id"],
        {
            "key": key(),
            "version": d["version"],
            "routes": ["operator"],
            "heritage_enabled": False,
            "values": {
                "operator_work_period": number(
                    "project",
                    "operator_work_period",
                    None,
                    "DAY",
                    status,
                    {"start_basis": "unspecified"},
                )
            },
        },
    )
    assert not d["missing"]
    assert d["effective"]["operator_work_period"]["status"] == status


@pytest.mark.parametrize(
    "patch",
    [
        {"unit": {"code": "", "version": 1}},
        {"unit": {"code": "ITEM", "version": 1}},
        {"basis": None},
        {"basis": {"start_basis": ""}},
        {"source_value": "1.0000000001"},
    ],
)
def test_operator_invalid_period_has_field_error(team, patch):
    from apps.workspace.schema import validate_one

    with pytest.raises(Fault) as error:
        validate_one(
            "operator_work_period",
            {
                **number(
                    "project", "operator_work_period", "1", "MONTH", basis={"start_basis": "تحویل"}
                ),
                **patch,
            },
        )
    assert error.value.field.startswith("operator_work_period.")


@pytest.mark.parametrize(
    "criteria_value,path",
    [
        ({"important": [{}]}, "criteria.important.0"),
        ({"important": [[]]}, "criteria.important.0"),
        ({"important": [1]}, "criteria.important.0"),
        ({"important": [True]}, "criteria.important.0"),
        ({"important": ["bad"]}, "criteria.important.0"),
        ({"important": {}}, "criteria.important"),
        ({"preferences": {"risk": {}}}, "criteria.preferences.risk"),
        ({"preferences": {"phase": [[]]}}, "criteria.preferences.phase"),
    ],
)
def test_search_malformed_members_400_envelope(client, criteria_value, path):
    import json

    r = client.get("/api/v1/core/opportunities", {"criteria": json.dumps(criteria_value)})
    assert r.status_code == 400
    assert path in r.json()["error"]["fields"]
    assert any("\u0600" <= c <= "\u06ff" for c in r.json()["error"]["message"])


@pytest.mark.parametrize(
    "value",
    [
        {"important": []},
        {"important": ["risk", "amount"]},
        {"preferences": {"unknown_preference": "unknown", "risk": None}},
    ],
)
def test_search_valid_empty_and_unknown_preserved(value):
    assert discovery.criteria(value) == value


@pytest.mark.parametrize("ids", [[{}, {}], [[], []], [1, 2]])
def test_compare_malformed_ids_controlled(ids):
    with pytest.raises(Fault) as error:
        discovery.compare(ids)
    assert error.value.status == 400


def test_operator_definition_reverse_protects_saved_quantity_and_guard(team):
    import importlib

    from django.apps import apps
    from django.db import connection
    from django.db.models.deletion import ProtectedError

    from apps.catalog.models import Quantity

    row = Quantity.from_payload(
        number("project", "operator_work_period", "3", "DAY", basis={"start_basis": "تحویل"})
    )
    row.save()
    original = row.as_dict()
    with pytest.raises(ProtectedError), transaction.atomic():
        importlib.import_module("apps.catalog.migrations.0010_operator_work_period").unseed(
            apps, SimpleNamespace(connection=connection)
        )
    row.refresh_from_db()
    assert row.as_dict() == original
    with connection.cursor() as cur:
        cur.execute("SELECT tgenabled FROM pg_trigger WHERE tgname='immutable_field'")
        assert cur.fetchone()[0] == "O"


def test_synthetic_seed_is_multicity_idempotent_and_forbidden_in_public(settings, monkeypatch):
    monkeypatch.setattr("apps.workspace.files.scan", lambda data: "clean")
    call_command("import_reference", verbosity=0)
    call_command("seed_core_demo", verbosity=0)
    first = list(
        Opportunity.objects.filter(synthetic=True, public_revision__isnull=False)
        .select_related("public_revision")
        .order_by("pk")
    )
    assert len(first) == 6
    mapped = [
        row.public_revision.snapshot for row in first if "city" in row.public_revision.snapshot
    ]
    assert len({snapshot["city"] for snapshot in mapped}) >= 4
    assert len({snapshot["province"] for snapshot in mapped}) >= 3
    versions = {row.pk: row.public_revision_id for row in first}
    call_command("seed_core_demo", verbosity=0)
    assert Opportunity.objects.filter(synthetic=True).count() == 6
    assert {
        row.pk: row.public_revision_id
        for row in Opportunity.objects.filter(synthetic=True).order_by("pk")
    } == versions
    settings.INVEST_ENV = "public"
    with pytest.raises(CommandError, match="forbidden"):
        call_command("seed_core_demo", verbosity=0)
