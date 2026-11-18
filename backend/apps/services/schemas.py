import copy
import json
from decimal import Decimal
from pathlib import Path

from apps.catalog.models import Group, Province, Subtype
from apps.catalog.values import ValueErrorDetail, decimal_string, normalize, parse_number
from apps.workspace.schema import Fault, check_keys

CATALOG = json.loads(Path(__file__).with_name("schemas.json").read_text())
SOURCE = json.loads(Path(__file__).with_name("source-services.json").read_text())
KINDS = tuple(CATALOG)


def base_fields(kind):
    fs = copy.deepcopy(CATALOG[kind]["fields"])
    for f in fs:
        ref = f.get("reference")
        if ref == "province":
            sentinels = (
                {"unknown": "هنوز محل مشخص نیست"}
                if kind == "foreign-investment"
                else {"any": "هرجا نیاز تاییدشده بیشتر باشد"}
                if kind == "charity"
                else {}
                if kind in ["proposal", "ideas"]
                else {"all": "همه استان‌ها"}
                if kind == "land-preparation"
                else {"all": "هنوز مشخص نیست / سراسر کشور"}
            )
            f["options"] = {**sentinels, **dict(Province.objects.values_list("id", "name"))}
        if ref == "sector":
            f["options"] = dict(Group.objects.values_list("id", "name"))
        if ref == "type":
            by_parent = {}
            for s in Subtype.objects.all():
                by_parent.setdefault(s.group_id, []).append([s.pk.split(".")[-1], s.name])
            f.update(
                options_by_parent=by_parent,
                parent="sector",
                options={v: label for xs in by_parent.values() for v, label in xs},
            )
    for f in fs:
        f["namespace"] = "invest.service." + kind.replace("-", "_")
        f["version"] = 1
    return fs


def answer_fields(kind, raw, all_fields=False):
    if kind != "land-preparation":
        return []
    from .advisories import CONFIGS, questions

    selected = raw.get("types", [])
    if not all_fields and (
        not isinstance(selected, list)
        or len(selected) > 100
        or any(not isinstance(v, str) for v in selected)
    ):
        raise Fault("فهرست شناسه خدمات زمین معتبر نیست.", field="types")
    technical = SOURCE[kind]["technical_advisory_types"]
    technical_ids = [t["id"] if isinstance(t, dict) else t for t in technical]
    ids = technical_ids if all_fields else selected if isinstance(selected, list) else []
    answers = {k.removeprefix("answer_"): v for k, v in raw.items() if k.startswith("answer_")}
    qs = []
    for key in ids:
        if key in CONFIGS:
            qs.extend(
                q
                for q in questions(key, answers, all_fields=all_fields)
                if q["id"] != "participation"
            )
    added = [t for t in SOURCE[kind]["service_types"] if t["id"] not in technical_ids]
    if all_fields or any(t["id"] in ids for t in added):
        existing = next((q for q in qs if q["id"] == "owner"), None)
        extra = [
            {"value": "endowment", "label": "متولی یا مرجع مرتبط با موقوفه"},
            {"value": "unknown", "label": "هنوز مشخص نیست"},
        ]
        if existing:
            existing = copy.deepcopy(existing)
            qs = [q for q in qs if q["id"] != "owner"]
            existing["options"].extend(extra)
            qs.insert(0, existing)
        else:
            qs.append(
                {
                    "id": "owner",
                    "label": "صاحب اختیار زمین یا ملک کدام است؟",
                    "options": [
                        {"value": "public", "label": "دستگاه عمومی یا دولتی"},
                        {"value": "private", "label": "مالک / شرکت خصوصی"},
                        *extra,
                        {"value": "any", "label": "محدودیت ندارم"},
                    ],
                }
            )
        qs.append(
            {
                "id": "lpServiceRight",
                "label": "اختیار سفارش و پیگیری خدمات این ملک چه وضعیتی دارد؟",
                "options": [
                    {"value": "documented", "label": "مدارک مالک یا نماینده برای بررسی موجود است"},
                    {"value": "pending", "label": "اختیار نیازمند بررسی است"},
                    {
                        "value": "disputed",
                        "label": "اختلاف مالکیت، تصرف یا محدودیت اقدام وجود دارد",
                    },
                ],
            }
        )
        if not any(q["id"] == "revenue" for q in qs):
            qs.append(
                {
                    "id": "revenue",
                    "label": "هزینه بسته خدمات چگونه پرداخت شود؟",
                    "options": [
                        {"value": k, "label": v}
                        for k, v in [
                            ("public", "حق‌الزحمه یا پرداخت نقدی طبق قرارداد"),
                            ("sale", "تسویه غیرنقدی، پس از بررسی اختیار و امکان آن"),
                            ("mixed", "ترکیب نقدی و غیرنقدی"),
                            ("support", "منابع عمومی یا حمایتی مستند"),
                        ]
                    ],
                }
            )
        for t in added:
            if all_fields or t["id"] in ids:
                qs.append(
                    {
                        "id": "status-" + t["id"],
                        "label": t["question"],
                        "options": [
                            {"value": "ready", "label": "مستندات اولیه برای بررسی موجود است"},
                            {"value": "pending", "label": "در حال بررسی یا تکمیل است"},
                            {"value": "unknown", "label": "هنوز مشخص نیست"},
                        ],
                    }
                )
    out = {}
    for q in qs:
        key = "answer_" + q["id"]
        if key not in out:
            out[key] = {
                "key": key,
                "label": q["label"],
                "kind": "enum",
                "section": 1,
                "options": {},
                "required": True,
                "unit": None,
                "when": None,
                "source": SOURCE[kind]["source"],
            }
        out[key]["options"].update({x["value"]: x["label"] for x in q["options"]})
    return list(out.values())


