#!/usr/bin/env python3
"""Execute one frozen D28 split against the real Django scorer and isolated PostgreSQL."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(os.environ.get("EVIDENCE_DIR", "/evidence"))
SPLIT = os.environ["D28_SPLIT"]
if SPLIT not in {"development", "held-out"}:
    raise SystemExit("D28_SPLIT must be development or held-out")

from django.contrib.auth import get_user_model
from django.core import signing
from django.utils import timezone

from apps.core import discovery
from apps.core.models import Opportunity, Review, Submission
from apps.workspace.models import Draft


def canonical_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_score(snapshot: dict, kind: str, route: str, criteria: dict, weights: dict) -> dict:
    """Contract oracle: independent arithmetic over the frozen basic axes; no product scorer import."""
    checks = []

    def numeric(value):
        return Decimal(value["value"]) if isinstance(value, dict) and value.get("status") == "known" else None

    def add(axis, state, reason):
        checks.append({"axis": axis, "state": state, "reason": reason})

    if "budget_max" in criteria or ("budget_min" in criteria and route == "buyer"):
        key = {"fund": "minimum_investment", "buyer": "price", "lessee": "deposit", "contractor": "working_capital_min"}.get(route, "min_capital")
        value = numeric(snapshot.get(key))
        ok = None if value is None else value <= Decimal(criteria.get("budget_max", value))
        if kind == "sale" or route == "buyer":
            ok = ok is not False and ("budget_min" not in criteria or value is not None and value >= Decimal(criteria["budget_min"])) if value is not None else None
        add("amount", "unknown" if ok is None else "met" if ok else "unmet", key)
    cat = "subtype" if criteria.get("subtype") else "group" if criteria.get("group") else None
    if cat:
        value = snapshot.get(cat)
        add("category", "unknown" if value in [None, "unknown", "not_applicable", ""] else "met" if value in criteria[cat] else "unmet", cat)
    loc = next((key for key in ("city", "county", "province") if criteria.get(key)), None)
    if loc:
        value = snapshot.get(loc)
        add("location", "unknown" if value in [None, "unknown", "not_applicable", ""] else "met" if value in criteria[loc] else "unmet", loc)
    if criteria.get("risk"):
        value = snapshot.get("risk")
        add("risk", "unknown" if value in [None, "unknown", "not_applicable", ""] else "met" if value in criteria["risk"] else "unmet", "risk")
    if criteria.get("return"):
        value = snapshot.get("irr" if kind == "project" else "forecast_irr" if snapshot.get("forecast_type") == "irr" else "forecast")
        rate = numeric(value)
        comparable = rate is not None and value.get("basis") == criteria["return"]["basis"]
        add("returns", "unknown" if not comparable else "met" if rate >= Decimal(criteria["return"]["minimum"]) else "unmet", "return")
    for key, wanted in criteria.get("conditions", {}).items():
        value = snapshot.get(key)
        state = "unknown" if value is None or value in ["unknown", "not_applicable"] else "met" if value in wanted else "unmet"
        add("conditions", state, key)
    counts = {axis: sum(item["axis"] == axis for item in checks) for axis in weights}
    for item in checks:
        item["weight"] = Decimal(weights[item["axis"]]) / Decimal(counts[item["axis"]])
    with localcontext() as context:
        context.prec = 60
        denominator = sum((item["weight"] for item in checks), Decimal(0))
        earned = sum((item["weight"] for item in checks if item["state"] == "met"), Decimal(0))
        known = sum((item["weight"] for item in checks if item["state"] != "unknown"), Decimal(0))
        score = 100 * earned / denominator if denominator else None
        coverage = 100 * known / denominator if denominator else None
    return {
        "score": str(score) if score is not None else None,
        "coverage": str(coverage) if coverage is not None else None,
        "status": "no_preferences" if not denominator else "insufficient_data" if not known else "ranked",
        "checks": [{**item, "weight": str(item["weight"])} for item in checks],
    }


def main() -> None:
    inputs_path = ROOT / "d28-inputs.json"
    freeze = json.loads((ROOT / "d28-input-freeze.json").read_text())
    actual_hash = canonical_hash(inputs_path)
    assert actual_hash == freeze["sha256"], "frozen input hash mismatch"
    payload = json.loads(inputs_path.read_text())
    weights = payload["weights"]
    User = get_user_model()
    owner = User.objects.create_user(mobile="+12025550991")
    admin = User.objects.create_user(mobile="+12025550992", role="admin")
    opportunity_rows = [row for row in payload["opportunities"] if row["split"] == SPLIT]
    for ordinal, row in enumerate(opportunity_rows):
        draft = Draft.objects.create(id=row["id"], creator=owner, kind=row["kind"], routes=[row["route"]], raw=row["snapshot"])
        op = Opportunity.objects.create(id=row["id"], draft=draft, synthetic=True)
        revision = Submission.objects.create(
            id=row["revision_id"], opportunity=op, draft_version=1, kind=row["kind"], routes=[row["route"]], snapshot=row["snapshot"], submitted_by=owner
        )
        op.public_revision = revision
        op.save(update_fields=["public_revision"])
        Review.objects.create(submission=revision, actor=admin, decision="approved", reason="شاهد مصنوعی", created_at=timezone.now(), public_files=[])
    results = []
    mismatches = []
    scenarios = [row for row in payload["scenarios"] if row["split"] == SPLIT]
    for scenario in scenarios:
        first = discovery.listing(dict(scenario["criteria"]))
        second = discovery.listing(dict(scenario["criteria"]))
        items = first["items"]
        assert first["total"] == 6 and len(items) == 6
        assert [item["id"] for item in items] == [item["id"] for item in second["items"]]
        comparisons = []
        for item in items:
            source = next(row for row in opportunity_rows if row["id"] == item["id"])
            expected = independent_score(source["snapshot"], source["kind"], source["route"], scenario["criteria"], weights)
            actual = item["matching"]
            ok = all(actual[key] == expected[key] for key in ("score", "coverage", "status"))
            comparisons.append({"opportunity_id": item["id"], "expected": expected, "actual": actual, "pass": ok})
            if not ok:
                mismatches.append({"scenario": scenario["id"], "opportunity": item["id"]})
        results.append({
            "scenario_id": scenario["id"], "route": scenario["route"], "axis_family": scenario["axis_family"],
            "candidate_count": first["total"], "top5_ids": [item["id"] for item in items[:5]],
            "stable_order": True, "oracle": comparisons,
        })
    global_first = discovery.listing({})
    assert global_first["total"] == 48 and len(global_first["items"]) == 12 and global_first["next"]
    global_second = discovery.listing({}, cursor=global_first["next"])
    assert not set(item["id"] for item in global_first["items"]) & set(item["id"] for item in global_second["items"])
    output = {
        "schema": "invest.d28.technical-results@1", "split": SPLIT, "input_sha256": actual_hash,
        "policy_version": discovery.POLICY, "runtime_source": os.environ.get("RUNTIME_SOURCE", "unknown"),
        "counts": {"scenarios": len(scenarios), "opportunities": len(opportunity_rows), "candidate_pairs": sum(row["candidate_count"] for row in results), "top5_pairs": sum(len(row["top5_ids"]) for row in results), "oracle_mismatches": len(mismatches)},
        "cursor_control": {"total": global_first["total"], "page1": len(global_first["items"]), "page2": len(global_second["items"]), "overlap": 0},
        "human_labels_generated": False, "mismatches": mismatches, "results": results,
    }
    output_path = ROOT / f"d28-{SPLIT}-results.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output["counts"], ensure_ascii=False))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
