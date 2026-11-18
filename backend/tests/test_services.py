import uuid
from types import SimpleNamespace

import pytest
from django.db import DatabaseError, transaction

from apps.core import cases
from apps.core.models import Case, Opportunity, Report
from apps.identity.models import User
from apps.services import schemas, service
from apps.services.evaluation import evaluate
from apps.services.models import ServiceSubmission
from apps.workspace import service as ws
from apps.workspace.schema import Fault

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def service_reference_catalog(django_db_setup, django_db_blocker):
    from django.core.management import call_command

    with django_db_blocker.unblock():
        call_command("import_reference", verbosity=0)


def numeric(kind, key, value, unit, status="known"):
    return {
        "field": {
            "namespace": "invest.service." + kind.replace("-", "_"),
            "key": key,
            "version": 1,
        },
        "unit": {"code": unit, "version": 1},
        "status": status,
        "source_value": value,
        "basis": {"start_basis": "unspecified"} if unit in ["MONTH", "YEAR", "DAY"] else None,
    }


def test_temporary_housing_exact_and_hidden():
    k = "ma-renewal"
    raw = {
        "displacement": "yes",
        **{
            key: numeric(k, key, val, unit)
            for key, val, unit in [
                ("households", "۱۰", "ITEM"),
                ("deposit", "۲۰۰", "MILLION_TOMAN"),
                ("rent", "۵", "MILLION_TOMAN"),
                ("months", "۶", "MONTH"),
            ]
        },
    }
    r = evaluate(k, raw)
    assert r["calculations"]["deposit_total"]["value"] == "2000000000"
    assert r["calculations"]["rent_total"]["value"] == "300000000"
    raw["displacement"] = "no"
    r = evaluate(k, raw)
    assert not {"households", "deposit", "rent", "months"} & r["effective"].keys()
    assert r["calculations"]["deposit_total"]["value"] is None
    raw["displacement"] = "yes"
    raw["deposit"] = numeric(k, "deposit", None, "MILLION_TOMAN", "unknown")
    r = evaluate(k, raw)
    assert r["calculations"]["deposit_total"]["value"] is None
    assert r["calculations"]["rent_total"]["value"] == "300000000"


@pytest.mark.parametrize("kind", schemas.KINDS)
def test_service_draft_save_partial_and_report_no_case(kind):
    u = User.objects.create(mobile="+989120000001")
    session = SimpleNamespace(user=u)
    d = ws.create_draft(
        u,
        {
            "key": str(uuid.uuid4()),
            "kind": kind,
            "schema_version": 1,
            "owner": {"kind": "personal"},
        },
    )
    d = ws.save_draft(
        u,
        d["id"],
        {
            "key": str(uuid.uuid4()),
            "version": 1,
            "routes": [],
            "heritage_enabled": False,
            "values": {},
        },
    )
    assert d["version"] == 2
    report = service.create_report(session, d["id"], {"key": str(uuid.uuid4()), "version": 2})
    assert report["submitted"] is False
    assert (
        Report.objects.count() == 1
        and not Case.objects.exists()
        and not Opportunity.objects.exists()
    )
    with pytest.raises(Fault):
        service.submit(
            session,
            d["id"],
            {"key": str(uuid.uuid4()), "version": 2, "text": "بررسی کنید", "previous": None},
        )


def test_service_case_replay_snapshot_and_permission():
    u = User.objects.create(mobile="+989120000001")
    other = User.objects.create(mobile="+989120000002")
    s = SimpleNamespace(user=u)
    d = ws.create_draft(
        u,
        {
            "key": str(uuid.uuid4()),
            "kind": "ideas",
            "schema_version": 1,
            "owner": {"kind": "personal"},
        },
    )
    fs = schemas.fields("ideas")
    values = {
        k: next(iter(f["options"])) if f.get("options") else "ایده مصنوعی"
        for k, f in fs.items()
        if f["required"]
    }
    # Catalogue sector enum is dynamically populated.
    d = ws.save_draft(
        u,
        d["id"],
        {
            "key": str(uuid.uuid4()),
            "version": 1,
            "routes": [],
            "heritage_enabled": False,
            "values": values,
        },
    )
    payload = {
        "key": str(uuid.uuid4()),
        "version": 2,
        "text": "درخواست بررسی مصنوعی",
        "previous": None,
    }
    r = service.submit(s, d["id"], payload)
    assert r == service.submit(s, d["id"], payload)
    assert Case.objects.count() == ServiceSubmission.objects.count() == 1
    c = Case.objects.get()
    assert c.opportunity_id is None and c.submission_id is None
    with pytest.raises(Fault):
        cases.get_case(SimpleNamespace(user=other), c.pk)
    ws.save_draft(
        u,
        d["id"],
        {
            "key": str(uuid.uuid4()),
            "version": 2,
            "routes": [],
            "heritage_enabled": False,
            "values": {"title": "ویرایش بعدی"},
        },
    )
    assert ServiceSubmission.objects.get().snapshot["effective"]["title"] == "ایده مصنوعی"
    with pytest.raises(DatabaseError), transaction.atomic():
        ServiceSubmission.objects.filter(pk=c.service_submission_id).update(snapshot={})
    payload = {**payload, "text": "ورودی متفاوت"}
    with pytest.raises(Fault) as e:
        service.submit(s, d["id"], payload)
    assert e.value.status == 409


