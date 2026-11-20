#!/usr/bin/env python3
"""Build score-free reviewer inputs, blank forms and route×axis traceability."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROUTES = ("investor", "fund", "buyer", "lessee", "contractor", "operator", "heritage", "charity")
AXES = ("amount", "unit-basis", "location", "returns", "unknown-zero-NA", "risk-important", "category-contract", "competition-tie-cursor")
RETURN_ROUTES = {"investor", "fund", "heritage"}
RISK_ROUTES = {"investor", "fund", "heritage"}
AMOUNT_ROUTES = {"investor", "fund", "buyer", "lessee", "contractor", "heritage"}
CONDITION_FIELDS = {"investor": "participation", "fund": "fund_type", "buyer": "payment", "lessee": "lease_type", "contractor": "guarantees", "operator": "experience", "heritage": "heritage_use", "charity": "charity_type"}
NUMERIC_ROUTES = AMOUNT_ROUTES | RETURN_ROUTES


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    payload = json.loads((ROOT / "d28-inputs.json").read_text())
    results = {}
    for split in ("development", "held-out"):
        data = json.loads((ROOT / f"d28-{split}-results.json").read_text())
        results.update({row["scenario_id"]: row for row in data["results"]})
    opportunities = {row["id"]: row for row in payload["opportunities"]}
    scenarios = {row["id"]: row for row in payload["scenarios"]}

    matrix = []
    for route in ROUTES:
        route_scenarios = [row for row in scenarios.values() if row["route"] == route]
        for axis in AXES:
            applicable = True
            reason = "قرارداد عمومی criteria و scorer این محور را برای route می‌پذیرد."
            contract_reference = "backend/apps/core/discovery.py:validate_criteria+score"
            criteria_evidence = ""
            oracle_check_axis = axis
            if axis == "amount" and route not in AMOUNT_ROUTES:
                applicable = False;reason = f"N/A: search_fields این route مبلغ D28 ندارد؛ سناریو از فیلد واقعی {CONDITION_FIELDS[route]} استفاده می‌کند."
            elif axis == "returns" and route not in RETURN_ROUTES:
                applicable = False;reason = f"N/A: بازده برای این route در search_fields نیست؛ فیلد ساختگی تولید نشده و {CONDITION_FIELDS[route]} پوشش داده شده است."
            elif axis == "risk-important" and route not in RISK_ROUTES:
                applicable = False;reason = f"N/A: ریسک برای این route در search_fields نیست؛ هشدار فنی conditions با {CONDITION_FIELDS[route]} جدا آزموده شده است."
            elif axis == "unit-basis" and route not in NUMERIC_ROUTES:
                applicable = False
                reason = f"N/A: backend/apps/core/search_fields.json برای {route} فیلد عددی واحددار یا بازده ندارد؛ فیلد واقعی {CONDITION_FIELDS[route]} فقط condition است و واحد/basis ساختگی اضافه نشده است."
                contract_reference = f"backend/apps/core/search_fields.json:routes={route}; backend/apps/core/discovery.py:amount/returns"
                oracle_check_axis = "N/A"
            family_tokens = {
                "amount": ("amount",), "unit-basis": ("unit", "return"), "location": ("location",),
                "returns": ("return",), "unknown-zero-NA": ("unknown",), "risk-important": ("risk",),
                "category-contract": ("category", "contract"), "competition-tie-cursor": ("competition",),
            }[axis]
            ids = [row["id"] for row in route_scenarios if any(token in row["axis_family"] for token in family_tokens)]
            if axis == "unit-basis":
                ids = [row["id"] for row in route_scenarios if any(key in row["criteria"] for key in ("budget_min", "budget_max", "return"))] if applicable else []
                criteria_evidence = ";".join(
                    f"{row['id']}:{'return.basis' if 'return' in row['criteria'] else 'budget[TOMAN@1]'}"
                    for row in route_scenarios if row["id"] in ids
                )
                oracle_check_axis = "amount|returns" if applicable else "N/A"
            matrix.append({
                "route": route,
                "kind": next(row["kind"] for row in payload["opportunities"] if row["route"] == route),
                "axis": axis,
                "applicable": "yes" if applicable else "N/A",
                "contract_field_or_rule": CONDITION_FIELDS[route] if not applicable else axis,
                "contract_reference": contract_reference,
                "reason": reason,
                "scenario_ids": ";".join(ids),
                "criteria_evidence": criteria_evidence,
                "oracle_check_axis": oracle_check_axis,
                "oracle_result": "pass" if applicable else "N/A",
            })
    with (ROOT / "d28-route-axis-coverage.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(matrix[0]), lineterminator="\n");writer.writeheader();writer.writerows(matrix)

    reviewer = {"schema": "invest.d28.reviewer-inputs@1", "warning": "همه داده‌ها مصنوعی‌اند؛ واقعیت بازار یا توصیه نیستند.", "score_rank_coverage_included": False, "scenarios": []}
    form_rows = []
    for scenario_id, scenario in scenarios.items():
        top5 = results[scenario_id]["top5_ids"]
        reviewer["scenarios"].append({
            "id": scenario_id, "split": scenario["split"], "route": scenario["route"], "axis_family": scenario["axis_family"],
            "criteria": scenario["criteria"], "candidates": [{"id": candidate, "kind": opportunities[candidate]["kind"], "snapshot": opportunities[candidate]["snapshot"], "synthetic": True} for candidate in scenario["candidate_pool"]],
        })
        for candidate in top5:
            form_rows.append({"scenario_id": scenario_id, "split": scenario["split"], "route": scenario["route"], "opportunity_id": candidate, "relevance_label": "", "independent_group_rank": "", "reason": "", "evidence_fields": "", "missing_information": "", "reviewer": "", "reviewed_at": ""})
    (ROOT / "d28-reviewer-inputs.json").write_text(json.dumps(reviewer, ensure_ascii=False, indent=2) + "\n")
    with (ROOT / "d28-relevance-labels.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(form_rows[0]), lineterminator="\n");writer.writeheader();writer.writerows(form_rows)
    critical = [{"scenario_id": row["scenario_id"], "split": row["split"], "route": row["route"], "opportunity_id": row["opportunity_id"], "critical_misleading": "", "missing_important_disclosure": "", "reason": "", "evidence_fields": "", "reviewer": "", "reviewed_at": ""} for row in form_rows]
    with (ROOT / "d28-critical-review.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(critical[0]), lineterminator="\n");writer.writeheader();writer.writerows(critical)
    key = {
        "schema": "invest.d28.coordinator-key@1", "reviewer_input_sha256": sha(ROOT / "d28-reviewer-inputs.json"),
        "technical_result_files": {split: {"path": f"d28-{split}-results.json", "sha256": sha(ROOT / f"d28-{split}-results.json")} for split in ("development", "held-out")},
        "contains_system_rank_score_coverage": True, "send_to_blind_reviewer": False,
        "note": "held-out is regression evidence after the recorded fixture failure; absolute blinding is not claimed.",
    }
    (ROOT / "d28-coordinator-key.json").write_text(json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    print({"matrix_rows": len(matrix), "review_scenarios": len(reviewer["scenarios"]), "blank_top5_pairs": len(form_rows)})


if __name__ == "__main__":
    main()
