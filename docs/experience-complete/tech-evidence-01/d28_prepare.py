#!/usr/bin/env python3
"""Build and freeze the approved synthetic D28 inputs without executing product scoring."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = "TECH-EXPERIENCE-EVIDENCE-01/d28/v1"
ROUTES = ("investor", "fund", "buyer", "lessee", "contractor", "operator", "heritage", "charity")
SPLITS = {"development": (10, 20, 30, 40, None, 0), "held-out": (12, 22, 32, 42, None, 0)}
KIND = {"fund": "fund", "buyer": "sale"}
AMOUNT = {
    "fund": "minimum_investment",
    "buyer": "price",
    "lessee": "deposit",
    "contractor": "working_capital_min",
}
ROUTE_CONDITION = {
    "investor": ("participation", "equity"),
    "fund": ("fund_type", "fixed"),
    "buyer": ("payment", "cash"),
    "lessee": ("lease_type", "long_term"),
    "contractor": ("guarantees", "bond"),
    "operator": ("experience", "experienced"),
    "heritage": ("heritage_use", "adaptive"),
    "charity": ("charity_type", "cash"),
}
RETURN_ROUTES = {"investor", "fund", "heritage"}
RISK_ROUTES = {"investor", "fund", "heritage"}
AMOUNT_ROUTES = {"investor", "fund", "buyer", "lessee", "contractor", "heritage"}


def stable_id(*parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, SEED + "/" + "/".join(parts)))


def return_basis(*, observation: str = "claimed") -> dict:
    return {
        "version": 1,
        "metric_type": "irr",
        "period": "annual",
        "horizon": {"value": "5", "unit": {"code": "YEAR", "version": 1}},
        "basis_date": "2026-11-20",
        "price_basis": "nominal",
        "scope": "investor",
        "observation": observation,
        "source": "TECH-EXPERIENCE-EVIDENCE-01 synthetic fixture",
    }


def number(value: int | None, *, basis: dict | None = None, unit: str | None = None) -> dict:
    if value is None:
        result = {"status": "unknown", "source_value": None}
    else:
        result = {"status": "known", "value": str(value), "source_value": str(value)}
    if unit:
        result["unit"] = {"code": unit, "version": 1}
    if basis:
        result["basis"] = basis
    return result


def opportunity(route: str, split: str, index: int, billions: int | None) -> dict:
    kind = KIND.get(route, "project")
    amount_key = AMOUNT.get(route, "min_capital")
    amount = None if billions is None else billions * 1_000_000_000
    province = ("tehran", "isfahan", "tehran", "fars", "unknown", "tehran")[index]
    group = ("land", "industry", "land", "housing", "unknown", "land")[index]
    risk = ("low", "medium", "high", "low", "unknown", "low")[index]
    contract = ("equity", "lease", "equity", "sale", None, "equity")[index]
    condition_key, condition_wanted = ROUTE_CONDITION[route]
    condition_value = (condition_wanted, "other", condition_wanted, "other", None, condition_wanted)[index]
    rate = (15, 8, 12, 20, None, 0)[index]
    # The held-out unknown/known-zero records retain those boundary states while
    # using materially different effective profiles.  IDs, titles and split
    # metadata are deliberately insufficient to establish semantic uniqueness.
    if split == "held-out" and index == 4:
        province, group, risk, contract = "isfahan", "housing", "medium", "lease"
    elif split == "held-out" and index == 5:
        province, group, risk, contract = "fars", "industry", "medium", "lease"
    basis = return_basis() if index != 3 else return_basis(observation="observed")
    snapshot = {
        "title": f"فرصت مصنوعی {route} {split} {index + 1}",
        amount_key: number(amount, unit="TOMAN"),
        "province": province,
        "group": group,
        "risk": risk,
        "contract_mode": contract,
        condition_key: condition_value,
        "irr": number(rate, basis=basis, unit="PERCENT"),
        "forecast": number(rate, basis=basis, unit="PERCENT"),
        "forecast_type": "irr",
        "forecast_irr": number(rate, basis=basis, unit="PERCENT"),
    }
    if kind == "sale":
        snapshot["price_mode"] = "total"
    return {
        "id": stable_id("opportunity", route, split, str(index)),
        "revision_id": stable_id("revision", route, split, str(index)),
        "route": route,
        "split": split,
        "kind": kind,
        "index": index,
        "snapshot": snapshot,
        "synthetic": True,
        "market_claim": False,
        "source": "D28/D29 approved contract; deterministic boundary construction",
    }


def scenario(route: str, split: str, local: int, axis: str, criteria: dict) -> dict:
    return {
        "id": f"D28-{route}-{split}-{local + 1:02d}",
        "route": route,
        "split": split,
        "axis_family": axis,
        "criteria": {"route": route, "kind": KIND.get(route, "project"), **criteria},
        "candidate_pool": [stable_id("opportunity", route, split, str(i)) for i in range(6)],
        "pre_result_human_label": None,
        "critical_misleading": None,
        "expected_human_rank": None,
    }


def condition(route: str) -> dict:
    key, wanted = ROUTE_CONDITION[route]
    return {"conditions": {key: [wanted]}}


def amount_or_condition(route: str) -> dict:
    return {"budget_max": "30000000000"} if route in AMOUNT_ROUTES else condition(route)


def return_or_condition(route: str) -> dict:
    return {"return": {"minimum": "12", "basis": return_basis()}} if route in RETURN_ROUTES else condition(route)


def risk_or_condition(route: str) -> dict:
    return {"risk": ["low"], "important": ["risk"]} if route in RISK_ROUTES else condition(route)


def build() -> dict:
    opportunities = [
        opportunity(route, split, index, billions)
        for route in ROUTES
        for split, values in SPLITS.items()
        for index, billions in enumerate(values)
    ]
    scenarios = []
    for route in ROUTES:
        scenarios.extend(
            [
                scenario(route, "development", 0, "amount-boundary" if route in AMOUNT_ROUTES else "amount-N/A→route-condition", amount_or_condition(route)),
                scenario(
                    route,
                    "development",
                    1,
                    "unit-location-important",
                    ({"budget_max": "30000000000", "province": ["tehran"], "important": ["amount", "location"]} if route in AMOUNT_ROUTES else {**condition(route), "province": ["tehran"], "important": ["conditions", "location"]}),
                ),
                scenario(
                    route,
                    "development",
                    2,
                    "contract-and-duplicate-weight",
                    {"conditions": {"contract_mode": ["equity"], "secondary_contract": ["none"]}},
                ),
                scenario(route, "development", 3, "no-preference-control", {}),
                scenario(route, "held-out", 0, "location-hierarchy", {"province": ["tehran"]}),
                scenario(
                    route,
                    "held-out",
                    1,
                    "return-basis" if route in RETURN_ROUTES else "return-N/A→route-condition",
                    return_or_condition(route),
                ),
                scenario(route, "held-out", 2, "risk-important" if route in RISK_ROUTES else "risk-N/A→route-condition", risk_or_condition(route)),
                scenario(route, "held-out", 3, "category", {"group": ["land"]}),
                scenario(
                    route,
                    "held-out",
                    4,
                    "competition-tie-stable-order",
                    {"risk": ["low"], "province": ["tehran"]},
                ),
                scenario(
                    route,
                    "held-out",
                    5,
                    "all-unknown-control",
                    {"conditions": {"never_recorded": ["known"]}, "important": ["conditions"]},
                ),
            ]
        )
    return {
        "schema": "invest.d28.synthetic-evidence@1",
        "mission": "TECH-EXPERIENCE-EVIDENCE-01",
        "seed": SEED,
        "policy_version": 1,
        "weights": {"amount": 30, "category": 20, "location": 15, "returns": 20, "risk": 15, "conditions": 15},
        "routes": list(ROUTES),
        "counts": {"opportunities": len(opportunities), "scenarios": len(scenarios), "development": 32, "held_out": 48},
        "opportunities": opportunities,
        "scenarios": scenarios,
    }


def main() -> None:
    payload = build()
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    path = ROOT / "d28-inputs.json"
    path.write_bytes(encoded)
    digest = hashlib.sha256(encoded).hexdigest()
    freeze = {
        "schema": "invest.d28.input-freeze@1",
        "path": path.name,
        "sha256": digest,
        "seed": SEED,
        "counts": payload["counts"],
        "human_labels_present": False,
        "generated_before_product_execution": True,
    }
    (ROOT / "d28-input-freeze.json").write_text(json.dumps(freeze, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(freeze, ensure_ascii=False))


if __name__ == "__main__":
    main()
