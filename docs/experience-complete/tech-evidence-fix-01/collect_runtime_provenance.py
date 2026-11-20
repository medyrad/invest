#!/usr/bin/env python3
"""Bind captured evidence to exact checkout, images and runtime files."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
WEB_IMAGE = "investevidencefix-web:0380bbf"
BACKEND_IMAGE = "investevidencefix-backend:0380bbf"
WEB_CONTAINER = "invest-evidencefix-web-1"
BACKEND_CONTAINER = "invest-evidencefix-backend-1"
CURRENT_WEB_IMAGE = "invest-web"
CURRENT_BACKEND_IMAGE = "invest-backend"
CURRENT_WEB_CONTAINER = "invest-web-validation"
CURRENT_BACKEND_CONTAINER = "invest-backend-1"


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_image(name: str) -> dict:
    data = json.loads(run("docker", "image", "inspect", name))[0]
    return {
        "reference": name,
        "image_id": data["Id"],
        "repo_digests": data.get("RepoDigests") or [],
        "labels": data["Config"].get("Labels") or {},
        "created": data["Created"],
    }


def runtime_hashes(container: str, command: str) -> dict[str, str]:
    output = run("docker", "exec", container, "sh", "-lc", command)
    rows = {}
    for line in output.splitlines():
        digest, path = line.split(maxsplit=1)
        rows[path] = digest
    return rows


def main() -> None:
    source = json.loads((HERE / "source-fingerprints.json").read_text())
    web = inspect_image(WEB_IMAGE)
    backend = inspect_image(BACKEND_IMAGE)
    build_id = run("docker", "exec", WEB_CONTAINER, "cat", "/app/.next/BUILD_ID")
    current_web = inspect_image(CURRENT_WEB_IMAGE)
    current_backend = inspect_image(CURRENT_BACKEND_IMAGE)
    current_build_id = run("docker", "exec", CURRENT_WEB_CONTAINER, "cat", "/app/.next/BUILD_ID")
    frontend_runtime = runtime_hashes(
        WEB_CONTAINER,
        "find /app/.next/static /app/.next/server/app/tools /app/.next/server/app/library -type f -exec sha256sum {} +; sha256sum /app/.next/BUILD_ID /app/server.js",
    )
    backend_runtime = runtime_hashes(
        BACKEND_CONTAINER,
        "find /app -path /app/.venv -prune -o -type f -exec sha256sum {} +",
    )
    backend_mismatches = []
    backend_missing = []
    for row in source["backend"]["files"]:
        relative = row["path"].removeprefix("backend/")
        runtime_path = "/app/" + relative
        actual = backend_runtime.get(runtime_path)
        if actual is None:
            backend_missing.append(row["path"])
        elif actual != row["sha256"]:
            backend_mismatches.append(row["path"])

    captures = []
    for metadata_path in sorted(HERE.glob("capture-*.json")):
        metadata = json.loads(metadata_path.read_text())
        image_path = HERE / metadata["evidence_file"]
        current = metadata["product_url"] == "http://127.0.0.1:3108"
        captures.append({
            **metadata,
            "metadata_file": metadata_path.name,
            "metadata_sha256": sha(metadata_path),
            "evidence_sha256": sha(image_path),
            "evidence_bytes": image_path.stat().st_size,
            "runtime": {
                "frontend_image_id": current_web["image_id"] if current else web["image_id"],
                "backend_image_id": current_backend["image_id"] if current else backend["image_id"],
                "frontend_build_id": current_build_id if current else build_id,
            },
        })

    checks = {
        "checkout_matches_both_image_revisions": web["labels"].get("org.opencontainers.image.revision") == source["checkout_commit"] == backend["labels"].get("org.opencontainers.image.revision"),
        "frontend_source_fingerprint_matches_image_label": web["labels"].get("invest.source.frontend.sha256") == source["frontend"]["sha256"],
        "backend_source_fingerprint_matches_image_label": backend["labels"].get("invest.source.backend.sha256") == source["backend"]["sha256"],
        "product_diff_from_baseline_empty": source["product_diff_from_baseline"] == [],
        "backend_tracked_source_equals_runtime": not backend_missing and not backend_mismatches,
        "frontend_build_id_present": bool(build_id),
        "frontend_affected_runtime_files_hashed": len(frontend_runtime) >= 20,
        "all_13_captures_bound": len(captures) == 13,
        "all_capture_files_exist": all((HERE / row["evidence_file"]).exists() for row in captures),
        "capture_conditions_complete": all(
            row["final_url"].startswith(("http://127.0.0.1:3120", "http://127.0.0.1:3108"))
            and row["font_condition"]
            and row["motion_condition"] == "reduced"
            and row["browser"]["version"]
            and row["captured_at_utc"]
            for row in captures
        ),
    }
    failed = [key for key, value in checks.items() if not value]
    payload = {
        "schema": "invest.runtime-capture-provenance@1",
        "checkout_commit": source["checkout_commit"],
        "product_baseline_commit": source["product_baseline_commit"],
        "source": {
            "frontend_sha256": source["frontend"]["sha256"],
            "frontend_file_count": source["frontend"]["file_count"],
            "backend_sha256": source["backend"]["sha256"],
            "backend_file_count": source["backend"]["file_count"],
            "fingerprint_file": "source-fingerprints.json",
        },
        "images": {"frontend": web, "backend": backend},
        "runtime": {
            "product_url": "http://127.0.0.1:3120",
            "frontend_container": WEB_CONTAINER,
            "backend_container": BACKEND_CONTAINER,
            "frontend_build_id": build_id,
            "frontend_affected_file_hashes": frontend_runtime,
            "backend_missing_tracked_files": backend_missing,
            "backend_mismatched_tracked_files": backend_mismatches,
            "current_recapture": {
                "mission": "PROGRAMMER-RUNTIME-HOME-LOADING-FIX-01",
                "product_url": "http://127.0.0.1:3108",
                "frontend_container": CURRENT_WEB_CONTAINER,
                "backend_container": CURRENT_BACKEND_CONTAINER,
                "frontend_image": current_web,
                "backend_image": current_backend,
                "frontend_build_id": current_build_id,
                "scope": "DES-035 library accordion-open at 360/390/768/1440 only",
            },
        },
        "checks": checks,
        "failed": failed,
        "captures": captures,
    }
    (HERE / "runtime-provenance.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"checks": len(checks), "failed": failed, "captures": len(captures), "build_id": build_id}, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
