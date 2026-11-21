"""Locked-oracle loading, isolated seeding and content-free in-memory scoring."""

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone

ORACLE_SHA256 = "1cfe6230d7f5730ccbe4b11832ca81a893c2882e697cd3323b6abdd624fa2691"
HELD_OUT_SHA256 = "f9b95745736ba2529379ce97550b590cbe913222087046241151268c2cfeadda"
CONTEXT_SHA256 = "27e31b534223af6547a7dce41a9b24af626b0055671f5da946b45b08398841aa"
MODEL_EXTRACTION_VERSION = "assistant-model-extraction-v1"
THRESHOLDS = {"extraction": 0.95, "citation": 0.98, "persian": 0.90}
PERSISTED_RECORD_KEYS = {
    "case_id", "model", "metric", "token", "cost", "failure_code"
}


@dataclass(frozen=True)
class Assessment:
    eligible: bool
    recommendation: str | None
    reasons: list[str]


def assess(sol, luna):
    reasons = []
    for name, result in (("sol", sol), ("luna", luna)):
        if result.get("critical", 0):
            reasons.append(f"{name}:critical")
        for metric, threshold in THRESHOLDS.items():
            value = result.get("overall", {}).get(metric)
            if value is None or value < threshold:
                reasons.append(f"{name}:{metric}")
        if not result.get("human_persian_complete"):
            reasons.append(f"{name}:human-persian-open")
    for family, sol_metrics in sol.get("families", {}).items():
        luna_metrics = luna.get("families", {}).get(family, {})
        for metric, sol_value in sol_metrics.items():
            luna_value = luna_metrics.get(metric)
            if luna_value is None:
                reasons.append(f"luna:{family}:{metric}:missing")
            elif sol_value - luna_value > 0.05:
                reasons.append(f"luna:{family}:{metric}:degradation")
    if reasons:
        return Assessment(False, None, reasons)
    return Assessment(True, "gpt-6-luna", [])


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def load_oracle(path):
    path = Path(path)
    raw = path.read_bytes()
    if sha256_bytes(raw) != ORACLE_SHA256:
        raise ValueError("oracle_hash_mismatch")
    value = json.loads(raw)
    cases = value.get("cases") or []
    if (
        value.get("schema_version") != "invest-s09-eval-oracle-v1"
        or len(cases) != 120
        or len({case.get("id") for case in cases}) != 120
        or sum(case.get("split") == "development" for case in cases) != 40
        or sum(case.get("split") == "held-out" for case in cases) != 80
    ):
        raise ValueError("oracle_contract_mismatch")
    held_out = [case for case in cases if case["split"] == "held-out"]
    if sha256_bytes(canonical(held_out).encode()) != HELD_OUT_SHA256:
        raise ValueError("held_out_hash_mismatch")
    if sha256_bytes(canonical(value["public_context"]).encode()) != CONTEXT_SHA256:
        raise ValueError("context_hash_mismatch")
    return value


def context_hash(oracle):
    return sha256_bytes(canonical(oracle["public_context"]).encode())


def held_out_hash(oracle):
    frozen = [case for case in oracle["cases"] if case["split"] == "held-out"]
    return sha256_bytes(canonical(frozen).encode())


_INVALID = object()


def _parse_json(value):
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return _INVALID


def _model_fields(output):
    proposed = output.get("model_proposed_criteria") if isinstance(output, dict) else None
    if not isinstance(proposed, dict) or proposed.get("version") != MODEL_EXTRACTION_VERSION:
        return None
    result = {}
    for row in proposed.get("fields", []):
        if not isinstance(row, dict) or row.get("field") in result:
            return None
        value = _parse_json(row.get("value_json"))
        basis = _parse_json(row.get("basis_json"))
        if value is _INVALID or basis is _INVALID:
            return None
        result[row.get("field")] = {
            "status": row.get("status"),
            "value": value,
            "unit": row.get("unit"),
            "basis": basis,
        }
    return result


def _same_value(actual, expected):
    if isinstance(expected, list):
        return isinstance(actual, list) and {canonical(v) for v in actual} == {
            canonical(v) for v in expected
        }
    return actual == expected