def test_hidden_raw_cannot_overwrite_and_is_restored():
    k = "ma-renewal"
    raw = {"displacement": "yes", "deposit": numeric(k, "deposit", "200", "MILLION_TOMAN")}
    merged = schemas.merge(
        k, raw, {"displacement": "no", "deposit": numeric(k, "deposit", "900", "MILLION_TOMAN")}
    )
    assert merged["deposit"] == raw["deposit"]
    assert "deposit" not in evaluate(k, merged)["effective"]
    assert (
        evaluate(k, {**merged, "displacement": "yes"})["effective"]["deposit"]["value"]
        == "200000000"
    )


@pytest.mark.parametrize("raw", [[], {"displacement": []}, {"bad": "x"}, {"notes": "\0"}])
def test_malformed(raw):
    with pytest.raises(Fault):
        evaluate("ma-renewal", raw)


def complete_raw(kind):
    raw = {}
    for _ in range(4):
        for k, f in schemas.current_fields(kind, raw).items():
            if not f["required"] or k in raw:
                continue
            if f["unit"]:
                raw[k] = numeric(kind, k, "1", f["unit"])
            elif f["kind"] in ["multi", "ordered_multi"]:
                raw[k] = [next(iter(f["options"]))]
            elif f["kind"] == "boolean":
                raw[k] = False
            elif f.get("options_by_parent"):
                raw[k] = f["options_by_parent"][raw[f["parent"]]][0][0]
            elif f["options"]:
                raw[k] = next(iter(f["options"]))
            else:
                raw[k] = "داده مصنوعی آزمون"
    return raw


@pytest.mark.parametrize("kind", schemas.KINDS)
def test_complete_service_download_submit_and_case_assignment(kind):
    u = User.objects.create(mobile="+12025550101")
    expert = User.objects.create(mobile="+12025550102", role="expert")
    admin = User.objects.create(mobile="+12025550103", role="admin")
    session = SimpleNamespace(user=u)
    d = ws.create_draft(
        u,
        {
            "key": str(uuid.uuid4()),
            "kind": kind,
            "schema_version": 1,
            "owner": {"kind": "personal"},
        },
    )
    d = ws.save_draft(
        u,
        d["id"],
        {
            "key": str(uuid.uuid4()),
            "version": 1,
            "routes": [],
            "heritage_enabled": False,
            "values": complete_raw(kind),
        },
    )
    assert not d["missing"]
    report = service.create_report(session, d["id"], {"key": str(uuid.uuid4()), "version": 2})
    assert '<html lang="fa"' in service.report_html(service.get_report(u, report["id"]))
    assert not Case.objects.exists()
    receipt = service.submit(
        session,
        d["id"],
        {"key": str(uuid.uuid4()), "version": 2, "text": "بررسی مصنوعی خدمت", "previous": None},
    )
    case = Case.objects.get(pk=receipt["case"]["id"])
    assert case.service_submission.kind == kind
    payload = dict(
        key=str(uuid.uuid4()),
        version=1,
        action="assign",
        text="ارجاع مصنوعی",
        next_action="",
        expert=str(expert.pk),
        recipient=None,
        kind=None,
        files=[],
        next_followup_at=None,
    )
    c = cases.action(
        SimpleNamespace(user=admin, assurance="test", sensitive=True), case.pk, payload
    )
    assert c["expert"]["id"] == str(expert.pk)
    assert (
        cases.get_case(SimpleNamespace(user=expert, assurance="test", sensitive=True), case.pk).pk
        == case.pk
    )
    with pytest.raises(Fault):
        cases.contact(SimpleNamespace(user=expert, assurance="test", sensitive=True), case.pk)


