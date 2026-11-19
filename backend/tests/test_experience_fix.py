"""Regression for account-bound continuation and non-destructive edits."""

import json

import pytest
from django.utils import timezone

from apps.core import personal
from apps.core.models import LoginOperation, Report, Search
from apps.core.reporting import render
from apps.identity.sessions import mint_session
from apps.workspace.schema import Fault
from tests.test_core import current_core_definitions as definitions_fixture
from tests.test_core import key, publish
from tests.test_core import team as team_fixture

current_core_definitions = definitions_fixture
team = team_fixture

pytestmark = pytest.mark.django_db


def command(action, value, **extra):
    return {"key": key(), "action": action, "id": None, "value": value, **extra}


def test_handoff_rejects_other_account_and_other_session(team):
    first, other = team[2], team[3]
    data = command("search", {"name": "قصد حساب اول", "criteria": {}})
    LoginOperation.objects.create(
        key=data["key"], session=first, operation={"type": "save-criteria", **data["value"]}
    )
    same_user_new_session = mint_session(first.user, timezone.now())[0]
    for session in [other, same_user_new_session, None]:
        with pytest.raises(Fault):
            personal.mutate((session or first).user, data, session=session)
    assert not Search.objects.exists()
    result = personal.mutate(first.user, data, session=first)
    assert personal.mutate(first.user, data, session=first) == result
    assert Search.objects.filter(user=first.user).count() == 1
    first.revoked = True
    first.save()
    with pytest.raises(Fault):
        personal.mutate(first.user, data, session=first)


def test_profile_disjoint_fields_merge_and_stale_same_field_conflicts(team):
    user = team[2].user
    old = json.dumps({"name": "قدیم", "roles": ["investor"]})
    new = json.dumps({"name": "تغییر حرفه‌ای", "roles": ["investor", "contractor"]})
    personal.mutate(user, command("profile", {"name": "قدیم", "professional": old}))
    personal.mutate(user, command("profile", {"professional": new}, base={"professional": old}))
    personal.mutate(user, command("profile", {"name": "تغییر عمومی"}, base={"name": "قدیم"}))
    assert personal.state(user)["profile"] == {"name": "تغییر عمومی", "professional": new}
    with pytest.raises(Fault) as error:
        personal.mutate(user, command("profile", {"professional": old}, base={"professional": old}))
    assert error.value.status == 409
    assert personal.state(user)["profile"]["professional"] == new


def test_search_edit_lost_response_retry_and_stale_edit(team):
    user = team[2].user
    base = {"name": "قبلی", "criteria": {"route": "investor"}}
    personal.mutate(user, command("search", base))
    search = Search.objects.get(user=user)
    update = command(
        "search_update",
        {"name": "جدید", "criteria": {"route": "contractor"}},
        id=str(search.pk),
        base=base,
    )
    first = personal.mutate(user, update)
    assert personal.mutate(user, update) == first
    with pytest.raises(Fault) as error:
        personal.mutate(
            user, {**update, "key": key(), "value": {"name": "تب قدیمی", "criteria": {}}}
        )
    assert error.value.status == 409
    search.refresh_from_db()
    assert search.name == "جدید" and search.criteria["route"] == "contractor"


def test_report_semantic_sections_preview_download_and_history(team):
    from html.parser import HTMLParser

    class Sections(HTMLParser):
        def __init__(self):
            super().__init__()
            self.inside = False
            self.text = []

        def handle_starttag(self, tag, attrs):
            if tag == "section":
                self.inside = True

        def handle_endtag(self, tag):
            if tag == "section":
                self.inside = False

        def handle_data(self, value):
            if self.inside:
                self.text.append(value)

    _, op = publish(team, values={"title": "عنوان واقعی تاریخی"})
    value = {
        "criteria": {},
        "guide_context": {"kind": "visit", "mine": [["بودجه", "۱۲ میلیارد تومان"]]},
    }
    preview = personal.report_snapshot(op, value, "preview")
    receipt = personal.mutate(team[2].user, command("report", value, id=str(op.pk)))
    report = Report.objects.get(pk=receipt["report_id"])
    a, b = Sections(), Sections()
    a.feed(preview["rendered_html"])
    b.feed(report.snapshot["rendered_html"])
    # All sections before the operation-specific receipt have identical semantics.
    assert (
        a.text[: a.text.index("رسید و مبنای ثابت گزارش")]
        == b.text[: b.text.index("رسید و مبنای ثابت گزارش")]
    )
    for text in [
        "عنوان واقعی تاریخی",
        "پرونده کامل",
        "گام‌های اقدام",
        "بررسی امکان بازدید",
        "۱۲ میلیارد تومان",
    ]:
        assert text in report.snapshot["rendered_html"]
    legacy = {
        k: v for k, v in report.snapshot.items() if k not in ("rendered_html", "action_steps")
    }
    assert "در داده تاریخی این گزارش ثبت نشده" in render(legacy)


def test_cancel_after_consume_blocks_delayed_mutation(team):
    from apps.identity import otp

    session, token = mint_session(team[2].user, timezone.now())
    flow = otp.new_flow()["flow_token"]
    data = command("search", {"name": "لغوشده", "criteria": {}})
    handoff = {
        "destination": "/saved",
        "snapshot": {
            "version": 1,
            "key": data["key"],
            "operation": {"type": "save-criteria", **data["value"]},
        },
    }
    otp.intent(flow, "set", handoff, token)
    otp.intent(flow, "consume", session_token=token)
    otp.intent(flow, "cancel", session_token=token)
    with pytest.raises(Fault):
        personal.mutate(session.user, data, session=session)
    assert not Search.objects.filter(user=session.user).exists()
