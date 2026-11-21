#!/usr/bin/env python3
"""Run the locked S09 oracle through the real product path without persisting content."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

from apps.assistant import quota  # noqa: E402
from apps.assistant.evaluation import (  # noqa: E402
    ORACLE_SHA256,
    assert_resume_compatible,
    canonical,
    load_oracle,
    sanitized_record,
    score_citations,
    score_extraction,
    score_router,
    seed_public_context,
    version_manifest,
)
from apps.assistant.evaluation_budget import (  # noqa: E402
    CampaignBudgetError,
    CampaignLedger,
    conservative_reservation_usd,
    content_free_request_hash,
)
from apps.assistant.models import QuotaPolicy  # noqa: E402
from apps.assistant.orchestrator import (  # noqa: E402
    prepare_turn,
    product_tool_runner,
    provider_context,
)
from apps.assistant.provider import OpenAIProvider, ProviderError  # noqa: E402
from apps.assistant.quota import PROMPT_VERSION, SCHEMA_VERSION, TOOL_VERSION  # noqa: E402
from apps.assistant.routing import ROUTER_VERSION  # noqa: E402

ORACLE = ROOT / "specs/001-business-baseline/contracts/assistant-evaluation-oracle.json"
ALLOWED_FAILURES = {
    None,
    "injected_fault",
    "provider_unavailable",
    "timeout",
    "invalid_output",
    "invalid_citation",
    "invalid_model_extraction",
    "token_limit",
    "call_limit",
    "rate_limited",
    "budget_exhausted",
    "purpose_budget_exhausted",
    "principal_budget_exhausted",
    "model_mismatch",
    "missing_usage",
}


def _credential():
    path = os.environ.get("OPENAI_EVAL_API_KEY_FILE", "")
    if path and Path(path).is_file():
        value = Path(path).read_text().strip()
        if not value or value.lower() in {"changeme", "placeholder", "your-api-key"} or value.startswith("sk-example"):
            return ""
        return value
    return ""


def _commit():
    declared = os.environ.get("INVEST_SOURCE_COMMIT", "").strip()
    if len(declared) == 40 and all(character in "0123456789abcdef" for character in declared):
        return declared
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _versions():
    return {
        "prompt": PROMPT_VERSION,
        "tool": TOOL_VERSION,
        "schema": SCHEMA_VERSION,
        "router": ROUTER_VERSION,
    }


def _product_criteria(case):
    confirmed = {}
    for turn in case["execution"].get("history", []):
        confirmed.update(turn.get("confirmed_criteria") or {})
    picker = case["execution"].get("setup", {}).get("explicit_saved_picker_selection") or {}
    confirmed.update(picker.get("criteria") or {})
    result = {}
    for name, value in confirmed.items():
        if value.get("status") != "known":
            continue
        raw = value.get("value")
        if name == "location":
            result[value.get("basis") or "province"] = raw
        else:
            result[name] = raw
    return result or None


def _history(case):
    return [
        {"role": turn["role"], "text": turn["text"]}
        for turn in case["execution"].get("history", [])
    ]


def prepare_case(case):
    execution = case["execution"]
    if execution["must_not_dispatch"]:
        reason = execution["setup"]["preflight_reason"]
        return None, {"route": "not_dispatched", "reason": "preflight:" + reason, "model": None}
    prepared = prepare_turn(
        message=execution["message"],
        criteria=_product_criteria(case),
        opportunity_ids=execution.get("opportunity_ids") or [],
        history=_history(case),
    )
    code = prepared.decision.code
    semantic_route = "complex" if code.startswith("complex") or code == "multi_item_comparison" else "simple"
    semantic_reason = {
        "multi_item_comparison": "complex_comparison",
        "simple_explanation": "simple_explanation",
        "simple_comparison": "simple_comparison",
        "simple_search": "simple_search",
        "clarification": "clarification",
        "complex_comparison": "complex_comparison",
        "complex_constraints": "complex_constraints",
    }.get(code, code)
    observed = {
        "route": semantic_route,
        "reason": semantic_reason,
        "model": prepared.decision.model,
    }
    return prepared, observed


def _policy():
    return QuotaPolicy.objects.filter(active=True).order_by("-version").first() or QuotaPolicy.objects.create(version=1)


def _principal():
    return quota.internal_evaluation_principal("s09:locked-oracle-v1")


def _reserve(case, model, purpose):
    payload_hash = __import__("hashlib").sha256(
        canonical(
            {
                "case": case["id"],
                "model": model,
                "oracle": ORACLE_SHA256,
                "versions": _versions(),
            }
        ).encode()
    ).hexdigest()
    return quota.reserve(
        _principal(),
        f"assistant-eval:{model}:{case['id']}",
        payload_hash,
        model,
        purpose,
        route_code="fixed_model_evaluation",
        route_reason="isolated_harness_override",
        router_version=ROUTER_VERSION,
    )


def _run_model_case(
    oracle,
    case,
    model,
    purpose,
    transport,
    key,
    *,
    campaign=None,
    manifest=None,
):
    prepared, observed = prepare_case(case)
    router_metric = score_router(case, observed)
    if prepared is None:
        metrics = {
            "extraction": score_extraction(case, {}),
            "citation": score_citations(oracle, case, {}),
            "router": router_metric,
            "persian": {"applicable": False, "votes": 0},
        }
        return sanitized_record(case["id"], None, metrics), 0
    if case["execution"].get("provider_fault_injection"):
        metrics = {
            "extraction": score_extraction(case, {}, "injected_fault"),
            "citation": score_citations(oracle, case, {}, "injected_fault"),
            "router": router_metric,
            "persian": {"applicable": False, "votes": 0},
        }
        return sanitized_record(case["id"], model, metrics, failure_code="injected_fault"), 0
    reservation, policy, replay = _reserve(case, model, purpose)
    campaign_hash = None
    if campaign is not None:
        if manifest is None:
            quota.settle(reservation, status="failed", failure_code="campaign_manifest_missing")
            raise CampaignBudgetError("campaign_manifest_missing")
        campaign_hash = content_free_request_hash(
            case_id=case["id"], model=model, purpose=purpose, manifest=manifest
        )
        existing = campaign.entry(campaign_hash)
        if existing and existing.get("status") == "completed" and existing.get("outcome"):
            if reservation.status == "reserved":
                quota.settle(reservation, status="completed", usage=existing["usage"], model_returned=existing["model_returned"])
            return existing["outcome"], 0
        if replay and reservation.status != "reserved":
            raise CampaignBudgetError("evaluation_replay_without_recoverable_outcome")
        if existing and reservation.provider_calls:
            quota.settle(reservation, status="held", failure_code="resume_unknown_provider_result")
            raise CampaignBudgetError("resume_unknown_provider_result")
        try:
            if not existing:
                campaign.reserve(
                    campaign_hash,
                    case_id=case["id"], model=model, purpose=purpose,
                    reserved_usd=conservative_reservation_usd(model, policy),
                )
        except CampaignBudgetError:
            quota.settle(reservation, status="failed", failure_code="campaign_budget_blocked")
            raise
    provider = OpenAIProvider(key, settings.ASSISTANT_OPENAI_BASE_URL)
    if transport is not None:
        provider._request = transport
    try:
        result = provider.complete(
            provider_context(prepared, lambda: quota.claim_provider_call(reservation)),
            product_tool_runner(prepared),
            policy,
            reservation,
        )
        output = result.output
        failure = None
        usage = result.usage
        calls = int(usage.get("calls", 0))
    except CampaignBudgetError as exc:
        quota.settle(
            reservation,
            status="held",
            usage=getattr(result, "usage", {}),
            model_returned=getattr(result, "model", ""),
            request_id=getattr(result, "request_id", ""),
            failure_code=str(exc),
        )
        raise
    except ProviderError as exc:
        output = {}
        failure = exc.code if exc.code in ALLOWED_FAILURES else "provider_unavailable"
        quota.settle(
            reservation,
            status="held" if exc.unknown_cost else "failed",
            usage={**exc.usage, "calls": exc.calls},
            request_id=exc.request_id,
            failure_code=failure,
        )
        usage = exc.usage
        calls = exc.calls
        if campaign is not None:
            if calls:
                campaign.hold_unknown(
                    campaign_hash,
                    calls=calls,
                    failure_code=failure,
                    model_returned=exc.model_returned,
                    usage=exc.usage,
                )
            else:
                campaign.cancel_before_call(campaign_hash)
    metrics = {
        "extraction": score_extraction(case, output, failure),
        "citation": score_citations(oracle, case, output, failure),
        "router": router_metric,
        "persian": {
            "applicable": case["expected"]["applicability"]["persian"]["applicable"],
            "votes": 0,
        },
    }
    cost = usage.get("cost_usd") or "0"
    record = sanitized_record(case["id"], model, metrics, usage, cost, failure)
    if campaign is not None and failure is None:
        campaign.settle(campaign_hash, model_returned=result.model, usage=result.usage, outcome=record)
        quota.settle(reservation, status="completed", usage=result.usage, model_returned=result.model, request_id=result.request_id)
    output = None
    return record, calls


def _selected(oracle, mode):
    if mode == "smoke":
        ids = set(oracle["smoke_contract"]["eligible_development_case_ids"])
        return [case for case in oracle["cases"] if case["id"] in ids]
    return [case for case in oracle["cases"] if case["split"] == "held-out"]


def _safe_target(value):
    target = Path(value).resolve()
    allowed = (ROOT / ".tools").resolve()
    if allowed not in target.parents:
        raise ValueError("output_must_be_under_tools")
    return target


def _write_atomic(target, value):
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def main(transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["contract", "router", "smoke", "eval"], default="contract")
    parser.add_argument("--model", choices=["gpt-6.2-sol", "gpt-6-luna"], default="gpt-6.2-sol")
    parser.add_argument("--confirm-live", action="store_true")
    parser.add_argument("--output")
    parser.add_argument("--campaign-budget-usd")
    parser.add_argument("--campaign-ledger")
    args = parser.parse_args()
    oracle = load_oracle(ORACLE)
    manifest = version_manifest(
        oracle, commit=_commit(), mode=args.mode, versions=_versions()
    )
    counts = {
        "total": 120,
        "development": 40,
        "held_out": 80,
        "extraction_held_out": 44,
        "citation_held_out_cases": 24,
        "citation_held_out_tuples": 53,
        "dispatch_eligible": 81,
        "no_dispatch": 39,
    }
    if args.mode == "contract":
        result = {
            "manifest": manifest,
            "counts": counts,
            "records": [],
            "provider_calls": 0,
            "cost_usd": "0",
            "human_persian_votes": 0,
            "selection": None,
        }
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    seed_public_context(oracle)
    if args.mode == "router":
        records = []
        for case in oracle["cases"]:
            _, observed = prepare_case(case)
            records.append(
                sanitized_record(
                    case["id"],
                    observed["model"],
                    {"router": score_router(case, observed)},
                )
            )
        result = {
            "manifest": manifest,
            "counts": counts,
            "records": records,
            "provider_calls": 0,
            "cost_usd": "0",
            "human_persian_votes": 0,
            "selection": None,
        }
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return int(any(not row["metric"]["router"]["passed"] for row in records))
    if transport is None:
        if not args.campaign_budget_usd or not args.campaign_ledger:
            print(json.dumps({"manifest": manifest, "status": "blocked_campaign_guard_required", "provider_calls": 0, "cost_usd": "0"}))
            return 4
        try:
            campaign = CampaignLedger(
                _safe_target(args.campaign_ledger),
                args.campaign_budget_usd,
                manifest,
            )
        except CampaignBudgetError as exc:
            print(json.dumps({"manifest": manifest, "status": "blocked_" + str(exc), "provider_calls": 0, "cost_usd": "0"}))
            return 4
        if not args.confirm_live:
            print(json.dumps({"manifest": manifest, "status": "blocked_confirmation_required", "provider_calls": 0, "cost_usd": "0"}))
            return 3
        key = _credential()
        if not key:
            print(json.dumps({"manifest": manifest, "status": "blocked_missing_private_credential", "provider_calls": 0, "cost_usd": "0"}))
            return 2
    else:
        key = "injected-test-credential"
        campaign = None
    target = _safe_target(args.output) if args.output else None
    prior = None
    records = []
    if target and target.is_file():
        prior = json.loads(target.read_text())
        assert_resume_compatible(prior, manifest, args.model)
        records = prior.get("records", [])
    done = {row["case_id"] for row in records}
    calls = 0
    campaign_failure = None
    for case in _selected(oracle, args.mode):
        if case["id"] in done:
            continue
        try:
            record, used_calls = _run_model_case(
                oracle,
                case,
                args.model,
                args.mode,
                transport,
                key,
                campaign=campaign,
                manifest=manifest,
            )
        except (CampaignBudgetError, quota.QuotaError) as exc:
            campaign_failure = getattr(exc, "code", str(exc))
            break
        records.append(record)
        calls += used_calls
        if target:
            partial = {"manifest": manifest, "counts": counts, "records": records, "provider_calls": calls, "cost_usd": str(sum((Decimal(row["cost"]) for row in records), Decimal("0"))), "human_persian_votes": 0, "selection": None}
            _write_atomic(target, partial)
    total_cost = sum((Decimal(row["cost"]) for row in records), Decimal("0"))
    result = {
        "manifest": manifest,
        "counts": counts,
        "records": records,
        "provider_calls": calls,
        "cost_usd": str(total_cost),
        "human_persian_votes": 0,
        "selection": None,
    }
    if campaign is not None:
        result["campaign"] = campaign.summary()
    if campaign_failure:
        result["status"] = "blocked_" + campaign_failure
    encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    if target:
        _write_atomic(target, result)
    print(encoded)
    return 4 if campaign_failure else 0


if __name__ == "__main__":
    sys.exit(main())