def score_extraction(case, output, failure_code=None):
    if not case["expected"]["applicability"]["extraction"]["applicable"]:
        return {"applicable": False, "numerator": 0, "denominator": 0, "passed": None}
    if failure_code:
        return {"applicable": True, "numerator": 0, "denominator": 1, "passed": False}
    fields = _model_fields(output)
    expected = case["expected"]["criteria"]
    clarification = case["expected"]["clarification"]
    proposed = output.get("model_proposed_criteria", {}) if isinstance(output, dict) else {}
    ok = fields is not None
    if ok:
        alternatives = [expected["exact"], *expected.get("allowed_alternatives", [])]
        ok = any(
            set(fields) == set(candidate) | set(expected.get("unknown", []))
            and all(
                fields[name].get("status") == wanted.get("status")
                and _same_value(fields[name].get("value"), wanted.get("value"))
                and fields[name].get("unit") == wanted.get("unit")
                and fields[name].get("basis") == wanted.get("basis")
                for name, wanted in candidate.items()
            )
            for candidate in alternatives
        )
    if ok:
        ok = all(name not in fields for name in expected.get("absent", []))
        ok = ok and all(
            name in fields and fields[name]["status"] == "unknown" and fields[name]["value"] is None
            for name in expected.get("unknown", [])
        )
    if ok:
        needed = clarification["status"] == "required"
        forbidden = clarification["status"] == "forbidden"
        proposed_flag = proposed.get("needs_clarification")
        proposed_fields = set(proposed.get("clarification_fields") or [])
        ok = (not needed or proposed_flag is True) and (not forbidden or proposed_flag is False)
        ok = ok and set(clarification.get("fields") or []).issubset(proposed_fields)
    return {"applicable": True, "numerator": int(ok), "denominator": 1, "passed": ok}


def _context_value(oracle, opportunity_id, field):
    item = oracle["public_context"]["opportunities"].get(opportunity_id)
    if not item:
        return _INVALID
    path = oracle["public_context"].get("field_aliases", {}).get(field, field).split(".")
    value = item
    for part in path:
        if not isinstance(value, dict) or part not in value:
            return _INVALID
        value = value[part]
    return value


def _citation_tuple(row):
    return (row.get("id"), row.get("revision"), row.get("field"))


def score_citations(oracle, case, output, failure_code=None):
    contract = case["expected"]["citations"]
    applicable = case["expected"]["applicability"]["citation"]["applicable"]
    rows = output.get("citations", []) if isinstance(output, dict) else []
    if not isinstance(rows, list):
        rows = []
    unique = {}
    duplicates = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _citation_tuple(row)
        duplicates += int(key in unique)
        unique.setdefault(key, row)
    required = {
        (row["opportunity_id"], row["revision"], row["field"])
        for row in contract.get("required", [])
    }
    allowed = {
        (row["opportunity_id"], row["revision"], row["field"])
        for row in contract.get("allowed", [])
    }
    valid = set()
    invalid = set()
    for key, row in unique.items():
        value = _context_value(oracle, key[0], key[2])
        claimed = _parse_json(row.get("value_json"))
        item = oracle["public_context"]["opportunities"].get(key[0])
        exact_revision = isinstance(item, dict) and item["public_revision_id"] == key[1]
        if key in required | allowed and exact_revision and value is not _INVALID and claimed == value:
            valid.add(key)
        else:
            invalid.add(key)
    answer = output.get("answer", "") if isinstance(output, dict) else ""
    normalized = str(answer).translate(
        str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    )
    context_text = canonical(oracle["public_context"])
    ungrounded_numbers = [
        number
        for number in re.findall(r"(?<![\w-])\d+(?:[./]\d+)?", normalized)
        if number not in {"2", "3", "4", "100"}
        and number.replace("/", ".") not in context_text
    ]
    guard = not invalid and not ungrounded_numbers
    if not applicable:
        return {
            "applicable": False,
            "numerator": 0,
            "denominator": 0,
            "guard": guard and not rows,
            "duplicates": duplicates,
            "passed": None,
        }
    extras = set(unique) - required
    denominator = len(required) + len(extras)
    numerator = len(required & valid) + len(extras & valid)
    if failure_code:
        numerator = 0
    return {
        "applicable": True,
        "numerator": numerator,
        "denominator": denominator,
        "guard": guard,
        "duplicates": duplicates,
        "passed": numerator == denominator and guard,
    }


def score_router(case, observed):
    expected = case["expected"]["router"]
    ok = (
        isinstance(observed, dict)
        and observed.get("route") == expected["route"]
        and observed.get("reason") in expected["allowed_reason_codes"]
        and observed.get("model") == expected["model"]
    )
    return {"applicable": True, "numerator": int(ok), "denominator": 1, "passed": ok}


