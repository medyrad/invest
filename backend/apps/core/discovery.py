import hashlib
import json
from decimal import Decimal, localcontext

from django.conf import settings
from django.core import signing
from django.utils import timezone

from apps.catalog import models as catalog
from apps.workspace.schema import Fault

from .models import Opportunity
from .publication import active, bank_verified, get_op, is_synthetic

POLICY = 1
WEIGHTS = {
    "amount": 30,
    "category": 20,
    "location": 15,
    "returns": 20,
    "risk": 15,
    "conditions": 15,
}
UNKNOWN = [None, "unknown", "not_applicable", ""]


def numeric(v):
    return Decimal(v["value"]) if isinstance(v, dict) and v.get("status") == "known" else None


def criteria(value):
    from apps.workspace.schema import check_keys

    if isinstance(value, dict):
        check_keys(value, list(value))
    if not isinstance(value, dict) or set(value) - {
        "kind",
        "route",
        "q",
        "budget_max",
        "budget_min",
        "province",
        "county",
        "city",
        "group",
        "subtype",
        "risk",
        "return",
        "conditions",
        "important",
        "preferences",
        "sort",
    }:
        raise Fault("معیارهای جست‌وجو معتبر نیست.")
    for k in ["budget_max", "budget_min"]:
        if k in value:
            if not isinstance(value[k], str):
                raise Fault("بودجه رشته اعشاری تومان است.", field=k)
            from apps.catalog.values import ValueErrorDetail, parse_number

            try:
                number = parse_number(value[k])
                value[k] = str(number)
            except ValueErrorDetail as e:
                raise Fault(e.message, field=k) from e
            if number < 0:
                raise Fault("بودجه منفی معتبر نیست.", field=k)
    for k in ["province", "county", "city", "group", "subtype", "risk"]:
        if k in value and (
            not isinstance(value[k], list)
            or len(value[k]) > 500
            or any(not isinstance(v, str) or len(v) > 100 or "\0" in v for v in value[k])
        ):
            raise Fault("فهرست معیار معتبر نیست.", field=k)
    if value.get("sort", "relevance") not in ["relevance", "capital", "payback", "newest"]:
        raise Fault("ترتیب معتبر نیست.")
    if "preferences" in value and (
        not isinstance(value["preferences"], dict) or len(value["preferences"]) > 100
    ):
        raise Fault("ترجیحات معتبر نیست.")
    if value.get("kind", "project") not in ["project", "fund", "sale"]:
        raise Fault("نوع معتبر نیست.")
    if value.get("route") and value["route"] not in [
        "investor",
        "fund",
        "contractor",
        "buyer",
        "lessee",
        "heritage",
        "operator",
        "charity",
    ]:
        raise Fault("مسیر جست‌وجو معتبر نیست.")
    for k in ["route", "q"]:
        if k in value and (
            not isinstance(value[k], str) or len(value[k]) > 200 or "\0" in value[k]
        ):
            raise Fault("متن جست‌وجو معتبر نیست.")
    if (
        "budget_min" in value
        and "budget_max" in value
        and Decimal(value["budget_min"]) > Decimal(value["budget_max"])
    ):
        raise Fault("کف بودجه از سقف آن بزرگ‌تر است.", field="budget_min")
    if "return" in value and (
        not isinstance(value["return"], dict) or set(value["return"]) != {"minimum", "basis"}
    ):
        raise Fault("مبنای بازده لازم است.")
    if "return" in value:
        from apps.catalog.values import ValueErrorDetail, parse_number, return_basis

        try:
            value["return"]["minimum"] = str(parse_number(value["return"]["minimum"], signed=True))
            value["return"]["basis"] = return_basis(value["return"]["basis"])
        except ValueErrorDetail as exc:
            raise Fault(exc.message, field="return." + exc.field) from exc
    if "conditions" in value and (
        not isinstance(value["conditions"], dict)
        or len(value["conditions"]) > 30
        or any(
            not isinstance(k, str)
            or not isinstance(v, list)
            or any(not isinstance(x, str) for x in v)
            for k, v in value["conditions"].items()
        )
    ):
        raise Fault("شرایط معتبر نیست.")
    if "important" in value:
        items = value["important"]
        if not isinstance(items, list) or len(items) > 500:
            raise Fault(
                "شرط‌های مهم را به‌صورت فهرست محورهای معتبر وارد کنید.", field="criteria.important"
            )
        for i, item in enumerate(items):
            if not isinstance(item, str) or item not in WEIGHTS:
                raise Fault("محور شرط مهم معتبر نیست.", field=f"criteria.important.{i}")
    # Validate shallow preference values before conditional evaluation or any lookup.
    for key, item in value.get("preferences", {}).items():
        valid = item is None or isinstance(item, (str, int, float, bool))
        if isinstance(item, list):
            valid = len(item) <= 500 and all(isinstance(x, (str, int)) for x in item)
        if not valid:
            raise Fault(
                "مقدار ترجیح باید متن، عدد یا فهرست ساده باشد.", field="criteria.preferences." + key
            )
    # Advisory input is contextual evidence, never a D28 exclusion or invented score.
    # Retain only the selected type's active answers in effective query/report contracts.
    preferences = value.get("preferences", {})
    advisory_inputs = {}
    for key, answer in preferences.items():
        if key.startswith("adv:"):
            parts = key.split(":")
            if len(parts) != 3:
                raise Fault("شناسه پرسش تخصصی معتبر نیست.", field="preferences." + key)
            advisory_inputs.setdefault(parts[1], {})[parts[2]] = answer
    if advisory_inputs:
        from apps.services.advisories import evaluate as advisory

        effective_preferences = {k: v for k, v in preferences.items() if not k.startswith("adv:")}
        selected = preferences.get("subtypes", value.get("subtype", []))
        if selected is None:
            selected = []
        if not isinstance(selected, list) or any(not isinstance(x, str) for x in selected):
            raise Fault(
                "نوع‌های انتخابی پرسش تخصصی باید فهرست شناسه باشند.", field="preferences.subtypes"
            )
        route = value.get("route", "investor")
        role = route if route in ["investor", "operator", "contractor"] else "context"
        for subtype, answers in advisory_inputs.items():
            evaluated = advisory(subtype, answers, role=role)
            if subtype in selected:
                effective_preferences.update(
                    {
                        "adv:" + subtype + ":" + k: v
                        for k, v in evaluated["effective_answers"].items()
                    }
                )
        value["preferences"] = effective_preferences
    for k, model in [
        ("province", catalog.Province),
        ("county", catalog.County),
        ("city", catalog.City),
    ]:
        if value.get(k):
            ids = []
            for v in value[k]:
                qs = model.objects.filter(pk=v)
                if not qs.exists():
                    qs = model.objects.filter(name=v)
                if k == "county" and value.get("province"):
                    qs = qs.filter(province_id__in=value["province"])
                if k == "city" and value.get("county"):
                    qs = qs.filter(county_id__in=value["county"])
                ids.extend(str(x) for x in qs.values_list("pk", flat=True))
            value[k] = list(dict.fromkeys(ids)) if ids else value[k]
    return value


