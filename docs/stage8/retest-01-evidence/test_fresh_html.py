"""Independent HTTP downloads for false, zero, and unanswered semantics."""

import os
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from django.conf import settings
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.identity.models import User
from apps.identity.sessions import mint_session
from apps.services import service
from apps.workspace.models import Draft
from tests.test_services import complete_raw, numeric


def download(client, report_id):
    response = client.get(f"/api/v1/services/reports/{report_id}/download")
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/html")
    return response.content


@pytest.mark.django_db(transaction=True)
def test_fresh_html_preserves_false_zero_and_unanswered():
    assert settings.INVEST_ENV == "test"
    assert connection.settings_dict["NAME"].startswith("test_")
    evidence = Path(os.environ["RETEST_EVIDENCE_DIR"])

    user = User.objects.create_user(mobile="+12025550891")
    _, token = mint_session(user, timezone.now())
    client = APIClient()
    client.cookies["invest_session"] = token

    charity_raw = complete_raw("charity")
    charity_raw["demo"] = False
    charity = Draft.objects.create(kind="charity", creator=user, raw=charity_raw)
    charity_report = service.create_report(
        SimpleNamespace(user=user),
        charity.pk,
        {"key": str(uuid.uuid4()), "version": 1},
    )
    charity_html = download(client, charity_report["id"])
    assert "سناریوی آموزشی محله فرضی الف</dt><dd>خیر</dd>" in charity_html.decode()
    assert b">false<" not in charity_html
    (evidence / "fresh-charity-false.html").write_bytes(charity_html)

    proposal_raw = {"gap": numeric("proposal", "gap", "0", "TOMAN")}
    proposal = Draft.objects.create(kind="proposal", creator=user, raw=proposal_raw)
    proposal_report = service.create_report(
        SimpleNamespace(user=user),
        proposal.pk,
        {"key": str(uuid.uuid4()), "version": 1},
    )
    proposal_html = download(client, proposal_report["id"])
    decoded = proposal_html.decode()
    assert "0 تومان" in decoded
    assert "توضیحات تکمیلی" not in decoded
    (evidence / "fresh-proposal-zero-unanswered.html").write_bytes(proposal_html)
