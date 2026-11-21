import importlib.util
import json
import multiprocessing
import sys
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from apps.assistant import evaluation, evaluation_budget
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


def budget_manifest():
    return {
        "oracle_sha256": evaluation.ORACLE_SHA256,
        "held_out_sha256": evaluation.HELD_OUT_SHA256,
        "context_sha256": evaluation.CONTEXT_SHA256,
        "commit": "fixed-test-commit",
        "product_prompt_tool_schema_router_versions": {
            "prompt": "p",
            "tool": "t",
            "schema": "s",
            "router": "r",
        },
    }


def concurrent_reserve(path, request_hash, queue):
    try:
        ledger = evaluation_budget.CampaignLedger(Path(path), "2.00", budget_manifest())
        ledger.reserve(
            request_hash,
            case_id=request_hash[:8],
            model="gpt-6.2-sol",
            purpose="eval",
            reserved_usd=Decimal("1.20"),
        )
        queue.put("reserved")
    except evaluation_budget.CampaignBudgetError as exc:
        queue.put(str(exc))


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


def injected_transport_for(cases, model, captured):
    queue = iter(cases)

    def transport(payload, key, timeout):
        case = next(queue)
        captured.append(case["id"])
        return {
            "id": "opaque-injected",
            "model": model,
            "status": "completed",
            "output_text": json.dumps(output_for(case), ensure_ascii=False),
            "output": [],
            "usage": {"input_tokens": 10, "output_tokens": 10},
        }

    return transport


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
    assert payload["service_tier"] == "default"
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


@pytest.mark.django_db
def test_live_mode_requires_explicit_campaign_guard_before_credential(
    settings, monkeypatch, capsys
):
    settings.INVEST_ENV = "test"
    runner = module()
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--mode", "smoke"])
    monkeypatch.setattr(
        runner,
        "_credential",
        lambda: pytest.fail("credential_must_not_be_read_without_campaign_guard"),
    )
    assert runner.main() == 4
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "blocked_campaign_guard_required"
    assert result["provider_calls"] == 0 and result["cost_usd"] == "0"


def test_campaign_cap_exact_boundary_and_rejects_above_two_dollars(tmp_path):
    path = tmp_path / "campaign.json"
    ledger = evaluation_budget.CampaignLedger(path, "2.00", budget_manifest())
    ledger.reserve(
        "a" * 64,
        case_id="case-a",
        model="gpt-6.2-sol",
        purpose="smoke",
        reserved_usd=Decimal("2.00"),
    )
    assert ledger.summary()["exposure_usd"] == "2.00"
    with pytest.raises(evaluation_budget.CampaignBudgetError, match="campaign_budget_exhausted"):
        ledger.reserve(
            "b" * 64,
            case_id="case-b",
            model="gpt-6-luna",
            purpose="eval",
            reserved_usd=Decimal("0.0001"),
        )
    with pytest.raises(evaluation_budget.CampaignBudgetError, match="campaign_budget_out_of_range"):
        evaluation_budget.CampaignLedger(tmp_path / "too-much.json", "2.0001", budget_manifest())


def test_campaign_ledger_is_shared_across_modes_models_and_resume(tmp_path):
    path = tmp_path / "campaign.json"
    first = evaluation_budget.CampaignLedger(path, "2.00", budget_manifest())
    first.reserve(
        "c" * 64,
        case_id="smoke-sol",
        model="gpt-6.2-sol",
        purpose="smoke",
        reserved_usd=Decimal("0.104"),
    )
    first.settle(
        "c" * 64,
        model_returned="gpt-6.2-sol",
        usage={"input_tokens": 8000, "output_tokens": 1000, "calls": 1},
    )
    resumed = evaluation_budget.CampaignLedger(path, "2.00", budget_manifest())
    resumed.reserve(
        "d" * 64,
        case_id="eval-luna",
        model="gpt-6-luna",
        purpose="eval",
        reserved_usd=Decimal("0.0052"),
    )
    summary = resumed.summary()
    assert summary["actual_usd"] == "0.026"
    assert summary["reserved_usd"] == "0.0052"
    assert summary["exposure_usd"] == "0.0312"