def definition(kind, raw=None):
    result = {**CATALOG[kind], "fields": base_fields(kind) + answer_fields(kind, raw or {})}
    if kind == "foreign-investment":
        result["reading"] = json.loads(
            Path(__file__).with_name("international-references.json").read_text()
        )
    return result


def fields(kind):
    return {f["key"]: f for f in base_fields(kind) + answer_fields(kind, {}, all_fields=True)}


def current_fields(kind, raw):
    from .conditions import matches

    fs = base_fields(kind) + answer_fields(kind, raw)
    return {f["key"]: f for f in fs if matches(f.get("when"), raw)}


def validate_one(kind, key, value, field=None):
    f = field or fields(kind)[key]
    if value is None:
        raise Fault("مقدار خالی را حذف کنید یا وضعیت صریح وارد کنید.", field=key)
    if f["unit"]:
        try:
            ref = {
                "namespace": "invest.service." + kind.replace("-", "_"),
                "key": key,
                "version": 1,
            }
            if not isinstance(value, dict) or value.get("field") != ref:
                raise Fault("تعریف فیلد با خدمت یکسان نیست.", field=key)
            n = normalize(value)
            if n["status"] == "known":
                number = Decimal(n["value"])
                if f.get("integer") and number != number.to_integral():
                    raise Fault("مقدار باید عدد صحیح باشد.", field=key)
                if f.get("minimum") is not None and number < Decimal(f["minimum"]):
                    raise Fault("مقدار از حد مجاز این فیلد کمتر است.", field=key)
                if f.get("maximum") is not None and number > Decimal(f["maximum"]):
                    raise Fault("مقدار از حد مجاز این فیلد بیشتر است.", field=key)
            return n
        except ValueErrorDetail as e:
            raise Fault(e.message, field=key + "." + e.field) from e
    if f["kind"] == "boolean":
        if type(value) is not bool:
            raise Fault("گزینه باید بله یا خیر باشد.", field=key)
        return value
    if f["kind"] == "foreign_amount":
        if not isinstance(value, dict) or set(value) != {"status", "source_value", "currency"}:
            raise Fault("وضعیت، مبلغ و ارز نسخه‌دار را مشخص کنید.", field=key)
        check_keys(value, list(value))
        currency = value["currency"]
        allowed = fields(kind)["currency"]["options"]
        if (
            not isinstance(currency, dict)
            or set(currency) != {"code", "version"}
            or not isinstance(currency["code"], str)
            or currency["code"] not in allowed
            or type(currency["version"]) is not int
            or currency["version"] != 1
        ):
            raise Fault("ارز و نسخه شناخته‌شده انتخاب کنید.", field=key + ".currency")
        if value["status"] not in ["known", "unknown", "not_applicable"]:
            raise Fault("وضعیت مبلغ معتبر نیست.", field=key + ".status")
        try:
            amount = (
                decimal_string(parse_number(value["source_value"]))
                if value["status"] == "known"
                else None
            )
        except ValueErrorDetail as e:
            raise Fault(e.message, field=key + "." + e.field) from e
        if value["status"] != "known" and value["source_value"] is not None:
            raise Fault("مبلغ نامعلوم یا نامربوط مقدار عددی ندارد.", field=key)
        return {**value, "value": amount, "base_conversion": None, "contract_version": 1}
    if f["kind"] == "decimal":
        try:
            return decimal_string(parse_number(value))
        except ValueErrorDetail as e:
            raise Fault(e.message, field=key) from e
    options = f.get("options")
    if f.get("options_by_parent"):
        options = {
            str(v): label for values in f["options_by_parent"].values() for v, label in values
        }
    if f["kind"] in ["multi", "ordered_multi"]:
        if (
            not isinstance(value, list)
            or len(value) > 100
            or any(not isinstance(v, str) or v not in options for v in value)
            or len(set(value)) != len(value)
        ):
            raise Fault("فهرست گزینه‌های متمایز معتبر انتخاب کنید.", field=key)
        return value
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise Fault("متن معتبر تا۴۰۰۰حرف وارد کنید.", field=key)
    if f["kind"] == "enum" and (not options or value not in options):
        raise Fault("گزینه از فهرست مجاز انتخاب شود.", field=key)
    return value.strip()


