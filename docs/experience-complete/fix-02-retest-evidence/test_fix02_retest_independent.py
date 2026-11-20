import importlib
import json
from pathlib import Path

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core import personal
from apps.core.models import Case, Report
from apps.core.reporting import render
from apps.identity.sessions import mint_session
from tests.test_core import (
    current_core_definitions,
    key,
    number,
    publish,
    team,
)


pytestmark = pytest.mark.django_db

EXPECTED_ROUTE_LABELS = {
    "buyer": "خریدار",
    "charity": "مشارکت اجتماعی و خیریه",
    "contractor": "پیمانکار",
    "fund": "صندوق سرمایه‌گذاری",
    "heritage": "مرمت و احیای میراث",
    "investor": "سرمایه‌گذار",
    "lessee": "مستأجر",
    "operator": "بهره‌بردار",
}


def command(action, value, **extra):
    return {"key": key(), "action": action, "value": value, **extra}


def route_snapshot(route):
    return {
        "template_version": 2,
        "report_id": "independent-route-contract",
        "opportunity": {
            "kind": "project",
            "routes": [route],
            "fields": {"title": "گزارش مستقل مسیر"},
        },
        "field_labels": {},
        "action_steps": ["بررسی مستقل"],
    }


def test_allowed_routes_and_vocabulary_are_exact_and_versioned():
    from apps.core import reporting

    core = Path(reporting.__file__).resolve().parent
    search_contract = json.loads((core / "search_fields.json").read_text())
    allowed = {
        route
        for field in search_contract
        for route in field.get("routes", [])
    }
    vocabulary = json.loads((core / "report-routes-v1.json").read_text())
    assert allowed == set(EXPECTED_ROUTE_LABELS)
    assert len(allowed) == 8
    assert vocabulary["version"] == 1
    assert vocabulary["routes"] == EXPECTED_ROUTE_LABELS


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_import_fails_explicitly_when_vocabulary_and_contract_diverge(monkeypatch, mutation):
    from apps.core import reporting

    original = Path.read_text

    def changed(path, *args, **kwargs):
        value = original(path, *args, **kwargs)
        if path.name != "report-routes-v1.json":
            return value
        data = json.loads(value)
        if mutation == "missing":
            data["routes"].pop("investor")
        else:
            data["routes"]["future"] = "مسیر آینده"
        return json.dumps(data, ensure_ascii=False)

    monkeypatch.setattr(Path, "read_text", changed)
    with pytest.raises(RuntimeError, match="واژه‌نامه مسیر گزارش"):
        importlib.reload(reporting)
    monkeypatch.setattr(Path, "read_text", original)
    importlib.reload(reporting)


@pytest.mark.parametrize("route,label", EXPECTED_ROUTE_LABELS.items())
def test_every_allowed_route_has_one_customer_facing_persian_label(route, label):
    body = render(route_snapshot(route))
    assert body.count(f"مسیر: {label}") == 1
    assert f"مسیر: {route}" not in body
    assert "شناسه تاریخی ناشناخته" not in body


def test_unknown_historical_route_is_escaped_explicit_and_not_guessed(team):
    raw = "future-route<script>alert(1)</script>"
    snapshot = route_snapshot(raw)
    snapshot["template_version"] = 1
    body = render(snapshot)
    assert "مسیر: شناسه تاریخی ناشناخته: future-route&lt;script&gt;" in body
    assert "مسیر شناخته‌شده‌ای حدس زده نشد" in body
    assert raw not in body
    assert all(f"مسیر: {label}" not in body for label in EXPECTED_ROUTE_LABELS.values())

    user = team[2].user
    report = Report.objects.create(user=user, snapshot=snapshot)
    _, token = mint_session(user, timezone.now())
    api = APIClient()
    api.cookies["invest_session"] = token
    response = api.get(f"/api/v1/core/reports/{report.pk}")
    assert response.status_code == 200
    assert response.content.decode() == body
    assert response["Content-Security-Policy"].endswith("sandbox")


def test_fresh_preview_first_download_and_redownload_are_frozen_authorized_and_complete(team):
    _, opportunity = publish(
        team,
        values={
            "title": "گزارش مستقل سرمایه‌گذار",
            "budget": number("project", "budget", "14.5", "BILLION_TOMAN"),
        },
    )
    value = {
        "criteria": {"route": "investor"},
        "guide_context": {
            "kind": "documents",
            "mine": [["ظرفیت متقاضی", "۱۲ میلیارد تومان <script>"]],
        },
    }
    api = APIClient()
    preview = api.post(f"/api/v1/core/guide/{opportunity.pk}", value, format="json")
    assert preview.status_code == 200
    preview_body = preview.json()["html"]

    user = team[2].user
    session, token = mint_session(user, timezone.now())
    receipt = personal.mutate(
        user,
        command("report", value, id=str(opportunity.pk)),
        session=session,
    )
    report = Report.objects.get(pk=receipt["report_id"])
    frozen_snapshot = json.loads(json.dumps(report.snapshot))
    cases_before = Case.objects.count()
    api.cookies["invest_session"] = token
    first = api.get(receipt["download"])
    second = api.get(receipt["download"])

    assert first.status_code == second.status_code == 200
    assert first.content == second.content == report.snapshot["rendered_html"].encode()
    assert first["Content-Security-Policy"] == "default-src 'none'; style-src 'unsafe-inline'; sandbox"
    assert first["Content-Disposition"] == 'attachment; filename="invest-guide.html"'
    first_body = first.content.decode()
    for expected in [
        "گزارش مستقل سرمایه‌گذار",
        "مسیر: سرمایه‌گذار",
        "نیاز مالی کل",
        "14.5 میلیارد تومان",
        "نوع پیگیری",
        "درخواست بررسی اسناد و شرایط",
        "ظرفیت متقاضی",
        "۱۲ میلیارد تومان &lt;script&gt;",
        "پاسخ‌های مؤثر ثبت‌شده",
        "پرونده کامل",
        "گام‌های اقدام",
    ]:
        assert expected in first_body
    assert "مسیر: investor" not in preview_body + first_body
    assert "مسیر: سرمایه‌گذار" in preview_body
    assert Case.objects.count() == cases_before

    report.refresh_from_db()
    assert report.snapshot == frozen_snapshot
    _, other_token = mint_session(team[3].user, timezone.now())
    other = APIClient()
    other.cookies["invest_session"] = other_token
    assert other.get(receipt["download"]).status_code == 404
    assert APIClient().get(receipt["download"]).status_code in (401, 403)


def test_old_frozen_html_is_returned_byte_for_byte_without_rewrite_or_case(team):
    historical_html = "<!doctype html><meta charset=utf-8><p>مسیر: investor</p>"
    user = team[2].user
    report = Report.objects.create(
        user=user,
        snapshot={"template_version": 2, "rendered_html": historical_html},
    )
    before = json.loads(json.dumps(report.snapshot))
    cases_before = Case.objects.count()
    _, token = mint_session(user, timezone.now())
    api = APIClient()
    api.cookies["invest_session"] = token
    response = api.get(f"/api/v1/core/reports/{report.pk}")
    assert response.status_code == 200
    assert response.content == historical_html.encode()
    report.refresh_from_db()
    assert report.snapshot == before
    assert Case.objects.count() == cases_before
