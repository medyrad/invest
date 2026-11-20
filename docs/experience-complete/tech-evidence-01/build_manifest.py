from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIX_ROOT = ROOT.parent / "tech-evidence-fix-01"
EXTERNAL_FILES = (
    ROOT.parent / "tech-evidence-01-report.md",
    ROOT.parent / "tech-evidence-fix-01-report.md",
    ROOT.parent / "human-design-review" / "evidence-index.csv",
    ROOT.parent / "human-design-review" / "evidence-gallery.md",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(path: Path) -> dict[str, str | int]:
    return {
        "path": Path(os.path.relpath(path, ROOT)).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def main() -> None:
    files = sorted(
        path
        for path in ROOT.iterdir()
        if path.is_file() and path.name != "manifest.json"
    )
    files.extend(EXTERNAL_FILES)
    files.extend(
        path
        for path in sorted(FIX_ROOT.iterdir())
        if path.is_file() and path.name != "manifest.json"
    )
    freeze = json.loads((ROOT / "d28-input-freeze.json").read_text())
    validation = json.loads((ROOT / "validation.json").read_text())
    payload = {
        "schema": "invest.tech-evidence.manifest@1",
        "mission": "TECH-EXPERIENCE-EVIDENCE-01",
        "baseline_commit": "79519bb8e88cbf6c0bcf7614c63b3737cc668a70",
        "source_archive_sha256": "6221401c736250c5ac7e5595aa988301f64b8d2fe576590291a7c2e53c247f5b",
        "corrective_mission": "PROGRAMMER-EXPERIENCE-EVIDENCE-FIX-01",
        "independent_baseline_commit": "0380bbf3cdcf00f6997b060a7d43a1ad980dc56c",
        "input_sha256": freeze["sha256"],
        "product_behavior_changed": False,
        "d28_formula_or_weights_changed": False,
        "human_votes_recorded": False,
        "design": {"rows": 26, "slots": 104, "widths": [360, 390, 768, 1440]},
        "d28": {
            "routes": 8,
            "scenarios": 80,
            "opportunities": 96,
            "development_scenarios": 32,
            "held_out_scenarios": 48,
            "held_out_status": "regression-after-semantic-fixture-correction",
            "candidate_pairs": 480,
            "top5_pairs": 400,
            "oracle_mismatches": 0,
        },
        "validation": {"checks": validation["checks"], "passed": validation["passed"]},
        "files": [entry(path) for path in files],
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print({"manifest_files": len(payload["files"])})


if __name__ == "__main__":
    main()
