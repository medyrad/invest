#!/usr/bin/env python3
"""Replay development against product code/PostgreSQL; expectation is verified separately."""

from __future__ import annotations

import json
import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.core import discovery
from apps.core.models import Opportunity, Review, Submission
from apps.workspace.models import Draft


SOURCE = Path(os.environ["SOURCE_EVIDENCE_DIR"])
OUTPUT = Path(os.environ["OUTPUT_EVIDENCE_DIR"])


def main() -> None:
    payload = json.loads((SOURCE / "d28-inputs.json").read_text())
    rows = [row for row in payload["opportunities"] if row["split"] == "development"]
    scenarios = [row for row in payload["scenarios"] if row["split"] == "development"]
    User = get_user_model()
    owner = User.objects.create_user(mobile="+12025550881")
    admin = User.objects.create_user(mobile="+12025550882", role="admin")
    for row in rows:
        draft = Draft.objects.create(id=row["id"], creator=owner, kind=row["kind"], routes=[row["route"]], raw=row["snapshot"])
        opportunity = Opportunity.objects.create(id=row["id"], draft=draft, synthetic=True)
        revision = Submission.objects.create(
            id=row["revision_id"], opportunity=opportunity, draft_version=1, kind=row["kind"],
            routes=[row["route"]], snapshot=row["snapshot"], submitted_by=owner,
        )
        opportunity.public_revision = revision
        opportunity.save(update_fields=["public_revision"])
        Review.objects.create(
            submission=revision, actor=admin, decision="approved", reason="بازپخش مستقل مصنوعی",
            created_at=timezone.now(), public_files=[],
        )
    results = []
    for scenario in scenarios:
        first = discovery.listing(dict(scenario["criteria"]))
        second = discovery.listing(dict(scenario["criteria"]))
        assert first["total"] == 6 and len(first["items"]) == 6
        assert [item["id"] for item in first["items"]] == [item["id"] for item in second["items"]]
        results.append({
            "scenario_id": scenario["id"],
            "candidate_count": first["total"],
            "top5_ids": [item["id"] for item in first["items"][:5]],
            "actual": [{"opportunity_id": item["id"], "matching": item["matching"]} for item in first["items"]],
        })
    page = discovery.listing({})
    cursor_ids = [item["id"] for item in page["items"]]
    pages = [len(page["items"])]
    while page["next"]:
        page = discovery.listing({}, cursor=page["next"])
        pages.append(len(page["items"]))
        cursor_ids.extend(item["id"] for item in page["items"])
    output = {
        "schema": "invest.d28.independent-development-replay@1",
        "runtime_commit": os.environ["RUNTIME_SOURCE"],
        "counts": {"scenarios": len(results), "opportunities": len(rows), "candidate_pairs": sum(r["candidate_count"] for r in results), "top5_pairs": sum(len(r["top5_ids"]) for r in results)},
        "cursor": {"pages": pages, "total_ids": len(cursor_ids), "unique_ids": len(set(cursor_ids))},
        "results": results,
    }
    (OUTPUT / "development-replay-results.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output["counts"], ensure_ascii=False))


main()
