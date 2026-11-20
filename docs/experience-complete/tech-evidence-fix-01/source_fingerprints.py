#!/usr/bin/env python3
"""Create deterministic fingerprints for the product source used by evidence images."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def tracked_files(prefix: str) -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z", prefix], cwd=ROOT)
    return [ROOT / value.decode() for value in raw.split(b"\0") if value]


def fingerprint(prefix: str) -> dict:
    rows = []
    aggregate = hashlib.sha256()
    for path in tracked_files(prefix):
        relative = path.relative_to(ROOT).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({"path": relative, "sha256": digest, "bytes": path.stat().st_size})
        aggregate.update(relative.encode() + b"\0" + digest.encode() + b"\n")
    return {"sha256": aggregate.hexdigest(), "file_count": len(rows), "files": rows}


def main() -> None:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    product_diff = subprocess.check_output(
        ["git", "diff", "--name-only", "79519bb8e88cbf6c0bcf7614c63b3737cc668a70..HEAD", "--", "backend", "frontend"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    payload = {
        "schema": "invest.runtime-source-fingerprints@1",
        "checkout_commit": commit,
        "product_baseline_commit": "79519bb8e88cbf6c0bcf7614c63b3737cc668a70",
        "product_diff_from_baseline": product_diff,
        "frontend": fingerprint("frontend"),
        "backend": fingerprint("backend"),
    }
    (OUT / "source-fingerprints.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: payload[key]["sha256"] for key in ("frontend", "backend")}))


if __name__ == "__main__":
    main()
