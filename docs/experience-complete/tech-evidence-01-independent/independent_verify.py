#!/usr/bin/env python3
"""Independent structural/oracle verifier; imports no invest product scoring code."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal, localcontext
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "docs/experience-complete/tech-evidence-01"
HERE = Path(__file__).resolve().parent
EXPECTED_ROUTES = {
    "investor", "fund", "buyer", "lessee", "contractor", "operator", "heritage", "charity"
}
PRODUCT_BASELINE = "79519bb8e88cbf6c0bcf7614c63b3737cc668a70"
WEIGHTS = {"amount": 30, "category": 20, "location": 15, "returns": 20, "risk": 15, "conditions": 15}
UNKNOWN = (None, "unknown", "not_applicable", "")


def load(name: str):
    return json.loads((SOURCE / name).read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric(value):
    if isinstance(value, dict) and value.get("status") == "known":
        raw = value.get("source_value", value.get("value"))
        return Decimal(raw)
    return None


def calculate(snapshot: dict, kind: str, route: str, criteria: dict) -> dict:
    checks = []

    def add(axis: str, state: str):
        checks.append({"axis": axis, "state": state})

    if "budget_max" in criteria or ("budget_min" in criteria and route == "buyer"):
        key = {
            "fund": "minimum_investment",
            "buyer": "price",
            "lessee": "deposit",
            "contractor": "working_capital_min",
        }.get(route, "min_capital")
        value = numeric(snapshot.get(key))
        if value is None:
            state = "unknown"
        else:
            met = ("budget_max" not in criteria or value <= Decimal(criteria["budget_max"]))
            if kind == "sale" or route == "buyer":
                met = met and ("budget_min" not in criteria or value >= Decimal(criteria["budget_min"]))
            state = "met" if met else "unmet"
        add("amount", state)
    category = "subtype" if criteria.get("subtype") else "group" if criteria.get("group") else None
    if category:
        value = snapshot.get(category)
        add("category", "unknown" if value in UNKNOWN else "met" if value in criteria[category] else "unmet")
    location = next((key for key in ("city", "county", "province") if criteria.get(key)), None)
    if location:
        value = snapshot.get(location)
        add("location", "unknown" if value in UNKNOWN else "met" if value in criteria[location] else "unmet")
    if criteria.get("risk"):
        value = snapshot.get("risk")
        add("risk", "unknown" if value in UNKNOWN else "met" if value in criteria["risk"] else "unmet")
    if criteria.get("return"):
        if kind == "project":
            key = "irr"
        elif snapshot.get("forecast_type") in ("irr", "simple_rate", "effective_rate"):
            key = "forecast_" + snapshot["forecast_type"]
        else:
            key = "forecast"
        value = snapshot.get(key)
        rate = numeric(value)
        comparable = rate is not None and value.get("basis") == criteria["return"]["basis"]
        add("returns", "unknown" if not comparable else "met" if rate >= Decimal(criteria["return"]["minimum"]) else "unmet")
    for key, wanted in criteria.get("conditions", {}).items():
        value = snapshot.get(key)
        if value is None or (isinstance(value, str) and value in ("unknown", "not_applicable")):
            state = "unknown"
        elif isinstance(value, list):
            state = "met" if any(item in wanted for item in value) else "unmet"
        else:
            state = "met" if value in wanted else "unmet"
        if key.startswith("bank_"):
            state = "unknown"
        add("conditions", state)
    counts = Counter(check["axis"] for check in checks)
    for check in checks:
        check["weight"] = Decimal(WEIGHTS[check["axis"]]) / Decimal(counts[check["axis"]])
    with localcontext() as context:
        context.prec = 60
        denominator = sum((check["weight"] for check in checks), Decimal(0))
        earned = sum((check["weight"] for check in checks if check["state"] == "met"), Decimal(0))
        known = sum((check["weight"] for check in checks if check["state"] != "unknown"), Decimal(0))
        score = 100 * earned / denominator if denominator else None
        coverage = 100 * known / denominator if denominator else None
    return {
        "score": str(score) if score is not None else None,
        "coverage": str(coverage) if coverage is not None else None,
        "status": "no_preferences" if not denominator else "insufficient_data" if not known else "ranked",
        "checks": [{**check, "weight": str(check["weight"])} for check in checks],
    }


def same_decimal(left, right) -> bool:
    if left is None or right is None:
        return left is right
    return Decimal(left) == Decimal(right)


def compare_results(inputs: dict, outputs: dict) -> list[dict]:
    opportunities = {row["id"]: row for row in inputs["opportunities"]}
    scenarios = {row["id"]: row for row in inputs["scenarios"]}
    mismatches = []
    for split, output in outputs.items():
        for result in output["results"]:
            scenario = scenarios[result["scenario_id"]]
            expected_rows = []
            for pair in result["oracle"]:
                opportunity = opportunities[pair["opportunity_id"]]
                expected = calculate(opportunity["snapshot"], opportunity["kind"], opportunity["route"], scenario["criteria"])
                actual = pair["actual"]
                expected_checks = [(c["axis"], c["state"], Decimal(c["weight"])) for c in expected["checks"]]
                actual_checks = [(c["axis"], c["state"], Decimal(c["weight"])) for c in actual["checks"]]
                ok = (
                    same_decimal(expected["score"], actual["score"])
                    and same_decimal(expected["coverage"], actual["coverage"])
                    and expected["status"] == actual["status"]
                    and expected_checks == actual_checks
                )
                if not ok:
                    mismatches.append({"split": split, "scenario": scenario["id"], "opportunity": opportunity["id"]})
                expected_rows.append((opportunity, expected))
            expected_order = sorted(
                expected_rows,
                key=lambda item: (
                    -(Decimal(item[1]["score"]) if item[1]["score"] is not None else Decimal(0)),
                    -(Decimal(item[1]["coverage"]) if item[1]["coverage"] is not None else Decimal(0)),
                    -item[0]["index"],
                    item[0]["id"],
                ),
            )
            if result["top5_ids"] != [item[0]["id"] for item in expected_order[:5]]:
                mismatches.append({"split": split, "scenario": scenario["id"], "kind": "top5-order"})
    return mismatches


def compare_replay(inputs: dict, replay: dict) -> list[dict]:
    """Compare the independently executed development replay with this verifier's oracle."""
    opportunities = {row["id"]: row for row in inputs["opportunities"]}
    scenarios = {row["id"]: row for row in inputs["scenarios"]}
    mismatches = []
    for result in replay["results"]:
        scenario = scenarios[result["scenario_id"]]
        expected_rows = []
        for pair in result["actual"]:
            opportunity = opportunities[pair["opportunity_id"]]
            expected = calculate(opportunity["snapshot"], opportunity["kind"], opportunity["route"], scenario["criteria"])
            actual = pair["matching"]
            expected_checks = [(c["axis"], c["state"], Decimal(c["weight"])) for c in expected["checks"]]
            actual_checks = [(c["axis"], c["state"], Decimal(c["weight"])) for c in actual["checks"]]
            if not (
                same_decimal(expected["score"], actual["score"])
                and same_decimal(expected["coverage"], actual["coverage"])
                and expected["status"] == actual["status"]
                and expected_checks == actual_checks
            ):
                mismatches.append({"scenario": scenario["id"], "opportunity": opportunity["id"]})
            expected_rows.append((opportunity, expected))
        expected_order = sorted(
            expected_rows,
            key=lambda item: (
                -(Decimal(item[1]["score"]) if item[1]["score"] is not None else Decimal(0)),
                -(Decimal(item[1]["coverage"]) if item[1]["coverage"] is not None else Decimal(0)),
                -item[0]["index"],
                item[0]["id"],
            ),
        )
        if result["top5_ids"] != [item[0]["id"] for item in expected_order[:5]]:
            mismatches.append({"scenario": scenario["id"], "kind": "top5-order"})
    return mismatches


