import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from apps.assistant import evaluation
from apps.assistant.models import UsageReservation
from apps.assistant.provider import OUTPUT_SCHEMA, SYSTEM, TOOLS
from apps.core.models import Opportunity


SCRIPT = (
    Path("/scripts/run_assistant_evaluation.py")
    if Path("/scripts/run_assistant_evaluation.py").exists()
    else Path(__file__).resolve().parents[2] / "scripts/run_assistant_evaluation.py"
)
ORACLE = (
    Path("/app/specs/001-business-baseline/contracts/assistant-evaluation-oracle.json")
    if Path("/app/specs/001-business-baseline/contracts/assistant-evaluation-oracle.json").exists()
    else Path(__file__).resolve().parents[2]
    / "specs/001-business-baseline/contracts/assistant-evaluation-oracle.json"
)


def module():
    spec = importlib.util.spec_from_file_location("assistant_eval_runner", SCRIPT)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def oracle():
    return evaluation.load_oracle(ORACLE)


def proposed(case):
    fields = []
    for name, value in case["expected"]["criteria"]["exact"].items():
        fields.append(
            {
                "field": name,
                "status": value["status"],
                "value_json": evaluation.canonical(value["value"]),
                "unit": value["unit"],
                "basis_json": evaluation.canonical(value["basis"]),
            }
        )
    for name in case["expected"]["criteria"].get("unknown", []):
        fields.append(
            {
                "field": name,
                "status": "unknown",
                "value_json": "null",
                "unit": None,
                "basis_json": "null",
            }
        )
    clarification = case["expected"]["clarification"]
    return {
        "version": "assistant-model-extraction-v1",
        "fields": fields,
        "needs_clarification": clarification["status"] == "required",
        "clarification_fields": clarification["fields"],
    }


def output_for(case, *, citations=None):
    return {
        "answer": "پاسخ فارسی با مسیر دستی",
        "citations": citations or [],
        "next": ["ادامه دستی"],
        "model_proposed_criteria": proposed(case),
    }


def test_oracle_hash_schema_and_fixed_denominators():
    value = oracle()
    held = [case for case in value["cases"] if case["split"] == "held-out"]
    assert evaluation.ORACLE_SHA256 == "1cfe6230d7f5730ccbe4b11832ca81a893c2882e697cd3323b6abdd624fa2691"
    assert evaluation.held_out_hash(value) == evaluation.HELD_OUT_SHA256
    assert evaluation.context_hash(value) == evaluation.CONTEXT_SHA256
    assert sum(case["expected"]["applicability"]["extraction"]["applicable"] for case in held) == 44
    assert sum(case["expected"]["applicability"]["citation"]["applicable"] for case in held) == 24
    assert sum(len(case["expected"]["citations"]["required"]) for case in held) == 53
    assert sum(not case["execution"]["must_not_dispatch"] for case in value["cases"]) == 81


@pytest.mark.django_db
def test_seed_is_one_to_one_and_uses_frozen_public_revisions(settings):
    settings.INVEST_ENV = "test"
    value = oracle()
    seeded = evaluation.seed_public_context(value)
    assert len(seeded) == 15 == Opportunity.objects.filter(id__in=seeded).count()
    actual = {
        str(row.pk): str(row.public_revision_id)
        for row in Opportunity.objects.filter(id__in=seeded)
    }
    expected = {
        key: item["public_revision_id"]
        for key, item in value["public_context"]["opportunities"].items()
    }
    assert actual == expected
    assert evaluation.seed_public_context(value) == seeded


@pytest.mark.django_db
def test_injected_run_uses_product_prompt_tools_schema_and_never_sends_expected(settings):
    settings.INVEST_ENV = "test"
    value = oracle()
    evaluation.seed_public_context(value)
    runner = module()
    case = next(case for case in value["cases"] if case["id"] == "AI-E01-01")
    captured = []

    def transport(payload, key, timeout):
        captured.append(payload)
        return {
            "id": "opaque-injected",
            "model": payload["model"],
            "status": "completed",
            "output_text": json.dumps(output_for(case), ensure_ascii=False),
            "output": [],
            "usage": {"input_tokens": 10, "output_tokens": 10},
        }

    record, calls = runner._run_model_case(
        value, case, "gpt-6-luna", "smoke", transport, "injected-test-credential"
    )
    assert calls == 1 and record["metric"]["extraction"]["passed"]
    payload = captured[0]
    assert payload["tools"] == TOOLS
    assert payload["text"]["format"]["schema"] == OUTPUT_SCHEMA
    encoded = json.dumps(payload, ensure_ascii=False)
    assert payload["input"][0]["content"] == SYSTEM
    assert "allowed_alternatives" not in encoded
    assert "critical_failure" not in encoded
    assert '"normalized"' not in encoded
    assert UsageReservation.objects.get().model == "gpt-6-luna"


