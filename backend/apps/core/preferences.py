"""Explicit source filter → publisher-field mapping, policy D28@1.
User cash-flow/basis-free wishes have no fabricated publisher counterpart.
"""

import json
from decimal import Decimal
from pathlib import Path

from apps.catalog.values import ValueErrorDetail, parse_number
from apps.workspace.schema import Fault

RULES = {
    "subtypes": ("subtype", "category", "eq", None),
    "phase": ("phase", "category", "eq", None),
    "owner": ("sector", "category", "eq", None),
    "horizon": ("payback_years", "returns", "max", "YEAR"),
    "lockup": ("lockup_months", "returns", "max", "MONTH"),
    "firstIncome": ("first_income_months", "returns", "max", "MONTH"),
    "income": ("income", "returns", "eq", None),
    "fundType": ("fund_type", "category", "eq", None),
    "saleCategory": ("category", "category", "eq", None),
    "usage": ("usage", "category", "eq", None),
    "workingCapital": ("working_capital_min", "conditions", "max", "BILLION_TOMAN"),
    "guarantees": ("accepted_guarantees", "conditions", "eq", None),
    "lumpBudget": ("lump_rent", "amount", "max", "BILLION_TOMAN"),
    "payout": ("payout", "returns", "eq", None),
    "intervention": ("interventions", "conditions", "eq", None),
    "shareMin": ("partner_share", "conditions", "min", "SHARE_PERCENT"),
    "governmentMin": ("government_share", "conditions", "min", "SHARE_PERCENT"),
    "executionMin": ("execution_months", "conditions", "min", "MONTH"),
    "settlement": ("partnership_settlements", "conditions", "eq", None),
    "payment": ("sale_payments", "conditions", "eq", None),
    "right": ("transfer_rights", "conditions", "eq", None),
    "leaseType": ("lease_types", "conditions", "eq", None),
    "leasePayment": ("lease_payments", "conditions", "eq", None),
    "leaseRent": ("monthly_rent", "amount", "max", "MILLION_TOMAN"),
    "leaseYears": ("duration_years", "conditions", "min", "YEAR"),
    "heritageReturn": ("heritage_returns", "conditions", "eq", None),
    "heritageUse": ("heritage_uses", "conditions", "eq", None),
    "heritageYears": ("heritage_years", "conditions", "min", "YEAR"),
    "heritagePayment": ("heritage_payments", "conditions", "eq", None),
    "cities": ("city", "location", "eq", None),
    "neighborhood": ("neighborhood", "location", "eq", None),
    "risk": ("risk", "risk", "eq", None),
    "occupied": ("rights_occupancy", "conditions", "eq", None),
    "renewal": ("rights_renewal", "conditions", "eq", None),
    "thirdPartyRights": ("rights_claims", "conditions", "eq", None),
}
RETURN_UNSPECIFIED = {"irrMin", "fundReturnMin", "irrBasis", "irrPrice"}
BUDGET_INFO = {
    "downPayment",
    "installmentMonths",
    "installmentBudget",
    "lumpBudget",
    "offsetValue",
    "offsetDescription",
    "saleOffsetValue",
    "saleOffsetDescription",
    "funding",
    "workingCapital",
}


SEARCH_FIELDS = {
    f["id"]: f for f in json.loads(Path(__file__).with_name("search_fields.json").read_text())
}


def active_preferences(route, preferences):
    def enabled(key):
        f = SEARCH_FIELDS.get(key)
        if not f:
            return False
        if f.get("routes") and route and route not in f["routes"]:
            return False
        if not f.get("routes") and f.get("section") == "location" and route == "fund":
            return False
        if key in ["usage", "area"] and route not in ["buyer", "lessee"]:
            return False
        when = f.get("showWhen")
        if when:
            parent = when["field"]
            v = preferences.get(parent)
            if not enabled(parent):
                return False
            if when.get("filled"):
                return v is not None and v != 0
            if "in" in when:
                return any(x in when["in"] for x in v) if isinstance(v, list) else v in when["in"]
        return True

    return {k: v for k, v in preferences.items() if enabled(k)}


