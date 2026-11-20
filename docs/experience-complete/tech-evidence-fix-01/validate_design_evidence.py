#!/usr/bin/env python3
"""Validate design slots and every link in the current capture provenance chain."""

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
PRODUCT_COMMIT = "24ebb1fcacb7782a6e1526e906ffed5f3514bea5"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def representative_errors(rows: list[dict]) -> list[str]:
    errors = []
    for row in rows:
        if row["classification"] != "representative-covered":
            continue
        same = row["route"] == row["evidence_route"] and row["state"] == row["evidence_state"]
        if not same or not row["representative_contract"]:
            errors.append(f"{row['row_id']}@{row['viewport_width']}: cross-route/state or missing contract")
    return errors


def chain_errors(current: dict, source_document: dict) -> list[str]:
    errors = []
    source = source_document.get("current_recapture", {})
    required = (
        "capture_checkout_commit", "product_source_commit", "product_source_tree",
        "source", "images", "containers", "runtime", "expected_capture_binding", "captures",
    )
    for key in required:
        if not current.get(key):
            errors.append(f"missing current_recapture.{key}")
    if errors:
        return errors
    if current["capture_checkout_commit"] != source.get("capture_checkout_commit"):
        errors.append("capture checkout does not match source fingerprint document")
    if current["product_source_commit"] != PRODUCT_COMMIT:
        errors.append("product source commit is not 24ebb1f")
    if current["product_source_commit"] != source.get("product_source_commit"):
        errors.append("product source commit mismatch")
    if current["product_source_tree"] != source.get("product_source_tree"):
        errors.append("product source tree mismatch")
    if source.get("product_diff_from_source") or source.get("untracked_product_files"):
        errors.append("product source diff is not empty")
    for kind in ("frontend", "backend"):
        expected = source.get(kind, {}).get("sha256")
        working = source.get(f"working_{kind}", {}).get("sha256")
        recorded = current["source"].get(f"{kind}_sha256")
        if not expected or working != expected or recorded != expected:
            errors.append(f"{kind} source fingerprint mismatch")
        image = current["images"].get(kind, {})
        labels = image.get("labels", {})
        if labels.get("org.opencontainers.image.revision") != PRODUCT_COMMIT:
            errors.append(f"{kind} image commit label mismatch")
        if labels.get("invest.source.tree") != current["product_source_tree"]:
            errors.append(f"{kind} image tree label mismatch")
        if labels.get(f"invest.source.{kind}.sha256") != expected:
            errors.append(f"{kind} image fingerprint label mismatch")
        container = current["containers"].get(kind, {})
        if container.get("image_id") != image.get("image_id") or container.get("state") != "running":
            errors.append(f"{kind} container/image binding mismatch")
    fingerprint_file = HERE / current["source"].get("fingerprint_file", "")
    if not fingerprint_file.is_file() or sha(fingerprint_file) != current["source"].get("fingerprint_file_sha256"):
        errors.append("source fingerprint document hash mismatch")
    runtime = current["runtime"]
    if runtime.get("product_url") != "http://127.0.0.1:3108":
        errors.append("current runtime URL is not primary 3108")
    if not runtime.get("frontend_build_id") or not runtime.get("frontend_runtime_sha256"):
        errors.append("frontend BUILD_ID/runtime hash absent")
    if runtime.get("backend_missing_commit_files") or runtime.get("backend_mismatched_commit_files"):
        errors.append("backend runtime differs from commit files")
    binding = current["expected_capture_binding"]
    if binding.get("frontend_build_id") != runtime.get("frontend_build_id"):
        errors.append("capture BUILD_ID binding mismatch")
    if binding.get("runtime_url") != runtime.get("product_url"):
        errors.append("capture runtime URL binding mismatch")
    captures = current["captures"]
    if len(captures) != 4:
        errors.append("current recapture does not contain four images")
    for capture in captures:
        metadata = HERE / capture.get("metadata_file", "")
        image = HERE / capture.get("evidence_file", "")
        if not metadata.is_file() or sha(metadata) != capture.get("metadata_sha256"):
            errors.append(f"{capture.get('metadata_file')}: metadata hash mismatch")
        if not image.is_file() or sha(image) != capture.get("evidence_sha256"):
            errors.append(f"{capture.get('evidence_file')}: image hash mismatch")
        if capture.get("runtime_binding") != binding:
            errors.append(f"{capture.get('evidence_file')}: runtime binding mismatch")
        if capture.get("state") != "topic-index;accordion-open" or capture.get("interaction", {}).get("expanded_accordions", 0) < 1:
            errors.append(f"{capture.get('evidence_file')}: accordion state mismatch")
    return errors