def test_campaign_ledger_serializes_competing_processes(tmp_path):
    path = tmp_path / "campaign.json"
    evaluation_budget.CampaignLedger(path, "2.00", budget_manifest())
    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    processes = [
        context.Process(target=concurrent_reserve, args=(str(path), character * 64, queue))
        for character in ("e", "f")
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(10)
        assert process.exitcode == 0
    assert sorted(queue.get(timeout=2) for _ in processes) == [
        "campaign_budget_exhausted",
        "reserved",
    ]


def test_retry_unknown_cost_remains_held_and_blocks_reuse(tmp_path):
    path = tmp_path / "campaign.json"
    ledger = evaluation_budget.CampaignLedger(path, "0.104", budget_manifest())
    ledger.reserve(
        "1" * 64,
        case_id="unknown",
        model="gpt-6.2-sol",
        purpose="eval",
        reserved_usd=Decimal("0.104"),
    )
    ledger.hold_unknown("1" * 64, calls=1, failure_code="timeout")
    assert ledger.summary()["unknown_usd"] == "0.104"
    with pytest.raises(evaluation_budget.CampaignBudgetError, match="campaign_budget_exhausted"):
        ledger.reserve(
            "2" * 64,
            case_id="retry",
            model="gpt-6.2-sol",
            purpose="eval",
            reserved_usd=Decimal("0.104"),
        )


@pytest.mark.parametrize(
    ("returned,usage,error"),
    [
        ("gpt-6-luna", {"input_tokens": 1, "output_tokens": 1, "calls": 1}, "model_mismatch"),
        ("gpt-6.2-sol", {"input_tokens": 1, "output_tokens": 1}, "missing_or_invalid_usage"),
    ],
)
def test_model_or_usage_mismatch_fails_closed(tmp_path, returned, usage, error):
    ledger = evaluation_budget.CampaignLedger(
        tmp_path / (error + ".json"), "2.00", budget_manifest()
    )
    ledger.reserve(
        "3" * 64,
        case_id="bad-result",
        model="gpt-6.2-sol",
        purpose="eval",
        reserved_usd=Decimal("0.104"),
    )
    with pytest.raises(evaluation_budget.CampaignBudgetError, match=error):
        ledger.settle("3" * 64, model_returned=returned, usage=usage)
    assert ledger.summary()["unknown_usd"] == "0.104"


def test_price_version_mismatch_and_content_leak_are_rejected(tmp_path):
    path = tmp_path / "campaign.json"
    ledger = evaluation_budget.CampaignLedger(path, "2.00", budget_manifest())
    ledger.reserve(
        "4" * 64,
        case_id="AI-E01-01",
        model="gpt-6-luna",
        purpose="smoke",
        reserved_usd=Decimal("0.0052"),
    )
    encoded = path.read_text()
    for forbidden in (
        "private-secret",
        "متن گفتگو",
        "raw_response",
        "نمونه محتوای پرامپت",
    ):
        assert forbidden not in encoded
    changed_manifest = budget_manifest()
    changed_manifest["commit"] = "different-source-commit"
    with pytest.raises(
        evaluation_budget.CampaignBudgetError, match="campaign_ledger_mismatch"
    ):
        evaluation_budget.CampaignLedger(path, "2.00", changed_manifest)
    changed = json.loads(encoded)
    changed["price_version"] = "changed"
    path.write_text(json.dumps(changed))
    with pytest.raises(evaluation_budget.CampaignBudgetError, match="campaign_ledger_mismatch"):
        evaluation_budget.CampaignLedger(path, "2.00", budget_manifest())


@pytest.mark.django_db
def test_insufficient_campaign_budget_stops_before_provider_call(settings, tmp_path):
    settings.INVEST_ENV = "test"
    value = oracle()
    evaluation.seed_public_context(value)
    runner = module()
    case = next(case for case in value["cases"] if case["id"] == "AI-E01-01")
    manifest = evaluation.version_manifest(
        value,
        commit="abc",
        mode="smoke",
        versions=runner._versions(),
        timestamp="fixed",
    )
    ledger = evaluation_budget.CampaignLedger(tmp_path / "campaign.json", "0.001", manifest)
    calls = []
    with pytest.raises(evaluation_budget.CampaignBudgetError, match="campaign_budget_exhausted"):
        runner._run_model_case(
            value,
            case,
            "gpt-6-luna",
            "smoke",
            lambda *args: calls.append(args),
            "injected-test-credential",
            campaign=ledger,
            manifest=manifest,
        )
    assert calls == []


def test_live_credential_has_no_environment_value_fallback(monkeypatch):
    runner = module()
    monkeypatch.delenv("OPENAI_EVAL_API_KEY_FILE", raising=False)
    monkeypatch.setenv("OPENAI_EVAL_API_KEY", "must-not-be-used")
    assert runner._credential() == ""


@pytest.mark.django_db
def test_full_injected_campaign_shares_ledger_and_resumes_without_duplicate_call(
    settings, monkeypatch, tmp_path, capsys
):
    settings.INVEST_ENV = "test"
    value = oracle()
    runner = module()
    monkeypatch.setattr(runner, "_safe_target", lambda value: Path(value).resolve())
    ledger = tmp_path / "campaign.json"
    smoke_output = tmp_path / "smoke-luna.json"
    luna_output = tmp_path / "eval-luna.json"
    sol_output = tmp_path / "eval-sol.json"

    smoke_cases = runner._selected(value, "smoke")
    held_out = runner._selected(value, "eval")
    eligible_held_out = [
        case
        for case in held_out
        if not case["execution"]["must_not_dispatch"]
        and not case["execution"].get("provider_fault_injection")
    ]
    assert len(smoke_cases) == 20
    assert len(held_out) == 80
    assert len(eligible_held_out) == 48

    captured = []
    shared = ["--campaign-budget-usd", "2.00", "--campaign-ledger", str(ledger)]
    assert runner.main(
        injected_transport_for(smoke_cases, "gpt-6-luna", captured),
        ["--mode", "smoke", "--model", "gpt-6-luna", "--output", str(smoke_output), *shared],
    ) == 0
    capsys.readouterr()

    with pytest.raises(runner.ControlledHarnessInterrupt, match="after_case:21"):
        runner.main(
            injected_transport_for(eligible_held_out, "gpt-6-luna", captured),
            ["--mode", "eval", "--model", "gpt-6-luna", "--output", str(luna_output), *shared],
            interrupt_after_cases=21,
        )
    checkpoint = json.loads(luna_output.read_text())
    assert len(checkpoint["records"]) == 21
    checkpoint_calls = checkpoint["provider_calls"]
    done = {row["case_id"] for row in checkpoint["records"]}
    remaining_luna = [case for case in eligible_held_out if case["id"] not in done]
    assert runner.main(
        injected_transport_for(remaining_luna, "gpt-6-luna", captured),
        ["--mode", "eval", "--model", "gpt-6-luna", "--output", str(luna_output), *shared],
    ) == 0
    capsys.readouterr()
    completed_luna = json.loads(luna_output.read_text())
    assert len(completed_luna["records"]) == 80
    assert completed_luna["provider_calls"] == 48
    assert completed_luna["provider_calls"] >= checkpoint_calls

    assert runner.main(
        injected_transport_for(eligible_held_out, "gpt-6.2-sol", captured),
        ["--mode", "eval", "--model", "gpt-6.2-sol", "--output", str(sol_output), *shared],
    ) == 0
    capsys.readouterr()
    completed_sol = json.loads(sol_output.read_text())
    assert len(completed_sol["records"]) == 80
    assert completed_sol["provider_calls"] == 48

    before_replay = len(captured)

    def unexpected_provider_call(*args):
        pytest.fail("settled case dispatched again during resume")

    assert runner.main(
        unexpected_provider_call,
        ["--mode", "eval", "--model", "gpt-6-luna", "--output", str(luna_output), *shared],
    ) == 0
    capsys.readouterr()
    assert len(captured) == before_replay == 116

    persisted = json.loads(ledger.read_text())
    assert len(persisted["entries"]) == 116
    assert {entry["status"] for entry in persisted["entries"].values()} == {"completed"}
    assert Decimal(persisted["cap_usd"]) == Decimal("2.00")
    assert all(entry["service_tier"] == "standard" for entry in persisted["entries"].values())
