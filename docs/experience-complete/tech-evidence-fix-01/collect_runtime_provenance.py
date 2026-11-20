#!/usr/bin/env python3
"""Bind current DES-035 captures to exact Git source, labeled images and containers."""

from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
WEB_IMAGE = "invest-web"
BACKEND_IMAGE = "invest-backend"
WEB_CONTAINER = "invest-web-1"
BACKEND_CONTAINER = "invest-backend-1"
RUNTIME_URL = "http://127.0.0.1:3108"


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


def inspect_container(name: str) -> dict:
    data = json.loads(run("docker", "inspect", name))[0]
    return {
        "name": name,
        "id": data["Id"],
        "image_id": data["Image"],
        "state": data["State"]["Status"],
    }


def runtime_hashes(container: str, command: str) -> dict[str, str]:
    output = run("docker", "exec", container, "sh", "-lc", command)
    rows = {}
    for line in output.splitlines():
        digest, path = line.split(maxsplit=1)
        rows[path] = digest
    return rows


def hash_map(rows: dict[str, str]) -> str:
    aggregate = hashlib.sha256()
    for path, digest in sorted(rows.items()):
        aggregate.update(path.encode() + b"\0" + digest.encode() + b"\n")
    return aggregate.hexdigest()


def response(path: str) -> dict:
    with urllib.request.urlopen(RUNTIME_URL + path, timeout=10) as result:
        return json.loads(result.read())


def historical(previous: dict) -> dict:
    if previous.get("schema") == "invest.runtime-capture-provenance@2":
        return previous["historical"]
    runtime = dict(previous["runtime"])
    runtime.pop("current_recapture", None)
    return {
        "description": "Preserved evidence from 0380bbf/3120; not the source of current DES-035 recaptures.",
        "checkout_commit": previous["checkout_commit"],
        "product_baseline_commit": previous["product_baseline_commit"],
        "source": previous["source"],
        "images": previous["images"],
        "runtime": runtime,
        "checks": previous["checks"],
        "captures": [
            row for row in previous["captures"] if row["row_id"] != "DES-035"
        ],
    }