def test_extraction_scorer_rejects_extra_unknown_as_zero_and_wrong_clarification():
    value = oracle()
    case = next(
        case
        for case in value["cases"]
        if case["split"] == "held-out"
        and case["expected"]["applicability"]["extraction"]["applicable"]
    )
    good = output_for(case)
    assert evaluation.score_extraction(case, good)["passed"]
    extra = deepcopy(good)
    extra["model_proposed_criteria"]["fields"].append(
        {"field": "invented", "status": "known", "value_json": "0", "unit": None, "basis_json": "null"}
    )
    assert not evaluation.score_extraction(case, extra)["passed"]
    wrong = deepcopy(good)
    wrong["model_proposed_criteria"]["needs_clarification"] = not good["model_proposed_criteria"]["needs_clarification"]
    assert not evaluation.score_extraction(case, wrong)["passed"]
    unknown_case = next(
        item
        for item in value["cases"]
        if item["split"] == "held-out" and item["expected"]["criteria"]["unknown"]
    )
    unknown_good = output_for(unknown_case)
    assert evaluation.score_extraction(unknown_case, unknown_good)["passed"]
    unknown_as_zero = deepcopy(unknown_good)
    target = unknown_case["expected"]["criteria"]["unknown"][0]
    row = next(field for field in unknown_as_zero["model_proposed_criteria"]["fields"] if field["field"] == target)
    row.update(status="known", value_json="0")
    assert not evaluation.score_extraction(unknown_case, unknown_as_zero)["passed"]


def test_citation_scorer_exact_value_duplicate_missing_and_forgery_mutations():
    value = oracle()
    case = next(
        case
        for case in value["cases"]
        if case["split"] == "held-out" and case["expected"]["citations"]["required"]
    )
    citations = []
    for wanted in case["expected"]["citations"]["required"]:
        citations.append(
            {
                "id": wanted["opportunity_id"],
                "revision": wanted["revision"],
                "field": wanted["field"],
                "value_json": evaluation.canonical(
                    evaluation._context_value(value, wanted["opportunity_id"], wanted["field"])
                ),
            }
        )
    good = output_for(case, citations=citations)
    scored = evaluation.score_citations(value, case, good)
    assert scored["passed"] and scored["numerator"] == scored["denominator"]
    duplicate = output_for(case, citations=[*citations, citations[0]])
    duplicated = evaluation.score_citations(value, case, duplicate)
    assert duplicated["passed"] and duplicated["duplicates"] == 1
    missing = output_for(case, citations=citations[1:])
    assert not evaluation.score_citations(value, case, missing)["passed"]
    forged = deepcopy(good)
    forged["citations"][0]["value_json"] = '"ساختگی"'
    assert not evaluation.score_citations(value, case, forged)["guard"]


@pytest.mark.django_db
def test_router_scores_all_120_and_preflight_faults_never_dispatch(settings):
    settings.INVEST_ENV = "test"
    value = oracle()
    evaluation.seed_public_context(value)
    runner = module()
    calls = []
    for case in value["cases"]:
        _, observed = runner.prepare_case(case)
        assert evaluation.score_router(case, observed)["passed"], (
            case["id"], observed, case["expected"]["router"]
        )
        if case["execution"]["must_not_dispatch"] or case["execution"].get("provider_fault_injection"):
            record, count = runner._run_model_case(
                value,
                case,
                "gpt-6.2-sol",
                "eval",
                lambda *args: calls.append(args),
                "injected-test-credential",
            )
            assert count == 0 and record["failure_code"] in {None, "injected_fault"}
    assert calls == []


def test_resume_rejects_model_or_any_frozen_hash_version_mismatch():
    value = oracle()
    current = evaluation.version_manifest(
        value,
        commit="abc",
        mode="eval",
        versions={"prompt": "p", "tool": "t", "schema": "s", "router": "r"},
        timestamp="fixed",
    )
    prior = {
        "manifest": deepcopy(current),
        "records": [evaluation.sanitized_record("AI-E01-01", "gpt-6.2-sol", {})],
    }
    evaluation.assert_resume_compatible(prior, current, "gpt-6.2-sol")
    for key in ("oracle_sha256", "context_sha256", "held_out_sha256"):
        changed = deepcopy(prior)
        changed["manifest"][key] = "wrong"
        with pytest.raises(ValueError, match="resume_manifest_mismatch"):
            evaluation.assert_resume_compatible(changed, current, "gpt-6.2-sol")
    with pytest.raises(ValueError, match="resume_model_mismatch"):
        evaluation.assert_resume_compatible(prior, current, "gpt-6-luna")


def test_persisted_record_is_allowlisted_and_contains_no_raw_content_or_secret():
    record = evaluation.sanitized_record(
        "AI-E01-01",
        "gpt-6-luna",
        {"extraction": {"numerator": 1, "denominator": 1}},
        {"input_tokens": 2, "output_tokens": 3},
        "0.0001",
    )
    assert set(record) == evaluation.PERSISTED_RECORD_KEYS
    encoded = json.dumps(record, ensure_ascii=False)
    for forbidden in ("prompt", "response", "tool_payload", "گفتگو", "injected-test-credential"):
        assert forbidden not in encoded


def test_contract_mode_has_zero_provider_calls_cost_and_no_selection(monkeypatch, capsys):
    runner = module()
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--mode", "contract"])
    assert runner.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["provider_calls"] == 0 and result["cost_usd"] == "0"
    assert result["selection"] is None and result["human_persian_votes"] == 0
