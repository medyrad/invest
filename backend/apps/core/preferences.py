"""Explicit source filter → publisher-field mapping, policy D28@1.
User cash-flow/basis-free wishes have no fabricated publisher counterpart.
"""

from decimal import Decimal

from apps.catalog.values import ValueErrorDetail, parse_number
from apps.workspace.schema import Fault

RULES = {
    "subtypes": ("subtype", "category", "eq", None),
    "phase": ("phase", "category", "eq", None),
    "owner": ("owner_sector", "category", "eq", None),
    "horizon": ("payback_years", "returns", "max", "YEAR"),
    "lockup": ("lockup_months", "returns", "max", "MONTH"),
    "firstIncome": ("first_income_months", "returns", "max", "MONTH"),
    "income": ("income", "returns", "eq", None),
    "fundType": ("fund_type", "category", "eq", None),
    "saleCategory": ("category", "category", "eq", None),
    "usage": ("usage", "category", "eq", None),
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
    "general": ("general_conditions", "conditions", "eq", None),
    "special": ("special_conditions", "conditions", "eq", None),
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


def evaluate(s, route, preferences):
    f = s.snapshot
    for key, wanted in preferences.items():
        if wanted in [None, "", "any", False] or wanted == []:
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
            if wanted not in ["no", "undecided"]:
                yield "risk", "unknown", "تضمین بانکی تا بررسی سند و دامنه احراز نمی‌شود."
            continue
        if key not in RULES:
            # Subjective applicant descriptions or source-only services cannot be inferred.
            yield (
                ("amount" if key in BUDGET_INFO else "conditions"),
                "unknown",
                "برای ترجیح «" + key + "» داده هم‌معنای بررسی‌شده وجود ندارد.",
            )
            continue
        field, axis, op, unit = RULES[key]
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
                or v["unit"]["code"] != unit
                or (
                    unit in ["YEAR", "MONTH"]
                    and v.get("basis", {}).get("start_basis") in [None, "", "unspecified"]
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
            ok = have >= n if op == "min" else have <= n
        else:
            choices = wanted if isinstance(wanted, list) else [str(wanted)]
            ok = any(x in choices for x in v) if isinstance(v, list) else v in choices
        yield (
            axis,
            "met" if ok else "unmet",
            "ترجیح «" + key + "» با فیلد «" + field + "»؛ صرفاً تطبیق داده، نه احتمال سود.",
        )