def amount(s, route):
    if s.kind == "fund":
        return numeric(s.snapshot.get("minimum_investment"))
    f = s.snapshot
    if s.kind == "sale":
        price = numeric(f.get("price"))
        if f.get("price_mode") == "total":
            return price
        # No implicit lot size: this is the amount explicitly priced, not total offered.
        return None
    key = {
        "investor": "min_capital",
        "heritage": "min_capital",
        "contractor": "working_capital_min",
        "buyer": "purchase_price",
        "lessee": "deposit",
    }.get(route, "min_capital")
    return numeric(f.get(key))


def score(s, c):
    f = s.snapshot
    checks = []

    def add(axis, state, reason, weight=None):
        checks.append(
            {"axis": axis, "state": state, "reason": reason, "weight": weight or WEIGHTS[axis]}
        )

    if "budget_max" in c or ("budget_min" in c and c.get("route") == "buyer"):
        value = amount(s, c.get("route"))
        ok = None
        if value is not None:
            ok = ("budget_max" not in c or value <= Decimal(c["budget_max"])) and (
                not (s.kind == "sale" or c.get("route") == "buyer")
                or "budget_min" not in c
                or value >= Decimal(c["budget_min"])
            )
        add(
            "amount",
            "unknown" if ok is None else "met" if ok else "unmet",
            "حداقل ورود با سقف بودجه؛ خرید با بازه قیمت. قیمت واحد، مبلغ کل فرض نمی‌شود.",
        )
    cat = "subtype" if c.get("subtype") else "group" if c.get("group") else None
    if cat and not c.get("preferences", {}).get("subtypes"):
        add(
            "category",
            "unknown" if f.get(cat) in UNKNOWN else "met" if f.get(cat) in c[cat] else "unmet",
            "دسته انتخاب‌شده",
        )
    loc = next((k for k in ["city", "county", "province"] if c.get(k)), None)
    if loc and not c.get("preferences", {}).get("neighborhood"):
        add(
            "location",
            "unknown" if f.get(loc) in UNKNOWN else "met" if f.get(loc) in c[loc] else "unmet",
            "عمیق‌ترین سطح انتخابی؛ گزینه‌ها در یک سطح یا هستند.",
        )
    if c.get("risk"):
        add(
            "risk",
            "unknown"
            if f.get("risk") in UNKNOWN
            else "met"
            if f.get("risk") in c["risk"]
            else "unmet",
            "ریسک اعلامی؛ تأیید مستقل نیست.",
        )
    if c.get("return"):
        v = f.get(
            "irr"
            if s.kind == "project"
            else "forecast_" + f["forecast_type"]
            if f.get("forecast_type") in ["irr", "simple_rate", "effective_rate"]
            else "forecast"
        )
        n = numeric(v)
        comparable = n is not None and v.get("basis") == c["return"]["basis"]
        try:
            minimum = Decimal(c["return"]["minimum"])
        except (ValueError, TypeError, ArithmeticError) as e:
            raise Fault("حد بازده معتبر نیست.") from e
        add(
            "returns",
            "unknown" if not comparable else "met" if n >= minimum else "unmet",
            "بازده فقط با مبنای کامل یکسان مقایسه می‌شود.",
        )
    conditions = c.get("conditions", {})
    if conditions:
        for k, wanted in conditions.items():
            v = f.get(k)
            state = (
                "unknown"
                if v is None or (isinstance(v, str) and v in ["unknown", "not_applicable"])
                else None
            )
            # Verified bank evidence is never inferred from an owner's claim.
            if k.startswith("bank_"):
                state = "unknown"
            if state is None:
                state = (
                    "met"
                    if (any(x in wanted for x in v) if isinstance(v, list) else v in wanted)
                    else "unmet"
                )
            add(
                "conditions",
                state,
                "شرط " + k,
                Decimal(WEIGHTS["conditions"]) / Decimal(len(conditions)),
            )
    preferences = c.get("preferences", {})
    from .preferences import evaluate

    preferences = {k: v for k, v in preferences.items() if not (k == "risk" and c.get("risk"))}
    for axis, state, reason in evaluate(s, c.get("route"), preferences, groups=c.get("group", [])):
        add(axis, state, reason)
    # Independent criteria share their axis weight; the denominator is query-defined.
    counts = {axis: sum(1 for item in checks if item["axis"] == axis) for axis in WEIGHTS}
    for item in checks:
        item["weight"] = Decimal(WEIGHTS[item["axis"]]) / Decimal(counts[item["axis"]])
    with localcontext() as ctx:
        ctx.prec = 60
        W = sum((Decimal(x["weight"]) for x in checks), Decimal(0))
        E = sum((Decimal(x["weight"]) for x in checks if x["state"] == "met"), Decimal(0))
        K = sum((Decimal(x["weight"]) for x in checks if x["state"] != "unknown"), Decimal(0))
        sc = 100 * E / W if W else None
        coverage = 100 * K / W if W else None
    return {
        "score": str(sc) if sc is not None else None,
        "coverage": str(coverage) if coverage is not None else None,
        "status": "no_preferences" if not W else "insufficient_data" if not K else "ranked",
        "checks": [{**x, "weight": str(x["weight"])} for x in checks],
        "warnings": [
            x["reason"]
            for x in checks
            if x["axis"] in c.get("important", []) and x["state"] != "met"
        ],
        "policy_version": POLICY,
    }