@pytest.mark.parametrize("key", ["field.namespace", "field.key", "unit.code"])
def test_exact_input_nul_before_lookup(key):
    value = numeric("proposal", "gap", "1.5", "BILLION_TOMAN")
    first, second = key.split(".")
    value[first][second] = "x\0"
    with pytest.raises(Fault):
        evaluate("proposal", {"gap": value})


@pytest.mark.parametrize("value", ["1,5", "1.1234567891", "1000000000000000000000000", "-1"])
def test_amount_precision_and_ambiguous(value):
    with pytest.raises(Fault):
        evaluate("proposal", {"gap": numeric("proposal", "gap", value, "TOMAN")})


def test_zero_unknown_and_resources_not_inferred():
    for status, value in [("known", "0"), ("unknown", None), ("not_applicable", None)]:
        result = evaluate("proposal", {"gap": numeric("proposal", "gap", value, "TOMAN", status)})
        assert result["effective"]["gap"]["status"] == status
        assert result["calculations"]["resource_difference"]["value"] is None
    result = evaluate(
        "proposal",
        {
            "total_need": numeric("proposal", "total_need", "۱٫۵", "BILLION_TOMAN"),
            "existing_resources": numeric(
                "proposal", "existing_resources", "۱۵۰۰", "MILLION_TOMAN"
            ),
        },
    )
    assert result["calculations"]["resource_difference"]["meaning"] == "balanced"


def test_currency_and_no_conversion():
    raw = {
        "route": "equity",
        "currency": "EUR",
        "amount": {
            "status": "known",
            "source_value": "۱٫۵",
            "currency": {"code": "EUR", "version": 1},
        },
    }
    result = evaluate("foreign-investment", raw)
    assert result["effective"]["amount"]["value"] == "1.5"
    assert result["effective"]["amount"]["base_conversion"] is None
    with pytest.raises(Fault):
        evaluate("foreign-investment", {**raw, "currency": "USD"})
    with pytest.raises(Fault):
        evaluate(
            "foreign-investment",
            {**raw, "amount": {**raw["amount"], "currency": {"code": "EUR", "version": 2}}},
        )


def test_current_options_and_support_hidden():
    raw = {"route": "support", "revenue": "unknown", "license": "issued", "blended": True}
    result = evaluate("foreign-investment", raw)
    assert not {"revenue", "license", "blended"} & result["effective"].keys()
    with pytest.raises(Fault):
        evaluate("foreign-investment", {"route": "no-such-route"})
    with pytest.raises(Fault):
        evaluate("land-preparation", {"types": ["lhstudy"], "answer_owner": "endowment"})


def test_charity_no_coefficient_and_land_order():
    r = evaluate(
        "charity",
        {
            "group": "health",
            "cause": "specialtyclinic",
            "type": "expertise",
            "description": "ظرفیت مصنوعی",
        },
    )
    assert (
        r["impact"]["status"] == "needs_expert_estimate"
        and r["impact"]["value"] is None
        and r["irr"] is None
    )
    r = evaluate(
        "land-preparation",
        {
            "role": "owner",
            "types": ["lp-legal", "lp-ownership"],
            "answer_lpServiceRight": "disputed",
        },
    )
    assert [x["id"] for x in r["entries"]] == ["lp-legal", "lp-ownership"]
    assert not r["assessment_blocked"] and r["expert_request_allowed"]


