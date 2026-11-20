#!/usr/bin/env python3
"""Sync only the thirteen corrected evidence slots into the human-review index."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MATRIX = ROOT / "docs/experience-complete/tech-evidence-01/design-slot-matrix.csv"
INDEX = ROOT / "docs/experience-complete/human-design-review/evidence-index.csv"
TARGETS = {
    ("DES-003", "360"), ("DES-003", "768"),
    ("DES-009", "360"), ("DES-009", "390"), ("DES-009", "768"),
    ("DES-014", "360"), ("DES-014", "768"),
    ("DES-021", "390"), ("DES-021", "768"),
    ("DES-035", "360"), ("DES-035", "390"), ("DES-035", "768"), ("DES-035", "1440"),
}


def main() -> None:
    with MATRIX.open() as handle:
        matrix = {(row["row_id"], row["viewport_width"]): row for row in csv.DictReader(handle)}
    with INDEX.open() as handle:
        rows = list(csv.DictReader(handle))
    assert TARGETS <= matrix.keys()
    touched = set()
    for row in rows:
        key = (row["row_id"], row["viewport_width"])
        if key not in TARGETS:
            continue
        source = matrix[key]
        row.update({
            "product_image": source["product_evidence"],
            "reference_image": source["reference_evidence"],
            "pair_status": source["classification"],
            "version": source["product_version"],
            "evidence_limit": source["proof_or_limitation"] + "؛ provenance: tech-evidence-fix-01/runtime-provenance.json",
            "product_canvas": source["canvas"],
        })
        assert not row["human_verdict"]
        touched.add(key)
    assert touched == TARGETS
    with INDEX.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"updated={len(touched)} human_verdicts=0")


if __name__ == "__main__":
    main()
