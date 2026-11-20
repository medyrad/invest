#!/usr/bin/env python3
"""Build the corrective packet manifest after the parent package manifest."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MAIN = HERE.parent / "tech-evidence-01"
EXTERNAL = [
    HERE.parent / "tech-evidence-fix-01-report.md",
    MAIN / "manifest.json",
    MAIN / "d28-inputs.json",
    MAIN / "d28-input-freeze.json",
    MAIN / "d28-development-results.json",
    MAIN / "d28-held-out-results.json",
    MAIN / "d28-route-axis-coverage.csv",
    MAIN / "design-slot-matrix.csv",
    MAIN / "validation.json",
    HERE.parent / "human-design-review" / "evidence-index.csv",
    HERE.parent / "human-design-review" / "evidence-gallery.md",
]


def entry(path: Path) -> dict[str, str | int]:
    return {
        "path": Path(os.path.relpath(path, HERE)).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def main() -> None:
    local = [path for path in sorted(HERE.iterdir()) if path.is_file() and path.name != "manifest.json"]
    d28 = json.loads((HERE / "d28-validation.json").read_text())
    design = json.loads((HERE / "design-validation.json").read_text())
    provenance = json.loads((HERE / "runtime-provenance.json").read_text())
    payload = {
        "schema": "invest.tech-evidence-fix.manifest@1",
        "mission": "PROGRAMMER-EXPERIENCE-EVIDENCE-FIX-01",
        "independent_baseline_commit": "0380bbf3cdcf00f6997b060a7d43a1ad980dc56c",
        "product_behavior_changed": False,
        "d28_formula_or_weights_changed": False,
        "human_votes_recorded": False,
        "held_out_role": "regression-after-fixture-correction",
        "validation": {
            "d28": {"passed": d28["passed"], "checks": len(d28["checks"])},
            "design": {"passed": design["passed"], "checks": len(design["checks"])},
            "provenance": {"passed": sum(provenance["checks"].values()), "checks": len(provenance["checks"])},
        },
        "files": [entry(path) for path in local + EXTERNAL],
    }
    (HERE / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print({"manifest_files": len(payload["files"])})


if __name__ == "__main__":
    main()