def test_report_escape_and_current_authority():
    from apps.workspace.models import Draft, Organization, Representation

    org = Organization.objects.create(
        name="سازمان مصنوعی", country="ایران", registration="S08-TEST"
    )
    old = User.objects.create(mobile="+12025550101")
    new = User.objects.create(mobile="+12025550102")
    rep = Representation.objects.create(user=old, organization=org, status="active")
    d = Draft.objects.create(
        kind="ideas", creator=old, organization=org, raw={"title": "<script>alert(1)</script>"}
    )
    r = service.create_report(
        SimpleNamespace(user=old), d.pk, {"key": str(uuid.uuid4()), "version": 1}
    )
    rendered = service.report_html(service.get_report(old, r["id"]))
    assert "<script>" not in rendered and "&lt;script&gt;" in rendered
    rep.status = "revoked"
    rep.save()
    Representation.objects.create(user=new, organization=org, status="active")
    with pytest.raises(Fault):
        service.get_report(old, r["id"])
    assert service.get_report(new, r["id"]).pk


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"raw": {"title": "\0"}, "schema_version": 1},
        {"raw": {"stage": []}, "schema_version": 1},
    ],
)
def test_real_endpoint_malformed_400(client, payload):
    token = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    response = client.post(
        "/api/v1/services/evaluate/proposal",
        payload,
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 400
    assert response.json()["error"]["fields"]


def test_new_definition_reverse_preserves_consumer_and_guards():
    import importlib

    from django.apps import apps
    from django.db import connection
    from django.db.models.deletion import ProtectedError

    from apps.catalog.models import MoneyValue

    value = MoneyValue.from_payload(numeric("proposal", "gap", "1.5", "BILLION_TOMAN"))
    value.save()
    original = value.as_dict()
    with pytest.raises(ProtectedError), transaction.atomic():
        importlib.import_module("apps.catalog.migrations.0011_service_values").unseed(
            apps, SimpleNamespace(connection=connection)
        )
    value.refresh_from_db()
    assert value.as_dict() == original
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tgname,tgenabled FROM pg_trigger "
            "WHERE tgname IN ('immutable_field','immutable_unit') ORDER BY tgname"
        )
        assert cursor.fetchall() == [("immutable_field", "O"), ("immutable_unit", "O")]


def test_core_advisory_effective_snapshot_and_role():
    from apps.core.discovery import criteria

    v = criteria(
        {
            "route": "investor",
            "preferences": {
                "subtypes": ["roads"],
                "adv:roads:revenue": "public",
                "adv:roads:toll": "notallowed",
                "adv:roads:buyer": "documented",
            },
        }
    )
    assert "adv:roads:toll" not in v["preferences"]
    assert v["preferences"]["adv:roads:buyer"] == "documented"
    v = criteria(
        {
            "route": "operator",
            "preferences": {
                "subtypes": ["roads"],
                "adv:roads:phase": "existing",
                "adv:roads:participation": "finance",
                "adv:roads:traffic": "ready",
            },
        }
    )
    assert not {"adv:roads:phase", "adv:roads:participation"} & v["preferences"].keys()
    assert v["preferences"]["adv:roads:traffic"] == "ready"


def test_noncash_quantity_roundtrip_and_no_impact():
    u = User.objects.create(mobile="+12025550101")
    d = ws.create_draft(
        u,
        {
            "key": str(uuid.uuid4()),
            "kind": "charity",
            "schema_version": 1,
            "owner": {"kind": "personal"},
        },
    )
    raw = {
        "group": "health",
        "cause": "specialtyclinic",
        "type": "expertise",
        "description": "جلسه مصنوعی",
        "noncash_capacity": numeric("charity", "noncash_capacity", "۱٫۵", "SESSION"),
        "noncash_unit": "جلسه تخصصی اعلامی؛ افراد یکتا نیست",
        "noncash_period": numeric("charity", "noncash_period", "6", "MONTH"),
    }
    d = ws.save_draft(
        u,
        d["id"],
        {
            "key": str(uuid.uuid4()),
            "version": 1,
            "routes": [],
            "heritage_enabled": False,
            "values": raw,
        },
    )
    assert d["effective"]["noncash_capacity"]["value"] == "1.5"
    assert d["effective"]["noncash_capacity"]["unit"] == {"code": "SESSION", "version": 1}
    assert evaluate("charity", d["raw"])["impact"]["value"] is None


def test_service_file_pending_save_and_reference_retention():
    from datetime import timedelta

    from django.utils import timezone

    from apps.workspace.files import purge
    from apps.workspace.models import Draft, PrivateFile

    u = User.objects.create(mobile="+12025550101")
    d = Draft.objects.create(kind="ideas", creator=u, raw=complete_raw("ideas"))
    f = PrivateFile.objects.create(
        draft=d,
        uploader=u,
        kind="document",
        name="synthetic.pdf",
        size=3,
        sha256="a" * 64,
        attached=True,
        status="pending_check",
        content=b"abc",
    )
    saved = ws.save_draft(
        u,
        d.pk,
        {
            "key": str(uuid.uuid4()),
            "version": 1,
            "routes": [],
            "heritage_enabled": False,
            "values": {"title": "ذخیره مستقل از بررسی فایل"},
        },
    )
    assert saved["version"] == 2
    with pytest.raises(Fault):
        service.submit(
            SimpleNamespace(user=u),
            d.pk,
            {"key": str(uuid.uuid4()), "version": 2, "text": "مصنوعی", "previous": None},
        )
    f.status = "clean"
    f.save()
    receipt = service.submit(
        SimpleNamespace(user=u),
        d.pk,
        {"key": str(uuid.uuid4()), "version": 2, "text": "مصنوعی", "previous": None},
    )
    assert receipt["case"]["service_files"] == [str(f.pk)]
    f.deleted_at = timezone.now() - timedelta(days=31)
    f.save()
    d.deleted_at = f.deleted_at
    d.save()
    purge()
    f.refresh_from_db()
    assert f.purged_at is None and bytes(f.content) == b"abc"


