"""مکمل مستقل TEST-EXPERIENCE-RETEST-01؛ معیار از AC-PC و قراردادهای 009/010."""
from types import SimpleNamespace

import pytest

from apps.core import personal
from apps.core import preferences
from apps.services import advisories
from tests.test_core import publish, team


pytestmark = pytest.mark.django_db


def result(snapshot, route, wanted):
    subject = SimpleNamespace(snapshot=snapshot, kind="project")
    return list(preferences.evaluate(subject, route, wanted))


def test_four_landhousing_contexts_are_effective_and_buyer_is_conditional():
    config = advisories.config("lhstudy")
    by_id = {row["id"]: row for row in config["questions"]}
    base = {
        key: by_id[key]["options"][0]["value"]
        for key in ["revenue", "lhPlan", "lhHandover"]
    }
    public = next(option["value"] for option in by_id["revenue"]["options"] if option["value"] == "public")
    buyer = by_id["buyer"]["options"][0]["value"]
    active = advisories.evaluate("lhstudy", {**base, "revenue": public, "buyer": buyer})
    assert active["effective_answers"]["buyer"] == buyer
    assert all(active["effective_answers"][key] == base[key] for key in ["lhPlan", "lhHandover"])
    non_public = next(option["value"] for option in by_id["revenue"]["options"] if option["value"] != "public")
    inactive = advisories.evaluate("lhstudy", {**base, "revenue": non_public, "buyer": buyer})
    assert "buyer" not in inactive["effective_answers"]
    assert buyer not in str(inactive["guidance"])


@pytest.mark.parametrize(
    "field,snapshot,wanted,axis,state",
    [
        ("fundType", {"fund_type": "fixed"}, "fixed", "category", "met"),
        ("payout", {"payout": "1"}, "1", "returns", "met"),
        ("risk", {"risk": "medium"}, "high", "risk", "met"),
        ("heritageReturn", {"heritage_returns": "lease"}, "lease", "conditions", "met"),
        ("heritageUse", {"heritage_uses": "cafe"}, "cafe", "conditions", "met"),
        ("heritagePayment", {"heritage_payments": "delivery"}, "delivery", "conditions", "met"),
    ],
)
def test_runtime_context_rules_produce_expected_axis(field, snapshot, wanted, axis, state):
    route = "fund" if field in {"fundType", "payout", "risk"} else "heritage"
    criteria = {field: wanted}
    if field == "heritagePayment":
        criteria["heritageReturn"] = "fee"
    output = result(snapshot, route, criteria)
    pairs = [(row[0], row[1]) for row in output]
    if field == "heritagePayment":
        assert (axis, state) in pairs
    else:
        assert pairs == [(axis, state)]


def test_heritage_payment_is_inactive_outside_fee_or_mixed():
    output = result({"heritage_payments": "delivery"}, "heritage", {"heritageReturn": "lease", "heritagePayment": "delivery"})
    assert all(row[2].find("heritage_payments") < 0 for row in output)


def test_heritage_years_needs_matching_time_basis():
    snapshot = {
        "heritage_years": {
            "status": "known",
            "source_value": "8",
            "value": "8",
            "unit": {"code": "YEAR", "version": 1},
            "basis": {"start_basis": "تحویل"},
        }
    }
    assert result(snapshot, "heritage", {"heritageReturn": "lease", "heritageYears": 5})[-1][1] == "unknown"
    assert result(snapshot, "heritage", {"heritageReturn": "lease", "heritageYears": 5, "basis:heritageYears": "تحویل"})[-1][1] == "met"


@pytest.mark.parametrize("field", ["fundReturnMin", "irrMin"])
def test_partial_return_controls_are_unknown_not_fabricated(field):
    route = "fund" if field == "fundReturnMin" else "heritage"
    output = result({}, route, {field: 12})
    assert output == [("returns", "unknown", "حد بازده بدون مبنای کامل قابل تطبیق نیست.")]


def test_irr_basis_and_price_are_context_not_independent_scores():
    assert result({}, "heritage", {"irrBasis": "project", "irrPrice": "nominal"}) == []


def test_unverified_bank_name_cannot_create_verified_guarantee(monkeypatch):
    monkeypatch.setattr("apps.core.publication.bank_verified", lambda subject: False)
    output = result({}, "fund", {"bankGuarantee": "both"})
    assert output[0][:2] == ("risk", "unknown")


def test_general_special_notes_neither_score_nor_create_authority():
    values = {"general": "ready", "special": "ready", "notes": "متن کامل مستقل"}
    assert preferences.active_preferences("investor", values) == values
    assert result({}, "investor", values) == []


def test_report_route_enum_is_human_readable_persian(team):
    _, opportunity = publish(team, values={"title": "عنوان فارسی مستقل"})
    body = personal.report_snapshot(
        opportunity,
        {"criteria": {"route": "investor"}, "guide_context": {"kind": "visit"}},
        "independent-route-label",
    )["rendered_html"]
    assert "مسیر: investor" not in body
    assert "مسیر: سرمایه‌گذار" in body