def effective(kind, raw):
    if not isinstance(raw, dict) or len(raw) > 500 or set(raw) - fields(kind).keys():
        raise Fault("فیلد ناشناخته یا ورودی نامعتبر خدمت.", field="values")
    check_keys(raw, list(raw))
    current = current_fields(kind, raw)
    result, missing = {}, []
    for key, f in current.items():
        v = raw.get(key)
        parent = raw.get(f.get("parent"))
        allowed = (
            (f["options_by_parent"].get(parent, []) if isinstance(parent, str) else [])
            if f.get("options_by_parent")
            else None
        )
        if allowed is not None and v not in [x[0] for x in allowed]:
            v = None  # A saved child from another parent is dormant, never guessed.
        if v is not None:
            result[key] = validate_one(kind, key, v, f)
        if f["required"] and (v is None or v == []):
            missing.append(key)
    return result, missing


def merge(kind, old, values):
    fs = fields(kind)
    if not isinstance(values, dict) or set(values) - fs.keys():
        raise Fault("فیلدهای این خدمت معتبر نیستند.", field="values")
    check_keys(values, list(values))
    raw = dict(old)
    # Evaluate each submitted selector in schema order, using its current visibility.
    # Then evaluate dependants; hidden payload cannot overwrite dormant saved answers.
    for key in fs:
        current = current_fields(kind, raw)
        if key not in values or key not in current:
            continue
        value = values[key]
        if value is None:
            raw.pop(key, None)
        else:
            validate_one(kind, key, value, current[key])
            raw[key] = value
    effective(kind, raw)
    return raw


def readable_state(kind, raw):
    """Read historical drafts without letting one invalid old field hide the account list.

    Raw is never rewritten. Only this read DTO omits invalid values and flags them;
    save, evaluation, report and submission still use strict validation.
    """
    candidate = copy.deepcopy(raw)
    errors = {}
    for _ in range(len(raw) + 1 if isinstance(raw, dict) else 1):
        try:
            result, missing = effective(kind, candidate)
            return result, sorted(set(missing) | set(errors)), errors
        except Fault as error:
            key = error.field.split(".")[0]
            errors[key] = error.message
            if not isinstance(candidate, dict) or key not in candidate:
                return {}, sorted(set(current_fields(kind, {}).keys())), errors
            candidate.pop(key)
    raise AssertionError("Bounded draft validation did not terminate")
