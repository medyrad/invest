#!/usr/bin/env python3
"""Record the corrective fixture run without rewriting historical attempts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BASELINE = "0380bbf3cdcf00f6997b060a7d43a1ad980dc56c"
PACKAGE = ROOT / "docs/experience-complete/tech-evidence-01"
HERE = Path(__file__).resolve().parent
HISTORICAL = [
    "attempt-1-development-results.json",
    "attempt-1-input-freeze.json",
    "attempt-1-inputs.json",
    "attempt-2-development-results.json",
    "attempt-2-held-out-regression-results.json",
    "attempt-2-input-freeze.json",
    "attempt-2-inputs.json",
    "attempt-3-development-results.json",
    "attempt-3-held-out-regression-results.json",
    "attempt-3-input-freeze.json",
    "attempt-3-inputs.json",
    "heldout-first-attempt.json",
    "leak-replay-log.json",
]


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> None:
    preserved = []
    for name in HISTORICAL:
        current = (PACKAGE / name).read_bytes()
        baseline = subprocess.check_output(["git", "show", f"{BASELINE}:docs/experience-complete/tech-evidence-01/{name}"])
        preserved.append({"path": name, "sha256": sha_bytes(current), "equals_independent_baseline": current == baseline})
    freeze = json.loads((PACKAGE / "d28-input-freeze.json").read_text())
    payload = {
        "schema": "invest.tech-evidence-fix.fixture-change@1",
        "mission": "PROGRAMMER-EXPERIENCE-EVIDENCE-FIX-01",
        "independent_baseline_commit": BASELINE,
        "previous_input_sha256": "4f74b92e2cf72aaed04311cbd43470e6930f25710c967f7b2be137ca5160294f",
        "corrected_input_sha256": freeze["sha256"],
        "semantic_signatures": {"development": 48, "held_out": 48, "global": 96},
        "execution": {
            "development": {"database": "evidence_fix_dev_20261120", "status": "passed", "role": "development"},
            "held_out": {"database": "evidence_fix_heldout_20261120", "status": "passed", "role": "regression-after-fixture-correction"},
        },
        "results": {
            name: sha_bytes((PACKAGE / name).read_bytes())
            for name in ("d28-development-results.json", "d28-held-out-results.json")
        },
        "historical_artifacts": preserved,
        "all_historical_artifacts_unchanged": all(row["equals_independent_baseline"] for row in preserved),
        "human_labels_generated": False,
        "formula_or_weights_changed": False,
        "product_behavior_changed": False,
    }
    (HERE / "fixture-change-log.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"historical": len(preserved), "unchanged": payload["all_historical_artifacts_unchanged"]}))
    if not payload["all_historical_artifacts_unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