def public_dto(op):
    s = op.public_revision
    if settings.INVEST_ENV == "public" and is_synthetic(op):
        raise Fault("فرصت پیدا نشد.", 404)
    if not s:
        raise Fault("نسخه عمومی وجود ندارد.", 404)
    review = s.review_set.filter(decision="approved").order_by("-id").first()
    return {
        "id": str(op.pk),
        "revision": str(s.pk),
        "kind": s.kind,
        "routes": s.routes,
        "fields": {"title": "این فرصت تعلیق شده است"}
        if op.availability == "admin_suspended"
        else s.snapshot,
        "availability": op.availability
        if not op.expires_at or op.expires_at > timezone.now()
        else "expired",
        "accepting_requests": active(op),
        "published_at": review.created_at.isoformat() if review else None,
        "synthetic": is_synthetic(op),
        "verified": {"bank": bank_verified(s) if op.availability != "admin_suspended" else False},
        "expires_at": op.expires_at.isoformat() if op.expires_at else None,
        "no_expiry": op.expires_at is None,
        "last_reviewed_at": review.created_at.isoformat() if review else None,
        "images": [f"/api/v1/core/public-image/{fid}" for fid in review.public_files]
        if review and op.availability != "admin_suspended"
        else [],
    }


def listing(c, cursor=None):
    criteria(c)
    fingerprint = hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()
    if cursor:
        try:
            frozen = signing.loads(cursor, salt="core-search", max_age=3600)
        except signing.BadSignature as e:
            raise Fault("صفحه منقضی است؛ جست‌وجو را تازه کنید.", 409) from e
        if frozen["criteria"] != fingerprint or frozen["policy"] != POLICY:
            raise Fault("معیار یا نسخه صفحه تغییر کرده است.", 409)
        ids = frozen["ids"]
        offset = frozen["offset"]
        at = frozen["at"]
    else:
        rows = []
        for op in Opportunity.objects.filter(public_revision__isnull=False).select_related(
            "public_revision", "draft"
        ):
            if (settings.INVEST_ENV == "public" and is_synthetic(op)) or not active(op):
                continue
            s = op.public_revision
            if c.get("kind") and c["kind"] != s.kind:
                continue
            if c.get("route") and c["route"] not in s.routes:
                continue
            if (
                c.get("q")
                and c["q"].casefold()
                not in (str(s.snapshot.get("title", "")) + " " + str(op.pk)).casefold()
            ):
                continue
            r = score(s, c)
            approved = s.review_set.filter(decision="approved").first()
            rows.append((op, r, approved.created_at))
        rows.sort(
            key=lambda r: (
                -(Decimal(r[1]["score"]) if r[1]["score"] is not None else Decimal(0)),
                -(Decimal(r[1]["coverage"]) if r[1]["coverage"] is not None else Decimal(0)),
                -r[2].timestamp(),
                str(r[0].pk),
            )
        )
        if c.get("sort") == "newest":
            rows.sort(key=lambda r: (-r[2].timestamp(), str(r[0].pk)))
        elif c.get("sort") in ["capital", "payback"]:

            def order(r):
                n = (
                    amount(r[0].public_revision, c.get("route"))
                    if c["sort"] == "capital"
                    else numeric(r[0].public_revision.snapshot.get("payback_years"))
                )
                return (n is None, n if n is not None else Decimal(0), str(r[0].pk))

            rows.sort(key=order)
        ids = [{"id": str(o.pk), "revision": str(o.public_revision_id)} for o, _, _ in rows]
        offset = 0
        at = timezone.now().isoformat()
    output = []
    for row in ids[offset : offset + 12]:
        op = get_op(row["id"])
        # Never return an old now-withdrawn revision from a stale cursor.
        if active(op) and str(op.public_revision_id) == row["revision"]:
            output.append({**public_dto(op), "matching": score(op.public_revision, c)})
    next_cursor = (
        signing.dumps(
            {
                "criteria": fingerprint,
                "policy": POLICY,
                "ids": ids,
                "offset": offset + 12,
                "at": at,
            },
            salt="core-search",
            compress=True,
        )
        if offset + 12 < len(ids)
        else None
    )
    return {
        "items": output,
        "total": len(ids),
        "next": next_cursor,
        "policy_version": POLICY,
        "as_of": at,
        "criteria": c,
    }