def main() -> None:
    rows = list(csv.DictReader(MATRIX.open()))
    provenance = json.loads((HERE / "runtime-provenance.json").read_text())
    source_document = json.loads((HERE / "source-fingerprints.json").read_text())
    historical_captures = provenance["historical"]["captures"]
    current_captures = provenance["current_recapture"]["captures"]
    captures = {row["evidence_file"]: row for row in historical_captures + current_captures}
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

    mutated_rows = copy.deepcopy(rows)
    candidate = next(row for row in mutated_rows if row["classification"] == "representative-covered")
    candidate["evidence_route"] = "/tools/not-the-row-route"
    candidate["representative_contract"] = ""
    with tempfile.TemporaryDirectory(prefix="invest-design-mutation-") as temp:
        path = Path(temp) / "matrix.csv"
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(mutated_rows[0]), lineterminator="\n")
            writer.writeheader(); writer.writerows(mutated_rows)
        representative_mutation_rejected = bool(representative_errors(list(csv.DictReader(path.open()))))

    chain = chain_errors(provenance["current_recapture"], source_document)
    bad_commit = copy.deepcopy(provenance["current_recapture"])
    bad_commit["product_source_commit"] = "0" * 40
    commit_mutation_rejected = bool(chain_errors(bad_commit, source_document))
    bad_fingerprint = copy.deepcopy(provenance["current_recapture"])
    bad_fingerprint["source"]["frontend_sha256"] = "0" * 64
    fingerprint_mutation_rejected = bool(chain_errors(bad_fingerprint, source_document))

    classifications = {}
    for row in rows:
        classifications[row["classification"]] = classifications.get(row["classification"], 0) + 1
    checks = {
        "matrix_26x4": len(rows) == 104 and len({row["row_id"] for row in rows}) == 26,
        "nine_target_slots_exact": len(target_rows) == 9 and all(row["classification"] == "capture-needed→new-evidence" and row["route"] == row["evidence_route"] and row["state"] == row["evidence_state"] for row in target_rows),
        "all_representatives_same_route_state_with_contract": not representative,
        "representative_mutation_rejected": representative_mutation_rejected,
        "thirteen_fresh_captures": len(fresh_rows) == 13,
        "fresh_capture_provenance_valid": not capture_errors and not chain and not provenance["failed"],
        "four_library_recaptures_bound": len(current_captures) == 4,
        "commit_mutation_rejected": commit_mutation_rejected,
        "fingerprint_mutation_rejected": fingerprint_mutation_rejected,
        "human_fields_blank": all(not row["human_verdict"] and not row["specialist_design_approval"] for row in rows),
    }
    failed = [key for key, passed in checks.items() if not passed]
    result = {
        "schema": "invest.tech-evidence-fix.design-validation@2",
        "checks": checks,
        "passed": len(checks) - len(failed),
        "failed": failed,
        "classifications": classifications,
        "representative_errors": representative,
        "capture_errors": capture_errors,
        "provenance_chain_errors": chain,
        "mutation": {
            "temporary_copy_only": True,
            "cross_route_representative_rejected": representative_mutation_rejected,
            "wrong_commit_rejected": commit_mutation_rejected,
            "wrong_fingerprint_rejected": fingerprint_mutation_rejected,
        },
    }
    (HERE / "design-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
