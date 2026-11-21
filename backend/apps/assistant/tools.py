import re

from apps.catalog.models import Province
from apps.core import discovery
from apps.core.publication import get_op
from apps.workspace.schema import Fault

TOOL_NAMES = {
    "normalize_criteria",
    "search_public_opportunities",
    "get_public_opportunity",
    "compare_same_kind",
}
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
ROUTES = {
    "صندوق": ("fund", "fund"),
    "خرید": ("sale", "buyer"),
    "فروش": ("sale", "buyer"),
    "اجاره": ("project", "lessee"),
    "مرمت": ("project", "heritage"),
    "پیمانکار": ("project", "contractor"),
    "خیریه": ("project", "charity"),
    "بهره بردار": ("project", "operator"),
    "بهره‌بردار": ("project", "operator"),
    "سرمایه": ("project", "investor"),
}


def normalize(text, supplied=None):
    if not isinstance(text, str) or not text.strip() or len(text) > 4000 or "\0" in text:
        raise Fault("متن درخواست معتبر نیست.")
    value = text.translate(PERSIAN_DIGITS).strip()
    criteria = dict(supplied or {})
    if supplied is not None:
        discovery.criteria(criteria)
    for word, (kind, route) in ROUTES.items():
        if word in value:
            criteria.update({"kind": kind, "route": route})
            break
    ambiguities = []
    if not criteria.get("route"):
        ambiguities.append("مسیر سرمایه‌گذاری، صندوق، خرید، اجاره یا همکاری را مشخص کنید.")
    maximum = re.search(
        r"(?:تا|حداکثر)\s*([0-9]+(?:[./][0-9]+)?)\s*(میلیون|میلیارد)\s*(?:تومان)?", value
    )
    minimum = re.search(
        r"(?:از|حداقل)\s*([0-9]+(?:[./][0-9]+)?)\s*(میلیون|میلیارد)\s*(?:تومان)?", value
    )
    amount = maximum or minimum
    if amount:
        raw = amount.group(1).replace("/", ".")
        factor = 1_000_000 if amount.group(2) == "میلیون" else 1_000_000_000
        from decimal import Decimal

        criteria["budget_max" if maximum else "budget_min"] = str(Decimal(raw) * factor)
    elif re.search(r"\b[0-9]+\b", value):
        ambiguities.append("واحد مبلغ یا معنای عدد را مشخص کنید.")
    elif "بودجه" in value and "اصلاح" in value:
        ambiguities.append("مقدار و واحد بودجه تازه را مشخص کنید.")
    percent = re.search(r"([0-9]+(?:[./][0-9]+)?)\s*٪", value)
    if percent and not any(x in value for x in ("سالانه", "ماهانه", "IRR", "بازده ساده")):
        ambiguities.append("نوع، دوره و مبنای درصد بازده را مشخص کنید.")
    elif "بازده" in value and "return" not in criteria:
        ambiguities.append("مقدار، دوره و مبنای بازده مورد انتظار را مشخص کنید.")
    for province in Province.objects.all().only("id", "name"):
        if province.name and province.name in value:
            criteria["province"] = [str(province.pk)]
            break
    discovery.criteria(criteria)
    return {
        "criteria": criteria,
        "needs_clarification": bool(ambiguities),
        "questions": ambiguities,
    }


def run(name, arguments, *, fallback_text="", fallback_criteria=None):
    if name not in TOOL_NAMES or not isinstance(arguments, dict):
        raise Fault("ابزار دستیار مجاز نیست.", 403)
    if name == "normalize_criteria":
        if set(arguments) - {"text", "criteria"}:
            raise Fault("ورودی ابزار معتبر نیست.")
        return normalize(
            arguments.get("text", fallback_text), arguments.get("criteria", fallback_criteria)
        )
    if name == "search_public_opportunities":
        if set(arguments) != {"criteria"}:
            raise Fault("ورودی جست‌وجو معتبر نیست.")
        return discovery.listing(arguments["criteria"])
    if name == "get_public_opportunity":
        if set(arguments) != {"id"} or not isinstance(arguments["id"], str):
            raise Fault("شناسه فرصت معتبر نیست.")
        return discovery.public_dto(get_op(arguments["id"]))
    if set(arguments) != {"ids"}:
        raise Fault("ورودی مقایسه معتبر نیست.")
    return discovery.compare(arguments["ids"])
