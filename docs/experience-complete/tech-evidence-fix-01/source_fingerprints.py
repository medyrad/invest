#!/usr/bin/env python3
"""Fingerprint exact Git product blobs and prove the capture checkout has no product diff."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TARGET = os.environ.get(
    "PRODUCT_SOURCE_COMMIT", "24ebb1fcacb7782a6e1526e906ffed5f3514bea5"
)


def run(*args: str, text: bool = True):
    return subprocess.check_output(args, cwd=ROOT, text=text)


def commit_fingerprint(commit: str, prefix: str) -> dict:
    raw = run("git", "ls-tree", "-r", "-z", commit, "--", prefix, text=False)
    rows = []
    aggregate = hashlib.sha256()
    for record in raw.split(b"\0"):
        if not record:
            continue
        header, encoded_path = record.split(b"\t", 1)
        _mode, kind, blob = header.decode().split()
        if kind != "blob":
            continue
        path = encoded_path.decode()
        content = run("git", "cat-file", "blob", blob, text=False)
        digest = hashlib.sha256(content).hexdigest()
        rows.append({"path": path, "sha256": digest, "bytes": len(content), "blob": blob})
        aggregate.update(path.encode() + b"\0" + digest.encode() + b"\n")
    return {"sha256": aggregate.hexdigest(), "file_count": len(rows), "files": rows}


def working_fingerprint(source: dict) -> dict:
    rows = []
    aggregate = hashlib.sha256()
    missing = []
    for expected in source["files"]:
        path = ROOT / expected["path"]
        if not path.is_file():
            missing.append(expected["path"])
            continue
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        rows.append({"path": expected["path"], "sha256": digest, "bytes": len(content)})
        aggregate.update(expected["path"].encode() + b"\0" + digest.encode() + b"\n")
    return {
        "sha256": aggregate.hexdigest(),
        "file_count": len(rows),
        "missing": missing,
        "files": rows,
    }


def main() -> None:
    output = OUT / "source-fingerprints.json"
    previous = json.loads(output.read_text())
    historical = previous.get("historical")
    if historical is None:
        historical = {
            key: previous[key]
            for key in (
                "checkout_commit",
                "product_baseline_commit",
                "product_diff_from_baseline",
                "frontend",
                "backend",
            )
        }
    checkout = run("git", "rev-parse", "HEAD").strip()
    target = run("git", "rev-parse", TARGET).strip()
    target_tree = run("git", "rev-parse", f"{target}^{{tree}}").strip()
    checkout_tree = run("git", "rev-parse", f"{checkout}^{{tree}}").strip()
    frontend = commit_fingerprint(target, "frontend")
    backend = commit_fingerprint(target, "backend")
    product_diff = run(
        "git", "diff", "--name-only", target, "--", "frontend", "backend"
    ).splitlines()
    untracked = run(
        "git", "ls-files", "--others", "--exclude-standard", "--", "frontend", "backend"
    ).splitlines()
    payload = {
        "schema": "invest.runtime-source-fingerprints@2",
        "historical": historical,
        "current_recapture": {
            "capture_checkout_commit": checkout,
            "capture_checkout_tree": checkout_tree,
            "product_source_commit": target,
            "product_source_tree": target_tree,
            "product_diff_from_source": product_diff,
            "untracked_product_files": untracked,
            "frontend": frontend,
            "backend": backend,
            "working_frontend": working_fingerprint(frontend),
            "working_backend": working_fingerprint(backend),
        },
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    current = payload["current_recapture"]
    ok = (
        not product_diff
        and not untracked
        and not current["working_frontend"]["missing"]
        and not current["working_backend"]["missing"]
        and current["working_frontend"]["sha256"] == frontend["sha256"]
        and current["working_backend"]["sha256"] == backend["sha256"]
    )
    print(
        json.dumps(
            {
                "product_source_commit": target,
                "product_source_tree": target_tree,
                "frontend_sha256": frontend["sha256"],
                "backend_sha256": backend["sha256"],
                "working_tree_matches": ok,
            }
        )
    )
    if not ok:
        raise SystemExit("Working product source differs from the declared product commit.")


if __name__ == "__main__":
    main()
