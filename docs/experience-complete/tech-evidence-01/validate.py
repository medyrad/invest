#!/usr/bin/env python3
"""Validate denominators, independence boundaries, links and blank human gates."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name: str):
    return json.loads((HERE / name).read_text())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    checks = {}
    payload = load("d28-inputs.json")
    freeze = load("d28-input-freeze.json")
    checks["input_hash"] = digest(HERE / "d28-inputs.json") == freeze["sha256"]
    opportunities = payload["opportunities"]
    scenarios = payload["scenarios"]
    checks["d28_denominator"] = len(opportunities) == 96 and len({row["id"] for row in opportunities}) == 96 and len(scenarios) == 80 and len({row["id"] for row in scenarios}) == 80
    checks["route_counts"] = all(sum(row["route"] == route for row in opportunities) == 12 and sum(row["route"] == route for row in scenarios) == 10 for route in payload["routes"])
    checks["split_counts"] = sum(row["split"] == "development" for row in scenarios) == 32 and sum(row["split"] == "held-out" for row in scenarios) == 48 and all(sum(row["route"] == route and row["split"] == split for row in opportunities) == 6 for route in payload["routes"] for split in ("development", "held-out"))
    signatures = {(row["route"], row["split"], json.dumps(row["snapshot"], sort_keys=True, ensure_ascii=False)) for row in opportunities}
    checks["genuine_pool_difference"] = len(signatures) == 96
    checks["explicit_units"] = all(any(isinstance(value, dict) and value.get("unit", {}).get("code") == "TOMAN" for value in row["snapshot"].values()) for row in opportunities)
    checks["human_fields_absent_from_inputs"] = all(row["pre_result_human_label"] is None and row["critical_misleading"] is None and row["expected_human_rank"] is None for row in scenarios)

    outputs = {split: load(f"d28-{split}-results.json") for split in ("development", "held-out")}
    checks["result_hash_binding"] = all(result["input_sha256"] == freeze["sha256"] for result in outputs.values())
    checks["oracle_zero_mismatch"] = all(result["counts"]["oracle_mismatches"] == 0 for result in outputs.values())
    checks["candidate_and_top5_denominators"] = outputs["development"]["counts"]["candidate_pairs"] == 192 and outputs["development"]["counts"]["top5_pairs"] == 160 and outputs["held-out"]["counts"]["candidate_pairs"] == 288 and outputs["held-out"]["counts"]["top5_pairs"] == 240
    checks["cursor_no_overlap"] = all(result["cursor_control"] == {"total": 48, "page1": 12, "page2": 12, "overlap": 0} for result in outputs.values())
    rows = [row for result in outputs.values() for row in result["results"]]
    checks["competition_real_top5"] = all(row["candidate_count"] == 6 and len(row["top5_ids"]) == 5 for row in rows)
    checks["stable_order"] = all(row["stable_order"] for row in rows)
    checks["no_preference_null"] = all(all(pair["actual"]["score"] is None and pair["actual"]["coverage"] is None for pair in row["oracle"]) for row in rows if row["axis_family"] == "no-preference-control")
    checks["all_unknown_zero"] = all(all(pair["actual"]["score"] == "0" and pair["actual"]["coverage"] == "0" and pair["actual"]["status"] == "insufficient_data" for pair in row["oracle"]) for row in rows if row["axis_family"] == "all-unknown-control")
    checks["warnings_and_weights"] = all(all(sum(float(check["weight"]) for check in pair["actual"]["checks"] if check["axis"] == "conditions") <= 15.0000001 for pair in row["oracle"]) for row in rows)
    checks["important_unknown_warns"] = all(all(pair["actual"]["warnings"] for pair in row["oracle"] if any(check["state"] != "met" for check in pair["actual"]["checks"])) for row in rows if row["axis_family"] in {"risk-important", "all-unknown-control"})
    opportunity_index = {row["id"]: row["index"] for row in opportunities}
    amount_rows = [row for row in rows if row["axis_family"] == "amount-boundary"]
    checks["hiding_data_never_improves_score"] = all(float(next(pair["actual"]["score"] for pair in row["oracle"] if opportunity_index[pair["opportunity_id"]] == 4)) <= float(next(pair["actual"]["score"] for pair in row["oracle"] if opportunity_index[pair["opportunity_id"]] == 3)) for row in amount_rows)
    checks["known_zero_has_coverage"] = all(float(next(pair["actual"]["coverage"] for pair in row["oracle"] if opportunity_index[pair["opportunity_id"]] == 5)) > 0 for row in amount_rows)

    route_axis = list(csv.DictReader((HERE / "d28-route-axis-coverage.csv").open()))
    checks["route_axis_64"] = len(route_axis) == 64 and all(row["applicable"] in {"yes", "N/A"} and row["reason"] for row in route_axis)
    for filename, human_fields in {
        "d28-relevance-labels.csv": ("relevance_label", "independent_group_rank", "reason", "evidence_fields", "missing_information", "reviewer", "reviewed_at"),
        "d28-critical-review.csv": ("critical_misleading", "missing_important_disclosure", "reason", "evidence_fields", "reviewer", "reviewed_at"),
    }.items():
        form = list(csv.DictReader((HERE / filename).open()))
        checks[filename + "_400_blank"] = len(form) == 400 and all(all(row[field] == "" for field in human_fields) for row in form)
    reviewer = (HERE / "d28-reviewer-inputs.json").read_text()
    checks["reviewer_has_no_system_output"] = not any(f'"{field}"' in reviewer for field in ("score", "coverage", "system_rank", "matching"))

    design = list(csv.DictReader((HERE / "design-slot-matrix.csv").open()))
    checks["design_26x4"] = len(design) == 104 and len({row["row_id"] for row in design}) == 26 and {int(row["viewport_width"]) for row in design} == {360, 390, 768, 1440}
    checks["design_paths"] = all((ROOT / row["product_evidence"]).exists() and (not row["reference_evidence"] or (ROOT / row["reference_evidence"]).exists()) for row in design)
    checks["design_votes_blank"] = all(not row["human_verdict"] and not row["specialist_design_approval"] for row in design)
    group_votes = list(csv.DictReader((ROOT / "docs/experience-complete/human-design-review/group-verdicts.csv").open()))
    checks["group_votes_12_blank"] = len(group_votes) == 12 and all(all(not row[key] for key in ("verdict", "reviewed_scope", "excluded_scope", "reason", "correction", "evidence", "reviewer", "date")) for row in group_votes)
    gallery = (ROOT / "docs/experience-complete/human-design-review/evidence-gallery.md").read_text()
    links = re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", gallery)
    base = ROOT / "docs/experience-complete/human-design-review"
    broken = [link for link in links if not (base / link).resolve().exists()]
    checks["gallery_links"] = not broken and gallery.count("## G") == 12

    failures = [name for name, passed in checks.items() if not passed]
    result = {"schema": "invest.tech-evidence.validation@1", "checks": len(checks), "passed": len(checks) - len(failures), "failed": failures, "details": checks}
    (HERE / "validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