def evaluate(s, route, preferences, groups=None):
    f = s.snapshot
    for key, wanted in active_preferences(route, preferences).items():
        if (
            wanted is None
            or wanted is False
            or wanted == []
            or (isinstance(wanted, str) and wanted in ["", "any"])
        ):
            continue
        if not isinstance(wanted, (str, int, float, bool, list)) or (
            isinstance(wanted, list) and any(not isinstance(x, (str, int)) for x in wanted)
        ):
            raise Fault("ترجیح معتبر نیست.", field=key)
        if key in ["strictLocation", "keyword"]:
            continue
        if key in ["cities", "neighborhood"] and (
            preferences.get("neighborhood") if key == "cities" else False
        ):
            continue
        if key in RETURN_UNSPECIFIED:
            # Partial source controls are not a full ReturnMetric basis.
            if key in ["irrMin", "fundReturnMin"]:
                yield "returns", "unknown", "حد بازده بدون مبنای کامل قابل تطبیق نیست."
            continue
        if key == "bankGuarantee":
            if wanted in ["no", "undecided"]:
                continue
            from .publication import bank_verified

            if not bank_verified(s):
                yield "risk", "unknown", "تضمین بانکی تا بررسی مستقل سند و دامنه احراز نمی‌شود."
            else:
                parts = [f.get("bank_principal")] + (
                    [f.get("bank_profit")] if wanted == "both" else []
                )
                yield (
                    "risk",
                    "unknown"
                    if any(x not in ["yes", "no"] for x in parts)
                    else "met"
                    if all(x == "yes" for x in parts)
                    else "unmet",
                    "سند و دامنه تضمین بررسی شده؛ تضمین بازده سرمایه‌گذاری نیست.",
                )
            continue
        if key == "area":
            if s.kind != "sale":
                yield "category", "unknown", "مساحت عرصه برای این نوع داده قابل مقایسه ندارد."
                continue
            field = (
                "land_area"
                if f.get("category") == "property"
                else "area"
                if f.get("category") == "land"
                else None
            )
            v = f.get(field) if field else None
            if not isinstance(wanted, list) or len(wanted) != 2:
                raise Fault("بازه مساحت معتبر نیست.")
            if not isinstance(v, dict) or v.get("status") != "known":
                yield "category", "unknown", "مساحت عرصه اعلام نشده است."
                continue
            try:
                lo, hi = (parse_number(str(x)) for x in wanted)
            except ValueErrorDetail as exc:
                raise Fault(exc.message, field=key) from exc
            yield (
                "category",
                "met" if lo <= Decimal(v["value"]) <= hi else "unmet",
                "مساحت عرصه؛ مساحت اعیان جایگزین عرصه نیست.",
            )
            continue
        if key not in RULES:
            # Applicant descriptions and future-service answers remain context, not evidence.
            continue
        field, axis, op, unit = RULES[key]
        if key == "settlement" and route == "contractor":
            field = "contractor_settlements"
        if key == "lumpBudget" and preferences.get("leasePayment") != "lump":
            continue
        v = f.get(field)
        if field == "subtype" and isinstance(v, str):
            v = v.split(".")[-1]
        if v is None or (isinstance(v, str) and v in ["unknown", "not_applicable", ""]):
            yield axis, "unknown", "داده «" + field + "» اعلام نشده است."
            continue
        if op in ["min", "max"]:
            if (
                not isinstance(v, dict)
                or v.get("status") != "known"
                or (v["unit"]["code"] != unit and v.get("base_unit") != "TOMAN")
                or (
                    unit in ["YEAR", "MONTH", "DAY"]
                    and (
                        v.get("basis", {}).get("start_basis") in [None, "", "unspecified"]
                        or not isinstance(preferences.get("basis:" + key), str)
                        or preferences.get("basis:" + key) != v.get("basis", {}).get("start_basis")
                    )
                )
            ):
                yield axis, "unknown", "واحد یا مبنای «" + field + "» قابل مقایسه نیست."
                continue
            try:
                n = parse_number(str(wanted))
            except ValueErrorDetail as e:
                raise Fault(e.message, field=key) from e
            # Compare source units only; no guessed month/day or FX conversion.
            have = Decimal(v["source_value"])
            if v.get("base_unit") == "TOMAN":
                from apps.catalog.values import exact_product

                have = Decimal(v["value"])
                n = exact_product(
                    n, Decimal("1000000000") if unit == "BILLION_TOMAN" else Decimal("1000000")
                )
            ok = have >= n if op == "min" else have <= n
        else:
            choices = wanted if isinstance(wanted, list) else [str(wanted)]
            ok = any(x in choices for x in v) if isinstance(v, list) else v in choices
            if key == "subtypes" and groups:
                ok = ok and f.get("group") in groups
            if key == "neighborhood" and isinstance(v, str):
                ok = any(str(x).casefold() in v.casefold() for x in choices)
            if key == "risk":
                ranks = {"low": 1, "medium": 2, "high": 3}
                if v not in ranks or any(x not in ranks for x in choices):
                    yield axis, "unknown", "مبنای ریسک اعلام نشده است."
                    continue
                ok = any(ranks[v] <= ranks[x] for x in choices)
        yield (
            axis,
            "met" if ok else "unmet",
            "ترجیح «" + key + "» با فیلد «" + field + "»؛ صرفاً تطبیق داده، نه احتمال سود.",
        )
