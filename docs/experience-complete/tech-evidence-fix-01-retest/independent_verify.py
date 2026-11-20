#!/usr/bin/env python3
"""Independent bounded verifier for EVID-IT-001..004; imports no product scorer."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT / "docs/experience-complete/tech-evidence-01"
FIX = ROOT / "docs/experience-complete/tech-evidence-fix-01"
HERE = Path(__file__).resolve().parent
BASE = "0380bbf3cdcf00f6997b060a7d43a1ad980dc56c"
PRODUCT = "79519bb8e88cbf6c0bcf7614c63b3737cc668a70"
DELIVERY = "a742f709060198785f69eb4bc1fe97e70fd660ce"
ROUTES = {"investor", "fund", "buyer", "lessee", "contractor", "operator", "heritage", "charity"}
AMOUNT_FIELDS = {"investor": "min_capital", "fund": "minimum_investment", "buyer": "price", "lessee": "deposit", "contractor": "working_capital_min", "heritage": "min_capital"}
TARGETS = {
    ("DES-003", "360"), ("DES-003", "768"),
    ("DES-009", "360"), ("DES-009", "390"), ("DES-009", "768"),
    ("DES-014", "360"), ("DES-014", "768"),
    ("DES-021", "390"), ("DES-021", "768"),
}


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def canonical(row: dict) -> str:
    # Only contract/scoring material participates: row metadata and display title do not.
    snapshot = {key: value for key, value in row["snapshot"].items() if key != "title"}
    return json.dumps({"route": row["route"], "kind": row["kind"], "snapshot": snapshot}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def duplicates(payload: dict) -> list[dict]:
    grouped = defaultdict(list)
    for row in payload["opportunities"]:
        grouped[canonical(row)].append(row)
    return [
        {"route": rows[0]["route"], "members": [{"id": row["id"], "split": row["split"], "index": row["index"]} for row in rows]}
        for rows in grouped.values() if len(rows) > 1
    ]


def source_fingerprint(prefix: str) -> dict:
    paths = [Path(value) for value in run("git", "ls-files", prefix).splitlines() if value]
    aggregate = hashlib.sha256()
    rows = []
    for relative in paths:
        digest = sha(ROOT / relative)
        aggregate.update(relative.as_posix().encode() + b"\0" + digest.encode() + b"\n")
        rows.append({"path": relative.as_posix(), "sha256": digest})
    return {"sha256": aggregate.hexdigest(), "file_count": len(rows), "files": rows}


def docker_json(*args: str):
    return json.loads(run("docker", *args))


def runtime_hashes(container: str, command: str) -> dict[str, str]:
    output = run("docker", "exec", container, "sh", "-lc", command)
    result = {}
    for line in output.splitlines():
        digest, path = line.split(maxsplit=1)
        result[path] = digest
    return result


def main() -> None:
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}
    manifest = load(FIX / "manifest.json")
    manifest_errors = []
    for entry in manifest["files"]:
        path = (FIX / entry["path"]).resolve()
        if not path.exists() or path.stat().st_size != entry["bytes"] or sha(path) != entry["sha256"]:
            manifest_errors.append(entry["path"])
    checks["fix_manifest_hashes"] = not manifest_errors
    details["manifest_files"] = len(manifest["files"])
    details["manifest_errors"] = manifest_errors

    post_delivery = [value for value in run("git", "diff", "--name-only", DELIVERY + "..HEAD").splitlines() if value]
    allowed_post_delivery = all(
        value == "docs/experience-complete/tech-evidence-fix-01-retest-report.md"
        or value.startswith("docs/experience-complete/tech-evidence-fix-01-retest/")
        for value in post_delivery
    )
    checks["delivery_checkout"] = (
        subprocess.run(["git", "merge-base", "--is-ancestor", DELIVERY, "HEAD"], cwd=ROOT).returncode == 0
        and allowed_post_delivery
    )
    details["post_delivery_files"] = post_delivery
    checks["no_product_behavior_diff"] = not run("git", "diff", "--name-only", PRODUCT + "..HEAD", "--", "backend", "frontend")
    oracle_now = (PACKAGE / "d28_run.py").read_bytes()
    oracle_base = subprocess.check_output(["git", "show", BASE + ":docs/experience-complete/tech-evidence-01/d28_run.py"], cwd=ROOT)
    checks["oracle_unchanged"] = oracle_now == oracle_base
    details["oracle_sha256"] = hashlib.sha256(oracle_now).hexdigest()

    historical = [
        "attempt-1-development-results.json", "attempt-1-input-freeze.json", "attempt-1-inputs.json",
        "attempt-2-development-results.json", "attempt-2-held-out-regression-results.json", "attempt-2-input-freeze.json", "attempt-2-inputs.json",
        "attempt-3-development-results.json", "attempt-3-held-out-regression-results.json", "attempt-3-input-freeze.json", "attempt-3-inputs.json",
        "heldout-first-attempt.json", "leak-replay-log.json",
    ]
    historical_changed = []
    for name in historical:
        current = (PACKAGE / name).read_bytes()
        baseline = subprocess.check_output(["git", "show", f"{BASE}:docs/experience-complete/tech-evidence-01/{name}"], cwd=ROOT)
        if current != baseline:
            historical_changed.append(name)
    checks["historical_heldout_untouched"] = not historical_changed
    leak = load(PACKAGE / "leak-replay-log.json")
    checks["heldout_still_regression"] = leak["absolute_blinding_claimed"] is False and "regression" in leak["events"][-1]["result"] and manifest["held_out_role"] == "regression-after-fixture-correction"
    details["historical_changed"] = historical_changed

    payload = load(PACKAGE / "d28-inputs.json")
    signatures = [canonical(row) for row in payload["opportunities"]]
    duplicate_rows = duplicates(payload)
    split_signatures = {split: len({canonical(row) for row in payload["opportunities"] if row["split"] == split}) for split in ("development", "held-out")}
    checks["evid_it_001_96_semantic_unique"] = len(signatures) == len(set(signatures)) == 96 and split_signatures == {"development": 48, "held-out": 48} and not duplicate_rows
    meaningful_cross_split = []
    for route in ROUTES:
        for index in (4, 5):
            rows = {row["split"]: row for row in payload["opportunities"] if row["route"] == route and row["index"] == index}
            left = {k: v for k, v in rows["development"]["snapshot"].items() if k != "title"}
            right = {k: v for k, v in rows["held-out"]["snapshot"].items() if k != "title"}
            changed = {key for key in set(left) | set(right) if left.get(key) != right.get(key)}
            meaningful_cross_split.append({"route": route, "index": index, "changed": sorted(changed)})
    checks["unknown_zero_not_cosmetic"] = all(set(row["changed"]) & {"group", "province", "risk", "contract_mode"} for row in meaningful_cross_split)
    mutation = copy.deepcopy(payload)
    source = next(row for row in mutation["opportunities"] if row["route"] == "investor" and row["split"] == "development")
    target = next(row for row in mutation["opportunities"] if row["route"] == "investor" and row["split"] == "held-out")
    target["snapshot"] = copy.deepcopy(source["snapshot"])
    target["snapshot"]["title"] = "عنوان متفاوت mutation"
    checks["semantic_duplicate_mutation_rejected"] = bool(duplicates(mutation))
    details.update({"semantic_signatures": len(set(signatures)), "split_signatures": split_signatures, "duplicates": duplicate_rows, "unknown_zero_cross_split_changes": meaningful_cross_split})

    development = load(PACKAGE / "d28-development-results.json")
    heldout = load(PACKAGE / "d28-held-out-results.json")
    checks["d28_denominators_preserved"] = (
        len(payload["scenarios"]) == 80 and len(payload["opportunities"]) == 96
        and set(payload["routes"]) == ROUTES
        and all(len(row["candidate_pool"]) == len(set(row["candidate_pool"])) == 6 for row in payload["scenarios"])
        and development["counts"]["candidate_pairs"] == 192 and heldout["counts"]["candidate_pairs"] == 288
        and development["counts"]["top5_pairs"] == 160 and heldout["counts"]["top5_pairs"] == 240
    )

    search_fields = load(ROOT / "backend/apps/core/search_fields.json")
    def route_field(field: dict, route: str) -> bool:
        if "routes" in field:
            return route in field["routes"]
        if field["id"] in {"usage", "area"}:
            return route in {"buyer", "lessee"}
        return True
    numeric_route_fields = {route: [row["id"] for row in search_fields if route_field(row, route) and row.get("unit")] for route in ROUTES}
    axis_rows = list(csv.DictReader((PACKAGE / "d28-route-axis-coverage.csv").open()))
    scenarios = {row["id"]: row for row in payload["scenarios"]}
    outputs = {row["scenario_id"]: row for result in (development, heldout) for row in result["results"]}
    unit_errors = []
    boundary_samples = []
    amount_routes = set()
    return_routes = set()
    for row in axis_rows:
        if row["axis"] != "unit-basis":
            continue
        route = row["route"]
        ids = [value for value in row["scenario_ids"].split(";") if value]
        if route in {"operator", "charity"}:
            if row["applicable"] != "N/A" or ids or row["oracle_check_axis"] != "N/A" or numeric_route_fields[route]:
                unit_errors.append(route + ": invalid N/A contract")
            continue
        if row["applicable"] != "yes" or not ids:
            unit_errors.append(route + ": missing applicable scenarios")
            continue
        for scenario_id in ids:
            scenario = scenarios[scenario_id]
            if scenario["route"] != route:
                unit_errors.append(route + ": scenario route mismatch")
            has_amount = "budget_max" in scenario["criteria"] or "budget_min" in scenario["criteria"]
            has_return = isinstance(scenario["criteria"].get("return"), dict) and bool(scenario["criteria"]["return"].get("basis"))
            expected_axes = ({"amount"} if has_amount else set()) | ({"returns"} if has_return else set())
            result = outputs[scenario["id"]]
            actual_axes = {check["axis"] for pair in result["oracle"] for check in pair["actual"]["checks"]}
            expected_check_axes = {check["axis"] for pair in result["oracle"] for check in pair["expected"]["checks"]}
            if not expected_axes or not expected_axes <= actual_axes or not expected_axes <= expected_check_axes:
                unit_errors.append(route + ": no real oracle consumer in " + scenario_id)
            if has_amount:
                amount_routes.add(route)
                field = AMOUNT_FIELDS[route]
                values = [item["snapshot"].get(field) for item in payload["opportunities"] if item["route"] == route and item["split"] == scenario["split"]]
                if not values or any(not isinstance(value, dict) or value.get("unit") != {"code": "TOMAN", "version": 1} for value in values):
                    unit_errors.append(route + ": TOMAN@1 missing")
            if has_return:
                return_routes.add(route)
            boundary_samples.append({"route": route, "scenario": scenario["id"], "axes": sorted(expected_axes)})
    checks["evid_it_002_contract_and_oracle_samples"] = (
        not unit_errors and numeric_route_fields["operator"] == [] and numeric_route_fields["charity"] == []
        and amount_routes == {"investor", "fund", "buyer", "lessee", "contractor", "heritage"}
        and return_routes == {"investor", "fund", "heritage"}
    )
    mutated_axis = copy.deepcopy(axis_rows)
    operator = next(row for row in mutated_axis if row["route"] == "operator" and row["axis"] == "unit-basis")
    operator.update({"applicable": "yes", "scenario_ids": "D28-operator-development-02", "oracle_check_axis": "amount|returns"})
    scenario = scenarios["D28-operator-development-02"]
    checks["false_applicable_mutation_rejected"] = not ("budget_max" in scenario["criteria"] or "budget_min" in scenario["criteria"] or isinstance(scenario["criteria"].get("return"), dict))
    details.update({
        "numeric_route_fields": numeric_route_fields, "unit_basis_errors": unit_errors,
        "unit_basis_boundary_samples": boundary_samples,
        "unit_basis_amount_routes": sorted(amount_routes), "unit_basis_return_routes": sorted(return_routes),
    })

    forms = {}
    for name, fields in {
        "d28-relevance-labels.csv": ("relevance_label", "independent_group_rank", "reason", "evidence_fields", "missing_information", "reviewer", "reviewed_at"),
        "d28-critical-review.csv": ("critical_misleading", "missing_important_disclosure", "reason", "evidence_fields", "reviewer", "reviewed_at"),
    }.items():
        rows = list(csv.DictReader((PACKAGE / name).open()))
        forms[name] = len(rows)
        checks[name + "_400_unique_blank"] = len(rows) == 400 and len({(row["scenario_id"], row["opportunity_id"]) for row in rows}) == 400 and all(not row[field] for row in rows for field in fields)
    reviewer = (PACKAGE / "d28-reviewer-inputs.json").read_text()
    checks["reviewer_input_blind"] = not any(f'"{field}"' in reviewer for field in ("score", "coverage", "matching", "system_rank"))
    details["form_counts"] = forms

    matrix = list(csv.DictReader((PACKAGE / "design-slot-matrix.csv").open()))
    targets = [row for row in matrix if (row["row_id"], row["viewport_width"]) in TARGETS]
    checks["evid_it_003_nine_exact_route_state"] = len(targets) == 9 and all(row["classification"] == "capture-needed→new-evidence" and row["route"] == row["evidence_route"] and row["state"] == row["evidence_state"] for row in targets)
    representatives = [row for row in matrix if row["classification"] == "representative-covered"]
    checks["six_remaining_representatives_valid"] = len(representatives) == 6 and all(row["route"] == row["evidence_route"] and row["state"] == row["evidence_state"] and row["representative_contract"] for row in representatives)

    provenance = load(FIX / "runtime-provenance.json")
    source_front = source_fingerprint("frontend")
    source_back = source_fingerprint("backend")
    web_image = docker_json("image", "inspect", "investevidencefix-web:0380bbf")[0]
    backend_image = docker_json("image", "inspect", "investevidencefix-backend:0380bbf")[0]
    web_container = docker_json("inspect", "invest-evidencefix-web-1")[0]
    backend_container = docker_json("inspect", "invest-evidencefix-backend-1")[0]
    build_id = run("docker", "exec", "invest-evidencefix-web-1", "cat", "/app/.next/BUILD_ID")
    backend_runtime = runtime_hashes("invest-evidencefix-backend-1", "find /app -path /app/.venv -prune -o -type f -exec sha256sum {} +")
    backend_runtime_errors = []
    for row in source_back["files"]:
        runtime_path = "/app/" + row["path"].removeprefix("backend/")
        if backend_runtime.get(runtime_path) != row["sha256"]:
            backend_runtime_errors.append(row["path"])
    frontend_runtime = runtime_hashes("invest-evidencefix-web-1", "find /app/.next/static /app/.next/server/app/tools /app/.next/server/app/library -type f -exec sha256sum {} +; sha256sum /app/.next/BUILD_ID /app/server.js")
    recorded_frontend = provenance["runtime"]["frontend_affected_file_hashes"]
    frontend_runtime_errors = sorted(path for path, digest in recorded_frontend.items() if frontend_runtime.get(path) != digest)
    checks["source_runtime_equality"] = (
        source_front["sha256"] == provenance["source"]["frontend_sha256"] == web_image["Config"]["Labels"]["invest.source.frontend.sha256"]
        and source_back["sha256"] == provenance["source"]["backend_sha256"] == backend_image["Config"]["Labels"]["invest.source.backend.sha256"]
        and web_container["Image"] == web_image["Id"] and backend_container["Image"] == backend_image["Id"]
        and build_id == provenance["runtime"]["frontend_build_id"] and not backend_runtime_errors and not frontend_runtime_errors
    )
    captures = {row["evidence_file"]: row for row in provenance["captures"]}
    capture_errors = []
    state_errors = []
    fresh = [row for row in matrix if row["product_evidence"].startswith("docs/experience-complete/tech-evidence-fix-01/design-")]
    for row in fresh:
        name = Path(row["product_evidence"]).name
        capture = captures.get(name)
        metadata_path = FIX / ("capture-" + name.removeprefix("design-").removesuffix(".png") + ".json")
        if not capture or not metadata_path.exists():
            capture_errors.append(name + ": missing metadata/provenance")
            continue
        metadata = load(metadata_path)
        required = ["route", "state", "identity", "synthetic_seed", "product_url", "final_url", "viewport_width", "viewport_height", "browser", "captured_at_utc", "font_condition", "motion_condition"]
        if any(not metadata.get(key) for key in required):
            capture_errors.append(name + ": incomplete conditions")
        if capture["runtime"] != {"frontend_image_id": web_image["Id"], "backend_image_id": backend_image["Id"], "frontend_build_id": build_id}:
            capture_errors.append(name + ": runtime binding mismatch")
        if capture["evidence_sha256"] != sha(FIX / name) or int(metadata["viewport_width"]) != int(row["viewport_width"]):
            capture_errors.append(name + ": hash/viewport mismatch")
        if metadata["route"] != row["evidence_route"] or metadata["state"] != row["evidence_state"]:
            capture_errors.append(name + ": metadata/matrix evidence mismatch")
        if row["route"] != row["evidence_route"] or row["state"] != row["evidence_state"]:
            state_errors.append({"file": name, "row_state": row["state"], "evidence_state": row["evidence_state"]})
    checks["thirteen_capture_provenance_chain"] = len(fresh) == 13 and not capture_errors
    checks["capture_state_matches_matrix"] = not state_errors
    library = [row for row in fresh if row["row_id"] == "DES-035"]
    checks["four_library_from_matching_runtime"] = len(library) == 4 and all(Path(row["product_evidence"]).name in captures for row in library) and not [error for error in capture_errors if "library" in error]
    checks["human_fields_still_blank"] = all(not row["human_verdict"] and not row["specialist_design_approval"] for row in matrix)
    details.update({
        "target_slots": [{"row": row["row_id"], "width": row["viewport_width"], "path": row["product_evidence"]} for row in targets],
        "representatives": [{"row": row["row_id"], "width": row["viewport_width"], "route": row["route"], "state": row["state"]} for row in representatives],
        "capture_errors": capture_errors, "capture_state_errors": state_errors,
        "source_fingerprints": {"frontend": source_front["sha256"], "backend": source_back["sha256"]},
        "runtime": {"frontend_image": web_image["Id"], "backend_image": backend_image["Id"], "build_id": build_id, "backend_runtime_errors": backend_runtime_errors, "frontend_runtime_errors": frontend_runtime_errors},
    })

    replay_path = HERE / "development-replay-results.json"
    if replay_path.exists():
        replay = load(replay_path)
        shipped = {row["scenario_id"]: row for row in development["results"]}
        replay_mismatches = []
        for row in replay["results"]:
            expected = shipped[row["scenario_id"]]
            actual_pairs = {pair["opportunity_id"]: pair["matching"] for pair in row["actual"]}
            expected_pairs = {pair["opportunity_id"]: pair["actual"] for pair in expected["oracle"]}
            if row["top5_ids"] != expected["top5_ids"] or actual_pairs != expected_pairs:
                replay_mismatches.append(row["scenario_id"])
        checks["fresh_development_replay"] = (
            replay["runtime_commit"] == BASE and replay["input_sha256"] == sha(PACKAGE / "d28-inputs.json")
            and replay["counts"] == {"scenarios": 32, "opportunities": 48, "candidate_pairs": 192, "top5_pairs": 160}
            and replay["cursor"] == {"pages": [12, 12, 12, 12], "total_ids": 48, "unique_ids": 48}
            and not replay_mismatches
        )
        details["development_replay_mismatches"] = replay_mismatches

    browser_files = [HERE / f"browser-{name}.json" for name in ("proposal-summary", "foreign-investment-step1", "ma-renewal-step1", "charity-summary")]
    if all(path.exists() for path in browser_files):
        browser_rows = [load(path) for path in browser_files]
        checks["four_unique_browser_routes"] = len({row["route"] for row in browser_rows}) == 4 and all(row["focus"] and row["hit"] and not row["geometry"]["overflow"] and row["geometry"]["fonts"] == "loaded" and row["geometry"]["motion"] for row in browser_rows)
        independent_capture = load(HERE / "independent-capture-provenance.json")
        checks["independent_capture_runtime_bound"] = (
            independent_capture["runtime"] == {"frontend_image_id": web_image["Id"], "backend_image_id": backend_image["Id"], "frontend_build_id": build_id}
            and independent_capture["evidence_sha256"] == sha(HERE / independent_capture["evidence_file"])
            and independent_capture["route"] == "/tools/proposal" and independent_capture["state"] == "step-3: جمع‌بندی راهنمای اولیه"
        )
        details["browser_observations"] = browser_rows

    failed = [name for name, passed in checks.items() if not passed]
    result = {"schema": "invest.tech-evidence-fix.independent-retest@1", "checks": checks, "passed": len(checks) - len(failed), "failed": failed, "details": details}
    (HERE / "independent-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "failed": failed}, ensure_ascii=False))
    # Expected evidence findings do not make the verifier itself fail; integrity/runtime failures do.
    fatal = {"fix_manifest_hashes", "delivery_checkout", "no_product_behavior_diff", "oracle_unchanged", "historical_heldout_untouched", "source_runtime_equality"}
    if fatal & set(failed):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
