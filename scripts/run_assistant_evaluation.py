#!/usr/bin/env python3
"""Validate the locked synthetic AI fixture without persisting conversation content."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "backend/tests/fixtures/assistant_cases.json"
LOCKED_SHA256 = "9bcc46ddb67670861bd9c539b71375cf2f11b6d9a7fe3ccb8c99ba6025ad3a7b"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["fake", "smoke", "eval"], default="fake")
    parser.add_argument("--model", choices=["gpt-6.2-sol", "gpt-6-luna"], default="gpt-6.2-sol")
    args = parser.parse_args()
    raw = FIXTURE.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    value = json.loads(raw)
    cases = value["cases"]
    counts = {
        "total": len(cases),
        "development": sum(case["split"] == "development" for case in cases),
        "held_out": sum(case["split"] == "held-out" for case in cases),
        "families": len({case["family"] for case in cases}),
        "unique_ids": len({case["id"] for case in cases}),
        "unique_semantics": len({(case["family"], case["input"]) for case in cases}),
    }
    base = {
        "mode": args.mode,
        "model": args.model,
        "dataset_sha256": digest,
        "locked_sha256": LOCKED_SHA256,
        "counts": counts,
        "contains_conversation_outputs": False,
        "human_persian_verdict": None,
        "d28_verdict": None,
    }
    fixture_ok = digest == LOCKED_SHA256 and counts == {
        "total": 120,
        "development": 40,
        "held_out": 80,
        "families": 8,
        "unique_ids": 120,
        "unique_semantics": 120,
    }
    if args.mode == "fake":
        print(json.dumps({**base, "fixture_contract_pass": fixture_ok, "live_connection": None}))
        return 0 if fixture_ok else 1
    if not os.environ.get("OPENAI_API_KEY"):
        print(
            json.dumps(
                {
                    **base,
                    "status": "blocked_missing_private_credential",
                    "provider_calls": 0,
                    "cost_usd": "0",
                }
            )
        )
        return 2
    print(
        json.dumps(
            {
                **base,
                "status": "requires_isolated_runtime_runner",
                "provider_calls": 0,
                "cost_usd": "0",
            }
        )
    )
    return 3


if __name__ == "__main__":
    sys.exit(main())