def main() -> None:
    checks = {}
    findings = []
    manifest = load("manifest.json")
    manifest_mismatches = []
    for entry in manifest["files"]:
        path = SOURCE / entry["path"]
        if not path.exists() or path.stat().st_size != entry["bytes"] or sha(path) != entry["sha256"]:
            manifest_mismatches.append(entry["path"])
    checks["manifest_83_hashes"] = not manifest_mismatches and len(manifest["files"]) == 83

    inputs = load("d28-inputs.json")
    freeze = load("d28-input-freeze.json")
    checks["input_freeze"] = sha(SOURCE / "d28-inputs.json") == freeze["sha256"] == manifest["input_sha256"]

    attempt_hashes = []
    for attempt in (1, 2, 3):
        attempt_freeze = load(f"attempt-{attempt}-input-freeze.json")
        attempt_hashes.append(sha(SOURCE / f"attempt-{attempt}-inputs.json"))
        checks[f"attempt_{attempt}_freeze"] = attempt_hashes[-1] == attempt_freeze["sha256"]
    replay_log = load("leak-replay-log.json")
    logged_hashes = [event["input_sha256"] for event in replay_log["events"]]
    first_failure = load("heldout-first-attempt.json")
    checks["heldout_history_preserved"] = (
        logged_hashes == [attempt_hashes[0], attempt_hashes[0], attempt_hashes[1], attempt_hashes[2], freeze["sha256"]]
        and first_failure["input_sha256"] == attempt_hashes[0]
        and first_failure["result"] == "fixture-contract-failure"
        and first_failure["field"] == "return.basis"
        and first_failure["product_scoring_reached"] is False
        and replay_log["absolute_blinding_claimed"] is False
    )
    routes = set(inputs["routes"])
    checks["eight_routes"] = routes == EXPECTED_ROUTES
    opportunities = inputs["opportunities"]
    scenarios = inputs["scenarios"]
    checks["fixture_is_synthetic"] = all(row.get("synthetic") is True and row.get("market_claim") is False for row in opportunities)
    checks["80_scenarios_96_ids"] = len(scenarios) == len({r["id"] for r in scenarios}) == 80 and len(opportunities) == len({r["id"] for r in opportunities}) == 96
    checks["split_denominators"] = Counter(r["split"] for r in scenarios) == {"development": 32, "held-out": 48} and Counter(r["split"] for r in opportunities) == {"development": 48, "held-out": 48}
    checks["six_candidates"] = all(len(row["candidate_pool"]) == len(set(row["candidate_pool"])) == 6 for row in scenarios)
    opportunity_ids = {row["id"] for row in opportunities}
    checks["candidate_binding"] = all(set(row["candidate_pool"]) <= opportunity_ids for row in scenarios)

    semantic_signatures = []
    duplicate_pairs = []
    by_route_split = defaultdict(dict)
    for row in opportunities:
        effective = {key: value for key, value in row["snapshot"].items() if key != "title"}
        semantic_signatures.append((row["route"], json.dumps(effective, ensure_ascii=False, sort_keys=True)))
        by_route_split[(row["route"], row["index"])][row["split"]] = effective
    for key, split_rows in by_route_split.items():
        if set(split_rows) == {"development", "held-out"} and split_rows["development"] == split_rows["held-out"]:
            duplicate_pairs.append({"route": key[0], "index": key[1]})
    checks["96_semantically_distinct_opportunities"] = len(set(semantic_signatures)) == 96
    if duplicate_pairs:
        findings.append({"id": "EVID-IT-001", "severity": "high", "summary": f"{len(duplicate_pairs) * 2} opportunities collapse into {len(duplicate_pairs)} cross-split duplicate pairs after non-scoring title/IDs are removed."})

    outputs = {split: load(f"d28-{split}-results.json") for split in ("development", "held-out")}
    checks["candidate_top5_denominators"] = outputs["development"]["counts"]["candidate_pairs"] == 192 and outputs["development"]["counts"]["top5_pairs"] == 160 and outputs["held-out"]["counts"]["candidate_pairs"] == 288 and outputs["held-out"]["counts"]["top5_pairs"] == 240
    oracle_mismatches = compare_results(inputs, outputs)
    checks["independent_oracle_all_480_pairs"] = not oracle_mismatches

    mutation = copy.deepcopy(outputs)
    mutation["development"]["results"][0]["oracle"][0]["actual"]["score"] = "99.999"
    mutation_rejected = bool(compare_results(inputs, mutation))
    checks["verifier_rejects_score_mutation"] = mutation_rejected

    replay = json.loads((HERE / "development-replay-results.json").read_text())
    replay_mismatches = compare_replay(inputs, replay)
    checks["fresh_postgresql_development_replay"] = (
        replay["runtime_commit"] == PRODUCT_BASELINE
        and
        replay["counts"] == {"scenarios": 32, "opportunities": 48, "candidate_pairs": 192, "top5_pairs": 160}
        and replay["cursor"] == {"pages": [12, 12, 12, 12], "total_ids": 48, "unique_ids": 48}
        and not replay_mismatches
    )

    route_axis = list(csv.DictReader((SOURCE / "d28-route-axis-coverage.csv").open()))
    checks["route_axis_64"] = len(route_axis) == 64 and len({(r["route"], r["axis"]) for r in route_axis}) == 64
    scenario_index = {r["id"]: r for r in scenarios}
    weak_unit_basis = []
    for row in route_axis:
        if row["axis"] != "unit-basis" or row["applicable"] != "yes":
            continue
        linked = [scenario_index[sid] for sid in row["scenario_ids"].split(";")]
        numeric_axis = any("budget_max" in s["criteria"] or "budget_min" in s["criteria"] or "return" in s["criteria"] for s in linked)
        if not numeric_axis:
            weak_unit_basis.append(row["route"])
    checks["unit_basis_rows_have_numeric_consumer"] = not weak_unit_basis
    if weak_unit_basis:
        findings.append({"id": "EVID-IT-002", "severity": "medium", "summary": "unit-basis coverage is claimed without a numeric/return criterion for: " + ", ".join(weak_unit_basis)})

    form_counts = {}
    for name, human_fields in {
        "d28-relevance-labels.csv": ("relevance_label", "independent_group_rank", "reason", "evidence_fields", "missing_information", "reviewer", "reviewed_at"),
        "d28-critical-review.csv": ("critical_misleading", "missing_important_disclosure", "reason", "evidence_fields", "reviewer", "reviewed_at"),
    }.items():
        rows = list(csv.DictReader((SOURCE / name).open()))
        form_counts[name] = len(rows)
        checks[name + "_400_unique_blank"] = len(rows) == 400 and len({(r["scenario_id"], r["opportunity_id"]) for r in rows}) == 400 and all(not r[field] for r in rows for field in human_fields)
    reviewer_text = (SOURCE / "d28-reviewer-inputs.json").read_text()
    checks["reviewer_has_no_system_fields"] = not any(f'"{key}"' in reviewer_text for key in ("score", "coverage", "matching", "system_rank"))

    design = list(csv.DictReader((SOURCE / "design-slot-matrix.csv").open()))
    checks["design_26x4"] = len(design) == 104 and len({r["row_id"] for r in design}) == 26 and Counter(int(r["viewport_width"]) for r in design) == {360: 26, 390: 26, 768: 26, 1440: 26}
    checks["design_classification_total"] = Counter(r["classification"] for r in design) == {"reuse-valid": 49, "representative-covered": 15, "reference-component-only": 36, "capture-needed→new-evidence": 4}
    checks["design_metadata_and_paths"] = all(r["viewport_height"] and r["canvas"] and r["font"] == "document.fonts.ready" and r["motion"] == "reduced" and r["identity"] and r["synthetic_data"] and r["state"] and (ROOT / r["product_evidence"]).exists() and (not r["reference_evidence"] or (ROOT / r["reference_evidence"]).exists()) for r in design)
    checks["design_votes_blank"] = all(not r["human_verdict"] and not r["specialist_design_approval"] for r in design)
    checks["reference_component_only_not_full_pair"] = all(not r["reference_evidence"] or "component" in r["proof_or_limitation"].lower() or "full" in r["proof_or_limitation"].lower() or "صفحه" in r["proof_or_limitation"] for r in design if r["classification"] == "reference-component-only")

    wrong_state_representatives = [
        {"row_id": row["row_id"], "width": int(row["viewport_width"]), "route": row["route"], "state": row["state"], "evidence": row["product_evidence"]}
        for row in design
        if row["classification"] == "representative-covered"
        and "product-land-stage2-" in row["product_evidence"]
        and row["route"] != "/tools/land-preparation"
    ]
    checks["representative_same_route_and_state"] = not wrong_state_representatives
    if wrong_state_representatives:
        findings.append({"id": "EVID-IT-003", "severity": "high", "summary": f"{len(wrong_state_representatives)} representative slots use land-preparation step-2 captures for a different route/state."})

    fresh_design = [row for row in design if row["classification"] == "capture-needed→new-evidence"]
    evidence_metadata = json.dumps(manifest, ensure_ascii=False).lower()
    runtime_digest_recorded = "image_digest" in evidence_metadata or "runtime_digest" in evidence_metadata
    checks["fresh_capture_runtime_digest_recorded"] = len(fresh_design) == 4 and runtime_digest_recorded
    if fresh_design and not runtime_digest_recorded:
        findings.append({"id": "EVID-IT-004", "severity": "medium", "summary": "Fresh captures name a product commit but record no runtime image/source digest that independently binds the captured server to that commit."})

    browser_rows = [json.loads((HERE / f"browser-interaction-{width}.json").read_text()) for width in (360, 390, 768, 1440)]
    checks["independent_browser_library_four_widths"] = all(
        row["width"] == width and row["focus"] and row["hit"] and not row["overflow"]
        and row["accordionClick"] and row["expandedBefore"] != row["expandedAfter"]
        and row["fonts"] == "document.fonts.ready" and row["motion"] == "reduce"
        for width, row in zip((360, 390, 768, 1440), browser_rows)
    )

    result = {
        "schema": "invest.tech-evidence.independent-verification@1",
        "checks": checks,
        "passed": sum(checks.values()),
        "failed": [key for key, value in checks.items() if not value],
        "findings": findings,
        "details": {
            "manifest_mismatches": manifest_mismatches,
            "semantic_opportunity_signatures": len(set(semantic_signatures)),
            "cross_split_duplicate_pairs": duplicate_pairs,
            "oracle_mismatches": oracle_mismatches,
            "mutation_rejected": mutation_rejected,
            "development_replay_mismatches": replay_mismatches,
            "weak_unit_basis_routes": weak_unit_basis,
            "form_counts": form_counts,
            "attempt_hashes": attempt_hashes,
            "wrong_state_representatives": wrong_state_representatives,
            "fresh_design_slots": [{"row_id": row["row_id"], "width": row["viewport_width"], "path": row["product_evidence"]} for row in fresh_design],
        },
    }
    (HERE / "independent-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    if oracle_mismatches or not mutation_rejected or manifest_mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