def compare(ids):
    if (
        not isinstance(ids, list)
        or not 2 <= len(ids) <= 4
        or any(not isinstance(i, str) for i in ids)
        or len(set(ids)) != len(ids)
    ):
        raise Fault("۲ تا ۴ فرصت متمایز انتخاب کنید.")
    ops = [get_op(i) for i in ids]
    if any(not o.public_revision_id for o in ops):
        raise Fault("نسخه عمومی در دسترس نیست.", 404)
    if len({o.public_revision.kind for o in ops}) != 1:
        raise Fault("فقط فرصت‌های هم‌نوع مقایسه می‌شوند.")
    rows = []
    keys = set().union(*(o.public_revision.snapshot for o in ops))
    for key in sorted(keys):
        values = [o.public_revision.snapshot.get(key) for o in ops]
        typed = all(isinstance(v, dict) and v.get("status") == "known" for v in values)
        from apps.catalog.values import compare as compare_value

        compatible = typed and all(compare_value(values[0], v)["comparable"] for v in values)
        if key == "price":
            modes = [o.public_revision.snapshot.get("price_mode") for o in ops]
            compatible = compatible and len(set(modes)) == 1 and modes[0] in ["total", "per_unit"]
            if compatible and modes[0] == "per_unit":
                quantities = [o.public_revision.snapshot.get("price_quantity") for o in ops]
                compatible = all(
                    isinstance(q, dict)
                    and q.get("status") == "known"
                    and q.get("value") == quantities[0].get("value")
                    and q.get("base_unit") == quantities[0].get("base_unit")
                    and q.get("base_version") == quantities[0].get("base_version")
                    for q in quantities
                )
        rows.append(
            {
                "key": key,
                "values": values,
                "comparable": compatible,
                "reason": None
                if compatible
                else "داده نامعلوم، متن یا واحد/مبنای ناهمسان؛ برنده محاسبه نمی‌شود.",
            }
        )
    return {"items": [public_dto(o) for o in ops], "rows": rows}
