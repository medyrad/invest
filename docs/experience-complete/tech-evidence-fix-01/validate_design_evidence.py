#!/usr/bin/env python3
"""Validate exact route/state evidence and runtime provenance independently."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MATRIX = ROOT / "docs/experience-complete/tech-evidence-01/design-slot-matrix.csv"
TARGETS = {
    ("DES-003", "360"), ("DES-003", "768"),
    ("DES-009", "360"), ("DES-009", "390"), ("DES-009", "768"),
    ("DES-014", "360"), ("DES-014", "768"),
    ("DES-021", "390"), ("DES-021", "768"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def representative_errors(rows: list[dict]) -> list[str]:
    errors = []
    for row in rows:
        if row["classification"] != "representative-covered":
            continue
        same = row["route"] == row["evidence_route"] and row["state"] == row["evidence_state"]
        explicit = bool(row["representative_contract"])
        if not same or not explicit:
            errors.append(f"{row['row_id']}@{row['viewport_width']}: cross-route/state or missing contract")
    return errors


def main() -> None:
    rows = list(csv.DictReader(MATRIX.open()))
    provenance = json.loads((HERE / "runtime-provenance.json").read_text())
    captures = {row["evidence_file"]: row for row in provenance["captures"]}
    target_rows = [row for row in rows if (row["row_id"], row["viewport_width"]) in TARGETS]
    fresh_rows = [row for row in rows if row["product_evidence"].startswith("docs/experience-complete/tech-evidence-fix-01/design-")]
    representative = representative_errors(rows)
    capture_errors = []
    for row in fresh_rows:
        name = Path(row["product_evidence"]).name
        capture = captures.get(name)
        path = ROOT / row["product_evidence"]
        if not capture:
            capture_errors.append(f"{name}: provenance absent")
            continue
        if capture["route"] != row["evidence_route"] or capture["state"] != row["evidence_state"]:
            capture_errors.append(f"{name}: route/state mismatch")
        if capture["evidence_sha256"] != sha(path):
            capture_errors.append(f"{name}: image hash mismatch")
        if int(capture["viewport_width"]) != int(row["viewport_width"]):
            capture_errors.append(f"{name}: viewport mismatch")

    mutated = copy.deepcopy(rows)
    candidate = next(row for row in mutated if row["classification"] == "representative-covered")
    candidate["evidence_route"] = "/tools/not-the-row-route"
    candidate["representative_contract"] = ""
    with tempfile.TemporaryDirectory(prefix="invest-design-mutation-") as temp:
        path = Path(temp) / "matrix.csv"
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(mutated[0]), lineterminator="\n")
            writer.writeheader(); writer.writerows(mutated)
        mutation_rejected = bool(representative_errors(list(csv.DictReader(path.open()))))

    classifications = {}
    for row in rows:
        classifications[row["classification"]] = classifications.get(row["classification"], 0) + 1
    checks = {
        "matrix_26x4": len(rows) == 104 and len({row["row_id"] for row in rows}) == 26,
        "nine_target_slots_exact": len(target_rows) == 9 and all(row["classification"] == "capture-needed→new-evidence" and row["route"] == row["evidence_route"] and row["state"] == row["evidence_state"] for row in target_rows),
        "all_representatives_same_route_state_with_contract": not representative,
        "representative_mutation_rejected": mutation_rejected,
        "thirteen_fresh_captures": len(fresh_rows) == 13,
        "fresh_capture_provenance_valid": not capture_errors and not provenance["failed"],
        "four_library_recaptures_bound": len([row for row in fresh_rows if row["row_id"] == "DES-035"]) == 4,
        "human_fields_blank": all(not row["human_verdict"] and not row["specialist_design_approval"] for row in rows),
    }
    failed = [key for key, passed in checks.items() if not passed]
    result = {
        "schema": "invest.tech-evidence-fix.design-validation@1",
        "checks": checks,
        "passed": len(checks) - len(failed),
        "failed": failed,
        "classifications": classifications,
        "representative_errors": representative,
        "capture_errors": capture_errors,
        "target_slots": [{"row_id": row["row_id"], "width": int(row["viewport_width"]), "path": row["product_evidence"]} for row in target_rows],
        "mutation": {"temporary_copy_only": True, "cross_route_representative_rejected": mutation_rejected},
    }
    (HERE / "design-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
