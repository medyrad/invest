#!/usr/bin/env python3
"""Independent evidence checks for EVID-IT-001 and EVID-IT-002.

This validator deliberately imports neither the fixture generator nor product
scoring.  It evaluates the serialized contract evidence and proves sensitivity
with mutations written only to a temporary copy.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "docs/experience-complete/tech-evidence-01"
OUT = Path(__file__).resolve().parent
NON_SEMANTIC_SNAPSHOT_FIELDS = {"title"}
AMOUNT_FIELD = {
    "fund": "minimum_investment",
    "buyer": "price",
    "lessee": "deposit",
    "contractor": "working_capital_min",
}


def canonical_opportunity(row: dict) -> str:
    snapshot = {
        key: value
        for key, value in row["snapshot"].items()
        if key not in NON_SEMANTIC_SNAPSHOT_FIELDS
    }
    effective = {"route": row["route"], "kind": row["kind"], "snapshot": snapshot}
    return json.dumps(effective, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def semantic_duplicates(payload: dict) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in payload["opportunities"]:
        grouped[canonical_opportunity(row)].append(row)
    return [
        {
            "route": rows[0]["route"],
            "members": [
                {"id": row["id"], "split": row["split"], "index": row["index"]}
                for row in rows
            ],
        }
        for rows in grouped.values()
        if len(rows) > 1
    ]


def output_index() -> dict[str, dict]:
    rows = {}
    for split in ("development", "held-out"):
        payload = json.loads((PACKAGE / f"d28-{split}-results.json").read_text())
        rows.update({row["scenario_id"]: row for row in payload["results"]})
    return rows


def unit_basis_errors(matrix_rows: list[dict], payload: dict) -> list[str]:
    scenarios = {row["id"]: row for row in payload["scenarios"]}
    opportunities = payload["opportunities"]
    outputs = output_index()
    errors = []
    for row in matrix_rows:
        if row["axis"] != "unit-basis":
            continue
        route = row["route"]
        ids = [value for value in row["scenario_ids"].split(";") if value]
        if row["applicable"] == "N/A":
            if route not in {"operator", "charity"}:
                errors.append(f"{route}: unexpected unit-basis N/A")
            if ids or row["oracle_check_axis"] != "N/A" or "search_fields.json" not in row["contract_reference"]:
                errors.append(f"{route}: incomplete N/A trace")
            continue
        if not ids:
            errors.append(f"{route}: applicable without scenario")
            continue
        for scenario_id in ids:
            scenario = scenarios.get(scenario_id)
            if not scenario or scenario["route"] != route:
                errors.append(f"{route}: invalid scenario {scenario_id}")
                continue
            criteria = scenario["criteria"]
            has_amount = "budget_max" in criteria or "budget_min" in criteria
            has_return = "return" in criteria and isinstance(criteria["return"], dict) and bool(criteria["return"].get("basis"))
            if not (has_amount or has_return):
                errors.append(f"{route}:{scenario_id}: no numeric/return consumer")
                continue
            expected_axes = set()
            if has_amount:
                expected_axes.add("amount")
                key = AMOUNT_FIELD.get(route, "min_capital")
                route_values = [item["snapshot"].get(key) for item in opportunities if item["route"] == route and item["split"] == scenario["split"]]
                if not route_values or any(not isinstance(value, dict) or value.get("unit") != {"code": "TOMAN", "version": 1} for value in route_values):
                    errors.append(f"{route}:{scenario_id}: TOMAN@1 evidence missing")
            if has_return:
                expected_axes.add("returns")
            result = outputs.get(scenario_id)
            if not result:
                errors.append(f"{route}:{scenario_id}: output missing")
                continue
            for pair in result["oracle"]:
                actual_axes = {check["axis"] for check in pair["actual"]["checks"]}
                expected_oracle_axes = {check["axis"] for check in pair["expected"]["checks"]}
                if not expected_axes <= actual_axes or not expected_axes <= expected_oracle_axes:
                    errors.append(f"{route}:{scenario_id}: oracle consumer missing")
                    break
    return sorted(set(errors))


def main() -> None:
    payload = json.loads((PACKAGE / "d28-inputs.json").read_text())
    matrix = list(csv.DictReader((PACKAGE / "d28-route-axis-coverage.csv").open()))
    duplicates = semantic_duplicates(payload)
    signatures = {canonical_opportunity(row) for row in payload["opportunities"]}
    split_signatures = {
        split: len({canonical_opportunity(row) for row in payload["opportunities"] if row["split"] == split})
        for split in ("development", "held-out")
    }
    unit_errors = unit_basis_errors(matrix, payload)

    mutated = copy.deepcopy(payload)
    source = next(row for row in mutated["opportunities"] if row["route"] == "investor" and row["split"] == "development")
    target = next(row for row in mutated["opportunities"] if row["route"] == "investor" and row["split"] == "held-out")
    target["snapshot"] = copy.deepcopy(source["snapshot"])
    target["snapshot"]["title"] = "عنوان متفاوت که نباید duplicate را پنهان کند"
    with tempfile.TemporaryDirectory(prefix="invest-evidence-mutation-") as temp:
        mutation_path = Path(temp) / "d28-inputs-mutated.json"
        mutation_path.write_text(json.dumps(mutated, ensure_ascii=False, indent=2) + "\n")
        mutation_payload = json.loads(mutation_path.read_text())
        mutation_rejected = bool(semantic_duplicates(mutation_payload))

    mutated_matrix = copy.deepcopy(matrix)
    operator = next(row for row in mutated_matrix if row["route"] == "operator" and row["axis"] == "unit-basis")
    operator.update({"applicable": "yes", "scenario_ids": "D28-operator-development-02", "oracle_check_axis": "amount|returns"})
    unit_mutation_rejected = bool(unit_basis_errors(mutated_matrix, payload))

    checks = {
        "96_semantic_signatures": len(signatures) == 96,
        "48_unique_per_split": split_signatures == {"development": 48, "held-out": 48},
        "zero_cross_split_or_internal_duplicates": not duplicates,
        "semantic_mutation_rejected": mutation_rejected,
        "unit_basis_contract_trace": not unit_errors,
        "unit_basis_false_applicable_mutation_rejected": unit_mutation_rejected,
        "operator_charity_unit_basis_NA": {
            row["route"]
            for row in matrix
            if row["axis"] == "unit-basis" and row["applicable"] == "N/A"
        } == {"operator", "charity"},
        "denominators_preserved": Counter(row["split"] for row in payload["opportunities"]) == {"development": 48, "held-out": 48}
        and len(payload["scenarios"]) == 80,
    }
    failed = [name for name, passed in checks.items() if not passed]
    result = {
        "schema": "invest.tech-evidence-fix.d28-validation@1",
        "source_input_sha256": hashlib.sha256((PACKAGE / "d28-inputs.json").read_bytes()).hexdigest(),
        "checks": checks,
        "passed": len(checks) - len(failed),
        "failed": failed,
        "semantic_signature_count": len(signatures),
        "split_signature_counts": split_signatures,
        "duplicates": duplicates,
        "unit_basis_errors": unit_errors,
        "mutation": {
            "temporary_copy_only": True,
            "semantic_duplicate_rejected": mutation_rejected,
            "false_applicable_rejected": unit_mutation_rejected,
        },
    }
    (OUT / "d28-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