def sanitized_record(case_id, model, metrics, usage=None, cost="0", failure_code=None):
    usage = usage or {}
    record = {
        "case_id": case_id,
        "model": model,
        "metric": metrics,
        "token": {
            "input": int(usage.get("input_tokens", 0)),
            "output": int(usage.get("output_tokens", 0)),
        },
        "cost": str(cost),
        "failure_code": failure_code,
    }
    if set(record) != PERSISTED_RECORD_KEYS:
        raise ValueError("persisted_record_allowlist_mismatch")
    return record


def seed_public_context(oracle):
    """Seed the frozen public context one-to-one into a test-only PostgreSQL database."""
    if settings.INVEST_ENV != "test":
        raise RuntimeError("evaluation_seed_forbidden_outside_test")
    from apps.core.models import Opportunity, Review, Submission
    from apps.identity.models import User
    from apps.workspace.models import Draft

    owner, _ = User.objects.get_or_create(
        id=uuid.UUID("40000000-0000-4000-8000-000000000001"),
        defaults={"mobile": "+12025557001", "role": "owner"},
    )
    reviewer, _ = User.objects.get_or_create(
        id=uuid.UUID("40000000-0000-4000-8000-000000000002"),
        defaults={"mobile": "+12025557002", "role": "admin"},
    )
    seeded = []
    for index, item in enumerate(oracle["public_context"]["opportunities"].values(), 1):
        draft_id = uuid.UUID(f"30000000-0000-4000-8000-{index:012d}")
        routes = [item["route"]]
        snapshot = {
            "title": item["title"],
            "amount": item["amount"],
            "return": item["return"],
            "risk": item["risk"],
            "location": item["location"],
        }
        if item["kind"] == "project":
            snapshot["min_capital"] = item["amount"]
        elif item["kind"] == "fund":
            snapshot["minimum_investment"] = item["amount"]
        else:
            snapshot["price"] = item["amount"]
            snapshot["price_mode"] = "total"
        draft, _ = Draft.objects.update_or_create(
            id=draft_id,
            defaults={
                "creator": owner,
                "kind": item["kind"],
                "routes": routes,
                "raw": snapshot,
                "version": 1,
            },
        )
        opportunity, _ = Opportunity.objects.update_or_create(
            id=uuid.UUID(item["id"]),
            defaults={
                "draft": draft,
                "availability": "active"
                if item["publication_state"] == "published"
                else "owner_paused",
                "synthetic": True,
            },
        )
        submission, created = Submission.objects.get_or_create(
            id=uuid.UUID(item["public_revision_id"]),
            defaults={
                "opportunity": opportunity,
                "draft_version": 1,
                "kind": item["kind"],
                "routes": routes,
                "snapshot": snapshot,
                "files": [],
                "submitted_by": owner,
            },
        )
        if not created and (
            submission.opportunity_id != opportunity.pk
            or submission.draft_version != 1
            or submission.kind != item["kind"]
            or submission.routes != routes
            or submission.snapshot != snapshot
            or submission.files != []
            or submission.submitted_by_id != owner.pk
        ):
            raise RuntimeError("evaluation_seed_revision_mismatch")
        published_at = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
        review, _ = Review.objects.get_or_create(
            submission=submission,
            actor=reviewer,
            decision="approved",
            defaults={
                "reason": "synthetic-evaluation-context",
                "public_files": [],
                "created_at": published_at,
            },
        )
        if opportunity.public_revision_id != submission.pk:
            opportunity.public_revision = submission
            opportunity.save(update_fields=["public_revision"])
        seeded.append(str(opportunity.pk))
    if set(seeded) != set(oracle["public_context"]["opportunities"]):
        raise RuntimeError("evaluation_seed_mismatch")
    return seeded


def version_manifest(oracle, *, commit, mode, versions, timestamp=None):
    return {
        "commit": commit,
        "oracle_sha256": ORACLE_SHA256,
        "held_out_sha256": held_out_hash(oracle),
        "context_sha256": context_hash(oracle),
        "product_prompt_tool_schema_router_versions": versions,
        "mode": mode,
        "timestamp": timestamp or timezone.now().isoformat(),
    }


def assert_resume_compatible(prior, current, model):
    for key in (
        "oracle_sha256",
        "held_out_sha256",
        "context_sha256",
        "product_prompt_tool_schema_router_versions",
        "mode",
    ):
        if prior.get("manifest", {}).get(key) != current.get(key):
            raise ValueError("resume_manifest_mismatch:" + key)
    models = {row.get("model") for row in prior.get("records", [])}
    if models and models != {model}:
        raise ValueError("resume_model_mismatch")