def main() -> None:
    source_file = HERE / "source-fingerprints.json"
    source_document = json.loads(source_file.read_text())
    source = source_document["current_recapture"]
    previous = json.loads((HERE / "runtime-provenance.json").read_text())
    web = inspect_image(WEB_IMAGE)
    backend = inspect_image(BACKEND_IMAGE)
    web_container = inspect_container(WEB_CONTAINER)
    backend_container = inspect_container(BACKEND_CONTAINER)
    build_id = run("docker", "exec", WEB_CONTAINER, "cat", "/app/.next/BUILD_ID")
    frontend_runtime = runtime_hashes(
        WEB_CONTAINER, "find /app -type f -exec sha256sum {} + | sort -k2"
    )
    backend_runtime = runtime_hashes(
        BACKEND_CONTAINER,
        "find /app -path /app/.venv -prune -o -type f -exec sha256sum {} +",
    )
    backend_missing = []
    backend_mismatched = []
    for row in source["backend"]["files"]:
        path = "/app/" + row["path"].removeprefix("backend/")
        actual = backend_runtime.get(path)
        if actual is None:
            backend_missing.append(row["path"])
        elif actual != row["sha256"]:
            backend_mismatched.append(row["path"])

    expected_binding = {
        "capture_checkout_commit": source["capture_checkout_commit"],
        "product_source_commit": source["product_source_commit"],
        "product_source_tree": source["product_source_tree"],
        "frontend_source_sha256": source["frontend"]["sha256"],
        "backend_source_sha256": source["backend"]["sha256"],
        "frontend_image_id": web["image_id"],
        "backend_image_id": backend["image_id"],
        "frontend_build_id": build_id,
        "runtime_url": RUNTIME_URL,
    }
    captures = []
    for metadata_path in sorted(HERE.glob("capture-library-*.json")):
        metadata = json.loads(metadata_path.read_text())
        image_path = HERE / metadata["evidence_file"]
        captures.append(
            {
                **metadata,
                "metadata_file": metadata_path.name,
                "metadata_sha256": sha(metadata_path),
                "evidence_sha256": sha(image_path),
                "evidence_bytes": image_path.stat().st_size,
            }
        )

    labels_web = web["labels"]
    labels_backend = backend["labels"]
    checks = {
        "capture_checkout_matches_source_document": source["capture_checkout_commit"]
        == run("git", "rev-parse", "HEAD"),
        "product_source_is_24ebb1f": source["product_source_commit"]
        == run("git", "rev-parse", "24ebb1f"),
        "working_product_diff_empty": not source["product_diff_from_source"]
        and not source["untracked_product_files"],
        "working_fingerprints_match_product_commit": source["working_frontend"]["sha256"]
        == source["frontend"]["sha256"]
        and source["working_backend"]["sha256"] == source["backend"]["sha256"],
        "frontend_image_labels_match_source": labels_web.get(
            "org.opencontainers.image.revision"
        )
        == source["product_source_commit"]
        and labels_web.get("invest.source.tree") == source["product_source_tree"]
        and labels_web.get("invest.source.frontend.sha256")
        == source["frontend"]["sha256"],
        "backend_image_labels_match_source": labels_backend.get(
            "org.opencontainers.image.revision"
        )
        == source["product_source_commit"]
        and labels_backend.get("invest.source.tree") == source["product_source_tree"]
        and labels_backend.get("invest.source.backend.sha256")
        == source["backend"]["sha256"],
        "containers_run_exact_images": web_container["image_id"] == web["image_id"]
        and backend_container["image_id"] == backend["image_id"]
        and web_container["state"] == backend_container["state"] == "running",
        "backend_commit_files_match_runtime": not backend_missing
        and not backend_mismatched,
        "frontend_runtime_and_build_id_hashed": bool(build_id)
        and len(frontend_runtime) >= 20,
        "primary_runtime_identifies_itself": response("/api/v1/core/version").get(
            "runtime"
        )
        == "primary-development"
        and response("/core-version.json").get("version")
        == "RUNTIME-HOME-LOADING-FIX-01",
        "four_current_captures_bound": len(captures) == 4
        and all(row.get("runtime_binding") == expected_binding for row in captures),
        "capture_conditions_complete": all(
            row["row_id"] == "DES-035"
            and row["product_url"] == RUNTIME_URL
            and row["final_url"] == RUNTIME_URL + "/library"
            and row["state"] == "topic-index;accordion-open"
            and row["interaction"]["expanded_accordions"] >= 1
            and row["motion_condition"] == "reduced"
            and row["browser"]["version"]
            for row in captures
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    payload = {
        "schema": "invest.runtime-capture-provenance@2",
        "historical": historical(previous),
        "current_recapture": {
            "mission": "PROGRAMMER-RUNTIME-HOME-LOADING-FIX-02",
            "capture_checkout_commit": source["capture_checkout_commit"],
            "capture_checkout_tree": source["capture_checkout_tree"],
            "product_source_commit": source["product_source_commit"],
            "product_source_tree": source["product_source_tree"],
            "product_diff_from_source": source["product_diff_from_source"],
            "source": {
                "fingerprint_file": source_file.name,
                "fingerprint_file_sha256": sha(source_file),
                "frontend_sha256": source["frontend"]["sha256"],
                "frontend_file_count": source["frontend"]["file_count"],
                "backend_sha256": source["backend"]["sha256"],
                "backend_file_count": source["backend"]["file_count"],
            },
            "images": {"frontend": web, "backend": backend},
            "containers": {"frontend": web_container, "backend": backend_container},
            "runtime": {
                "product_url": RUNTIME_URL,
                "frontend_build_id": build_id,
                "frontend_file_count": len(frontend_runtime),
                "frontend_runtime_sha256": hash_map(frontend_runtime),
                "backend_missing_commit_files": backend_missing,
                "backend_mismatched_commit_files": backend_mismatched,
                "version": response("/api/v1/core/version"),
            },
            "expected_capture_binding": expected_binding,
            "checks": checks,
            "failed": failed,
            "captures": captures,
        },
        "checks": checks,
        "failed": failed,
    }
    (HERE / "runtime-provenance.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "checks": len(checks),
                "failed": failed,
                "captures": len(captures),
                "build_id": build_id,
            },
            ensure_ascii=False,
        )
    )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
