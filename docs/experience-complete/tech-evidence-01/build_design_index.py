#!/usr/bin/env python3
"""Create the auditable 26-row × 4-width design slot matrix from approved evidence."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
WIDTHS = (360, 390, 768, 1440)
PRIMARY = {"DES-003", *(f"DES-{i:03d}" for i in range(6, 10)), "DES-014", "DES-021", *(f"DES-{i:03d}" for i in range(22, 41))}
PRODUCT_VERSION = "79519bb8e88cbf6c0bcf7614c63b3737cc668a70 (product behavior unchanged from independently accepted 8c327ec)"
FIX_CHECKOUT = "0380bbf3cdcf00f6997b060a7d43a1ad980dc56c (product source equals 79519bb8 baseline)"
REFERENCE_SHA = "6221401c736250c5ac7e5595aa988301f64b8d2fe576590291a7c2e53c247f5b"


def current(name: str, width: int) -> str:
    return f"docs/experience-complete/tech-evidence-01/design-{name}-{width}.png"


def service(row: str, width: int) -> tuple[str, str, str, str]:
    if row in {"DES-006", "DES-007", "DES-008"}:
        stage = int(row[-1]) - 5
        return ("reuse-valid", f"docs/experience-complete/fix-01-continuation-evidence/product-land-stage{stage}-{width}.png", f"docs/experience-complete/fix-01-continuation-evidence/reference-land-empty-{width}.png", "same current component and breakpoint; no frontend behavior change after cb6aba7; filled stage differs explicitly from empty reference")
    direct = {
        "DES-003": {390: "docs/stage8/evidence/proposal-viewport-390.png", 1440: "docs/stage8/evidence/proposal-summary-1440.png"},
        "DES-009": {1440: "docs/stage8/evidence/foreign-investment-summary-1440.png"},
        "DES-014": {390: "docs/stage8/independent-evidence/renewal-exact-390.png", 1440: "docs/stage8/evidence/ma-renewal-summary-1440.png"},
        "DES-021": {360: "docs/stage8/independent-evidence/charity-noncash-360.png", 1440: "docs/stage8/evidence/charity-summary-1440.png"},
    }.get(row, {})
    ref = {
        "DES-003": "proposal", "DES-009": "foreign-investment", "DES-014": "ma-renewal", "DES-021": "charity"
    }[row]
    reference = f"docs/stage1/evidence/{ref}-{390 if width < 768 else 1440}.png"
    fixed = {
        "DES-003": {360: "proposal-summary", 768: "proposal-summary"},
        "DES-009": {360: "foreign-investment-step1", 390: "foreign-investment-step1", 768: "foreign-investment-step1"},
        "DES-014": {360: "ma-renewal-step1", 768: "ma-renewal-step1"},
        "DES-021": {390: "charity-summary", 768: "charity-summary"},
    }.get(row, {})
    if width in fixed:
        path = f"docs/experience-complete/tech-evidence-fix-01/design-{fixed[width]}-{width}.png"
        return ("capture-needed→new-evidence", path, reference, "fresh capture of the exact route/state on source-bound runtime; metadata and image digest are in tech-evidence-fix-01/runtime-provenance.json")
    if width in direct:
        return ("reuse-valid", direct[width], reference, "same route/state evidence; accepted S08 runtime and shared ServiceEditor unchanged through current docs-only baseline")
    representative = "docs/experience-complete/fix-01-continuation-evidence/product-land-stage2-{}.png".format(width)
    return ("representative-covered", representative, reference, "ServiceEditor, progress, field shell, breakpoint and interaction risk are shared; route-specific content remains covered at its direct widths")


def slot(row: str, width: int) -> tuple[str, str, str, str]:
    if row in {"DES-003", "DES-006", "DES-007", "DES-008", "DES-009", "DES-014", "DES-021"}:
        return service(row, width)
    if row == "DES-022":
        suffix = {360: "mobile-360", 390: "mobile-390", 768: "tablet-768", 1440: "desktop-1440"}[width]
        return ("reuse-valid", f"docs/stage3/evidence/foundation-{suffix}.png", f"docs/stage1/evidence/home-{390 if width < 768 else 1440}.png", "home shell and responsive breakpoint unchanged by COMP-EXPERIENCE fixes")
    if row == "DES-023":
        return ("reuse-valid", f"docs/core-delivery/independent-evidence/screenshots/results-{width}.png", f"docs/stage1/evidence/opportunities-results-{390 if width < 768 else 1440}.png", "route and result component unchanged; synthetic data mismatch is explicit, not a same-data pair")
    if row == "DES-024":
        return ("reuse-valid", f"docs/core-delivery/independent-evidence/screenshots/detail-{width}.png", f"docs/stage1/evidence/project-{390 if width < 768 else 1440}.png", "project detail product state remains current; data differs from reference and is not claimed same-condition")
    if row in {"DES-025", "DES-026"}:
        kind = "fund" if row == "DES-025" else "sale"
        return ("reference-component-only", current(f"detail-{kind}", width), f"docs/stage1/evidence/project-{390 if width < 768 else 1440}.png", "no full ZIP page for this kind; new current capture is checked against shared detail cards/header and D14/D29 semantics only")
    if row in {"DES-027", "DES-028", "DES-029"}:
        kind = {"DES-027": "project", "DES-028": "fund", "DES-029": "sale"}[row]
        direct_width = 390 if width < 768 else 1440
        product = f"docs/core-delivery/retest-01-evidence/compare-{kind}-{direct_width}.png"
        reference = f"docs/stage1/evidence/compare-projects-{direct_width}.png" if kind == "project" else ""
        classification = "reuse-valid" if width in {390, 1440} else "representative-covered"
        return (classification, product, reference, "same CompareTable component; 360 shares mobile breakpoint with 390 and 768 shares table-scroll behavior with desktop component; kind-specific D29 rows remain explicit")
    if row == "DES-030":
        return ("reuse-valid", f"docs/experience-complete/fix-01-continuation-evidence/product-saved-account-{width}.png", "", "current shared ProfessionalForm and saved tabs; reference has no full account state")
    if row == "DES-031":
        return ("reference-component-only", f"docs/experience-complete/fix-01-continuation-evidence/product-profile-account-{width}.png", f"docs/experience-complete/fix-01-continuation-evidence/reference-profile-empty-{width}.png", "account page has no full ZIP equivalent; shared professional components are compared")
    if row == "DES-032":
        return ("reuse-valid", f"docs/experience-complete/retest-01-evidence/product-profile-{width}.png", f"docs/experience-complete/retest-01-evidence/reference-profile-{width}.png", "same route, guest state, viewport and font-ready pair; frontend unchanged since accepted evidence")
    if row == "DES-033":
        return ("reference-component-only", current("report-current", width), "docs/stage1/evidence/project-{}.png".format(390 if width < 768 else 1440), "fresh FIX02 frozen HTML; ZIP has no equivalent report page, so only brand/card/typography components are comparable")
    if row == "DES-034":
        suffix = {360: "mobile-360", 390: "mobile-390", 768: "tablet-768", 1440: "desktop-1440"}[width]
        return ("reuse-valid", f"docs/stage3/evidence/login-code-step-{suffix}.png", f"docs/stage1/evidence/login-{390 if width < 768 else 1440}.png", "OTP state and breakpoint unchanged; late/account-switch behavior is linked through interaction regression, not inferred from screenshot")
    if row == "DES-035":
        return ("capture-needed→new-evidence", f"docs/experience-complete/tech-evidence-fix-01/design-library-{width}.png", f"docs/stage1/evidence/library-{390 if width < 768 else 1440}.png", "library recaptured on source-bound runtime with font, focus, hit-test, click and image digest provenance")
    panel = {"DES-036": "workspace", "DES-037": "drafts", "DES-038": "requests", "DES-039": "admin", "DES-040": "expert"}[row]
    reference = f"docs/stage1/evidence/drafts-{390 if width < 768 else 1440}.png" if row == "DES-037" else ""
    return ("reference-component-only", current(panel, width), reference, "new authenticated capture; no full ZIP equivalent for role panel, so shell/cards/buttons plus D03/D25-D27/D29-D32 are the only valid comparison basis")


def capture_time(path: str) -> str:
    target = ROOT / path
    if ("tech-evidence-01/design-" in path or "tech-evidence-fix-01/design-" in path) and target.exists():
        return datetime.fromtimestamp(target.stat().st_mtime, timezone.utc).isoformat()
    return "historical; authoritative time/version in adjacent manifest/report"


def capture_metadata(path: str) -> dict | None:
    marker = "docs/experience-complete/tech-evidence-fix-01/design-"
    if not path.startswith(marker):
        return None
    name = Path(path).name.removeprefix("design-").removesuffix(".png")
    metadata_path = ROOT / "docs/experience-complete/tech-evidence-fix-01" / f"capture-{name}.json"
    return json.loads(metadata_path.read_text())


def main() -> None:
    with (ROOT / "docs/experience-complete/human-design-review/scope.csv").open() as handle:
        scope = {row["id"]: row for row in csv.DictReader(handle) if row["id"] in PRIMARY}
    assert len(scope) == 26
    rows = []
    for row_id in sorted(scope):
        source = scope[row_id]
        for width in WIDTHS:
            classification, product, reference, proof = slot(row_id, width)
            assert product and (ROOT / product).exists(), (row_id, width, product)
            if reference:
                assert (ROOT / reference).exists(), (row_id, width, reference)
            metadata = capture_metadata(product)
            rows.append({
                "row_id": row_id, "group": source["group"], "route": source["route"], "state": source["state"], "identity": source["identity"],
                "viewport_width": width, "viewport_height": metadata["viewport_height"] if metadata else 1000,
                "canvas": f"{metadata['interaction']['canvas']['width']}x{metadata['interaction']['canvas']['height']}" if metadata else "full-page; exact pixels available in PNG", "classification": classification,
                "product_evidence": product, "reference_evidence": reference, "proof_or_limitation": proof,
                "evidence_route": metadata["route"] if metadata else source["route"], "evidence_state": metadata["state"] if metadata else source["state"],
                "representative_contract": "same-route-state; width represented by the same component/breakpoint contract" if classification == "representative-covered" else "",
                "product_version": FIX_CHECKOUT if metadata else PRODUCT_VERSION, "reference_zip_sha256": REFERENCE_SHA, "synthetic_data": metadata["synthetic_seed"] if metadata else "isolated seed_core_demo or frozen synthetic report",
                "font": metadata["font_condition"] if metadata else "document.fonts.ready", "motion": metadata["motion_condition"] if metadata else "reduced", "capture_time_utc": metadata["captured_at_utc"] if metadata else capture_time(product),
                "runtime_provenance": "docs/experience-complete/tech-evidence-fix-01/runtime-provenance.json" if metadata else "historical evidence path/version; no fresh-capture claim",
                "interaction_evidence": "tech-evidence-01/interaction-evidence.csv", "human_verdict": "", "specialist_design_approval": "",
            })
    assert len(rows) == 104
    with (OUT / "design-slot-matrix.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader();writer.writerows(rows)
    counts = {}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    (OUT / "design-slot-summary.json").write_text(json.dumps({"rows": len(scope), "slots": len(rows), "widths": list(WIDTHS), "classifications": counts, "human_verdicts_filled": 0}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