def test_service_organization_successor_revokes_consent_and_access():
    from apps.core import publication as pub
    from apps.workspace.models import PrivateFile, RepresentationRequest

    users = [
        User.objects.create(mobile="+1202555010" + str(i), role=r)
        for i, r in enumerate(["user", "user", "admin", "expert"])
    ]
    old, new, admin, expert = users
    admin_session = SimpleNamespace(user=admin, assurance="test", sensitive=True)
    expert_session = SimpleNamespace(user=expert, assurance="test", sensitive=True)

    def application(user):
        details = dict(
            name="سازمان مصنوعی",
            country="ایران",
            organization_type="نمونه",
            registration="S08-ORG",
            signatory="امضا",
            representative_name="نماینده",
            scope="درخواست خدمت",
            starts_on="2026-01-01",
            ends_on=None,
            no_expiry=True,
        )
        row = ws.organization(user, {"key": str(uuid.uuid4()), "details": details})
        req = RepresentationRequest.objects.get(pk=row["id"])
        for i in range(3):
            PrivateFile.objects.create(
                uploader=user,
                application=req,
                kind="document",
                name=f"synthetic-{i}.pdf",
                size=3,
                sha256="a" * 64,
                status="clean",
                attached=True,
                content=b"abc",
            )
        return req

    def approve(req):
        return pub.organization_review(
            admin_session,
            req.pk,
            dict(
                key=str(uuid.uuid4()),
                version=req.version,
                decision="approved",
                reason="بررسی مصنوعی",
                source="منبع مستقل مصنوعی",
                result="مقابله انجام شد",
            ),
        )

    first = application(old)
    approve(first)
    d = ws.create_draft(
        old,
        dict(
            key=str(uuid.uuid4()),
            kind="ideas",
            schema_version=1,
            owner={"kind": "organization", "request_id": str(first.pk)},
        ),
    )
    d = ws.save_draft(
        old,
        d["id"],
        dict(
            key=str(uuid.uuid4()),
            version=1,
            routes=[],
            heritage_enabled=False,
            values=complete_raw("ideas"),
        ),
    )
    receipt = service.submit(
        SimpleNamespace(user=old),
        d["id"],
        dict(key=str(uuid.uuid4()), version=2, text="مصنوعی", previous=None),
    )
    c = Case.objects.get(pk=receipt["case"]["id"])
    payload = dict(
        key=str(uuid.uuid4()),
        version=1,
        action="assign",
        text="ارجاع",
        next_action="",
        next_followup_at=None,
        expert=str(expert.pk),
        recipient=None,
        kind=None,
        files=[],
    )
    cases.action(admin_session, c.pk, payload)
    cases.action(
        SimpleNamespace(user=old),
        c.pk,
        {
            **payload,
            "key": str(uuid.uuid4()),
            "version": 2,
            "action": "grant",
            "recipient": str(expert.pk),
            "kind": "expert",
        },
    )
    assert cases.contact(expert_session, c.pk)["mobile"] == old.mobile
    successor = application(new)
    approve(successor)
    with pytest.raises(Fault):
        cases.get_case(SimpleNamespace(user=old), c.pk)
    with pytest.raises(Fault):
        cases.contact(expert_session, c.pk)
    assert cases.dto(cases.get_case(SimpleNamespace(user=new), c.pk))["customer_id"] == str(new.pk)
    c.refresh_from_db()
    cases.action(
        SimpleNamespace(user=new),
        c.pk,
        {
            **payload,
            "key": str(uuid.uuid4()),
            "version": c.version,
            "action": "grant",
            "recipient": str(expert.pk),
            "kind": "expert",
        },
    )
    assert cases.contact(expert_session, c.pk)["mobile"] == new.mobile


@pytest.mark.django_db(transaction=True)
def test_concurrent_service_sends_one_case_and_receipt():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.core.management import call_command
    from django.db import close_old_connections

    call_command("import_reference", verbosity=0)
    u = User.objects.create(mobile="+12025550101")
    for same_key in [True, False]:
        d = ws.create_draft(
            u,
            dict(key=str(uuid.uuid4()), kind="ideas", schema_version=1, owner={"kind": "personal"}),
        )
        d = ws.save_draft(
            u,
            d["id"],
            dict(
                key=str(uuid.uuid4()),
                version=1,
                routes=[],
                heritage_enabled=False,
                values=complete_raw("ideas"),
            ),
        )
        first_key = str(uuid.uuid4())
        barrier = Barrier(2)

        def send(index, barrier=barrier, d=d, first_key=first_key, same_key=same_key):
            close_old_connections()
            try:
                actor = User.objects.get(pk=u.pk)
                barrier.wait(timeout=10)
                return service.submit(
                    SimpleNamespace(user=actor),
                    d["id"],
                    dict(
                        key=first_key if same_key or not index else str(uuid.uuid4()),
                        version=2,
                        text="هم‌زمان مصنوعی",
                        previous=None,
                    ),
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            receipts = list(pool.map(send, [0, 1]))
        assert receipts[0]["case"]["id"] == receipts[1]["case"]["id"]
        assert Case.objects.filter(service_draft_id=d["id"]).count() == 1
        assert ServiceSubmission.objects.filter(draft_id=d["id"]).count() == 1
        if same_key:
            assert receipts[0] == receipts[1]


@pytest.mark.parametrize("route", ["equity", "contract", "credit", "execution", "support"])
def test_foreign_route_guards_and_hidden_fields(route):
    raw = {
        "route": route,
        "currency": "EUR",
        "rights": "direct",
        "revenue": "unknown",
        "license": "not-investment",
        "specific_credit_guarantee": "state",
        "specific_support_supportType": "unknown",
        "specific_support_continuity": "unknown",
        "amount": {
            "status": "known",
            "source_value": "1.500000001",
            "currency": {"code": "EUR", "version": 1},
        },
    }
    r = evaluate("foreign-investment", raw)
    assert r["expert_request_allowed"] and r["assessment_blocked"]
    assert r["effective"]["amount"]["value"] == "1.500000001" and r["irr"] is None
    if route == "support":
        assert not {"revenue", "license", "specific_credit_guarantee"} & r["effective"].keys()
    else:
        assert (
            not {"specific_support_supportType", "specific_support_continuity"}
            & r["effective"].keys()
        )


def test_demo_never_turns_into_actual_charity_impact():
    r = evaluate("charity", {"group": "learning", "cause": "school", "type": "cash", "demo": True})
    assert r["educational_example"]["formula"]
    assert r["educational_example"]["actual_impact"] is None and r["impact"]["value"] is None


def test_service_case_subject_constraint():
    from django.db import IntegrityError
    from django.utils import timezone

    u = User.objects.create(mobile="+12025550101")
    with pytest.raises(IntegrityError), transaction.atomic():
        Case.objects.create(customer=u, first_response_due=timezone.now())


def test_service_followup_requires_new_version_for_changed_files():
    from django.utils import timezone

    from apps.workspace.models import Draft, PrivateFile

    u = User.objects.create(mobile="+12025550101")
    session = SimpleNamespace(user=u)
    d = Draft.objects.create(kind="ideas", creator=u, raw=complete_raw("ideas"))
    first = service.submit(
        session, d.pk, dict(key=str(uuid.uuid4()), version=1, text="مصنوعی", previous=None)
    )
    c = Case.objects.get(pk=first["case"]["id"])
    c.status = "closed"
    c.save()
    f = PrivateFile.objects.create(
        draft=d,
        uploader=u,
        kind="document",
        name="synthetic.pdf",
        size=3,
        sha256="a" * 64,
        status="clean",
        attached=True,
        content=b"abc",
        received_at=timezone.now(),
    )
    with pytest.raises(Fault) as error:
        service.submit(
            session, d.pk, dict(key=str(uuid.uuid4()), version=1, text="پیگیری", previous=str(c.pk))
        )
    assert error.value.status == 409 and not c.service_submission.files
    d = ws.save_draft(
        u,
        d.pk,
        dict(key=str(uuid.uuid4()), version=1, routes=[], heritage_enabled=False, values={}),
    )
    followup = service.submit(
        session, d["id"], dict(key=str(uuid.uuid4()), version=2, text="پیگیری", previous=str(c.pk))
    )
    assert followup["case"]["service_files"] == [str(f.pk)]
    assert followup["case"]["previous"] == str(c.pk)


@pytest.mark.parametrize("subtypes", [10, "roads", True])
def test_malformed_advisory_subtypes_controlled(subtypes):
    from apps.core.discovery import criteria

    with pytest.raises(Fault) as error:
        criteria({"preferences": {"subtypes": subtypes, "adv:roads:revenue": "user"}})
    assert error.value.status == 400


def test_advisory_subtypes_none_is_unset():
    from apps.core.discovery import criteria

    assert criteria({"preferences": {"subtypes": None, "adv:roads:revenue": "user"}})[
        "preferences"
    ] == {"subtypes": None}


def test_service_initial_file_access_admin_expert_reassignment(client):
    from django.utils import timezone

    from apps.identity.sessions import mint_session
    from apps.workspace.models import Draft, PrivateFile

    u = User.objects.create(mobile="+12025550101")
    experts = [User.objects.create(mobile="+1202555010" + str(i), role="expert") for i in [2, 3]]
    d = Draft.objects.create(kind="ideas", creator=u, raw=complete_raw("ideas"))
    f = PrivateFile.objects.create(
        draft=d,
        uploader=u,
        kind="document",
        name="synthetic.pdf",
        size=3,
        sha256="a" * 64,
        status="clean",
        attached=True,
        content=b"abc",
    )
    receipt = service.submit(
        SimpleNamespace(user=u),
        d.pk,
        dict(key=str(uuid.uuid4()), version=1, text="مصنوعی", previous=None),
    )
    c = Case.objects.get(pk=receipt["case"]["id"])
    c.expert = experts[0]
    c.save()
    _, token = mint_session(experts[0], timezone.now(), sensitive=True)
    client.cookies["invest_session"] = token
    assert client.get("/api/v1/core/private-file/" + str(f.pk)).status_code == 200
    c.expert = experts[1]
    c.save()
    assert client.get("/api/v1/core/private-file/" + str(f.pk)).status_code == 403


def test_service_location_sentinels_preserve_reference_meaning():
    assert "all" not in schemas.current_fields("proposal", {})["province"]["options"]
    assert "unknown" in schemas.current_fields("foreign-investment", {})["province"]["options"]
    assert "any" in schemas.current_fields("charity", {})["province"]["options"]
    assert "all" in schemas.current_fields("land-preparation", {})["province"]["options"]


def test_private_report_bundle_preserves_clean_content_and_safe_names():
    import io
    import json
    import zipfile
    from pathlib import Path

    from apps.workspace.models import Draft, PrivateFile

    u = User.objects.create(mobile="+12025550101")
    d = Draft.objects.create(kind="ideas", creator=u, raw=complete_raw("ideas"))
    data = (Path(__file__).parent / "fixtures/s08/synthetic.pdf").read_bytes()
    f = PrivateFile.objects.create(
        draft=d,
        uploader=u,
        kind="document",
        name="../../synthetic.pdf",
        size=len(data),
        sha256="a" * 64,
        status="clean",
        attached=True,
        media_type="application/pdf",
        content=data,
    )
    result = service.create_report(
        SimpleNamespace(user=u), d.pk, dict(key=str(uuid.uuid4()), version=1)
    )
    assert result["download"].endswith("/package") and result["submitted"] is False
    report = service.get_report(u, result["id"])
    content = service.report_package(report)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        assert "report.html" in archive.namelist() and "manifest.json" in archive.namelist()
        manifest = json.loads(archive.read("manifest.json"))
        assert archive.read(manifest["files"][0]["path"]) == data
        assert all(
            not name.startswith("/") and ".." not in name.split("/") for name in archive.namelist()
        )
        assert b"<svg" in archive.read("report.html")
    assert not Case.objects.exists()
    f.status = "quarantined"
    f.save()
    with pytest.raises(Fault):
        service.report_package(report)


def test_legacy_invalid_service_field_cannot_hide_drafts_or_bypass_validation():
    from apps.workspace.models import Draft

    u = User.objects.create(mobile="+12025550101")
    raw = complete_raw("proposal")
    raw["province"] = "all"
    d = Draft.objects.create(kind="proposal", creator=u, raw=raw)
    dto = ws.list_drafts(u)[0]
    assert (
        dto["raw"] == raw
        and "province" in dto["validation_errors"]
        and "province" in dto["missing"]
    )
    d.refresh_from_db()
    assert d.raw == raw
    with pytest.raises(Fault):
        service.submit(
            SimpleNamespace(user=u),
            d.pk,
            dict(key=str(uuid.uuid4()), version=1, text="مصنوعی", previous=None),
        )
    raw["province"] = next(iter(schemas.current_fields("proposal", {})["province"]["options"]))
    saved = ws.save_draft(
        u,
        d.pk,
        dict(key=str(uuid.uuid4()), version=1, routes=[], heritage_enabled=False, values=raw),
    )
    assert not saved["validation_errors"] and saved["raw"]["province"] == raw["province"]


@pytest.mark.parametrize("types", [[{}], [[]], {}])
def test_malformed_land_selection_400_without_lookup_type_error(client, types):
    token = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    response = client.post(
        "/api/v1/services/evaluate/land-preparation",
        {"raw": {"types": types}, "schema_version": 1},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )
    assert response.status_code == 400 and response.json()["error"]["fields"]


@pytest.mark.django_db(transaction=True)
def test_service_representative_replacement_serializes_named_consent():
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event

    from django.core.management import call_command
    from django.db import close_old_connections
    from django.utils import timezone

    from apps.core.models import Consent
    from apps.workspace.models import Draft, Organization, Representation

    call_command("import_reference", verbosity=0)
    old = User.objects.create(mobile="+12025550101")
    new = User.objects.create(mobile="+12025550102")
    expert = User.objects.create(mobile="+12025550103", role="expert")
    org = Organization.objects.create(
        name="سازمان مصنوعی", country="ایران", registration="S08-RACE"
    )
    rep = Representation.objects.create(user=old, organization=org, status="active")
    d = Draft.objects.create(kind="ideas", creator=old, organization=org, raw=complete_raw("ideas"))
    receipt = service.submit(
        SimpleNamespace(user=old),
        d.pk,
        dict(key=str(uuid.uuid4()), version=1, text="مصنوعی", previous=None),
    )
    c = Case.objects.get(pk=receipt["case"]["id"])
    c.expert = expert
    c.save()
    entering = Event()

    def consent():
        close_old_connections()
        try:
            user = User.objects.get(pk=old.pk)
            entering.set()
            try:
                cases.action(
                    SimpleNamespace(user=user),
                    c.pk,
                    dict(
                        key=str(uuid.uuid4()),
                        version=c.version,
                        action="grant",
                        text="",
                        next_action="",
                        next_followup_at=None,
                        expert=None,
                        recipient=str(expert.pk),
                        kind="expert",
                        files=[],
                    ),
                )
                return 200
            except Fault as error:
                return error.status
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Organization.objects.select_for_update().get(pk=org.pk)
            # Same order as the approved independent organization review: revoke,
            # replace representative, commit. A new old-representative grant must wait.
            Consent.objects.filter(case=c, revoked_at__isnull=True).update(
                revoked_at=timezone.now()
            )
            future = pool.submit(consent)
            assert entering.wait(timeout=5)
            blocked = False
            try:
                future.result(timeout=0.4)
            except TimeoutError:
                blocked = True
            rep.status = "revoked"
            rep.save()
            Representation.objects.create(user=new, organization=org, status="active")
        status = future.result(timeout=10)
    assert blocked and status == 403
    assert not Consent.objects.filter(case=c, revoked_at__isnull=True).exists()


def test_service_child_without_parent_never_inferred_and_report_uses_parent_label():
    assert "cause" not in evaluate("charity", {"cause": "school"})["effective"]
    assert "cause" not in evaluate("charity", {"group": "health", "cause": "school"})["effective"]
    u = User.objects.create(mobile="+12025550101")
    from apps.workspace.models import Draft

    d = Draft.objects.create(
        kind="charity", creator=u, raw={"group": "learning", "cause": "school"}
    )
    r = service.create_report(SimpleNamespace(user=u), d.pk, dict(key=str(uuid.uuid4()), version=1))
    html = service.report_html(service.get_report(u, r["id"]))
    assert "مدرسه، ساخت، تکمیل یا تجهیز" in html
