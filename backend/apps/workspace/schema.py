import json
from pathlib import Path

from apps.catalog import models as catalog
from apps.catalog.values import ValueErrorDetail, normalize, reject_nul

SCHEMA = json.loads(Path(__file__).with_name("schema_data.json").read_text())
FIELDS = {f["key"]: f for f in SCHEMA["fields"]}
STATUSES = ("unknown", "not_applicable")


class Fault(Exception):
    def __init__(self, message="درخواست معتبر نیست.", status=400, field="payload", current=None):
        self.message, self.status, self.field, self.current = message, status, field, current


def check_keys(data, keys):
    if not isinstance(data, dict) or set(data) != set(keys):
        raise Fault("کلیدهای درخواست با قرارداد یکسان نیستند.")
    try:
        reject_nul(data)
    except ValueErrorDetail as e:
        raise Fault(e.message, field=e.field) from e


def active_keys(routes, heritage_enabled, raw):
    participation = "investor" in routes or ("heritage" in routes and not heritage_enabled)
    conditions = {
        "always": True,
        "participation": participation,
        "execution": participation or "contractor" in routes,
        "duration": bool(set(routes) & {"investor", "lessee", "heritage"}),
        "rights": bool(set(routes) & {"buyer", "lessee"}),
        "heritage": "heritage" in routes and heritage_enabled,
        "heritage_years": "heritage" in routes
        and heritage_enabled
        and raw.get("heritage_returns") != ["fee"],
    }
    conditions.update({r: r in routes for r in SCHEMA["routes"]})
    # heritage-specific fields require explicit heritage structure selection.
    conditions["heritage"] = "heritage" in routes and heritage_enabled
    return {k for k, f in FIELDS.items() if conditions.get(f["when"], False)}


def validate_one(key, value):
    f = FIELDS[key]
    if f["unit"]:
        try:
            if not isinstance(value, dict) or value.get("field") != {
                "namespace": "invest.opportunity.project",
                "key": key,
                "version": 1,
            }:
                raise Fault("تعریف فیلد باید با معنای کنترل یکسان باشد.", field=key)
            return normalize(value)
        except ValueErrorDetail as e:
            raise Fault(e.message, field=key + "." + e.field) from e
    if f["kind"] in ("multi", "lines"):
        if value in STATUSES:
            return value
        if (
            not isinstance(value, list)
            or not value
            or len(value) > 50
            or any(not isinstance(x, str) or not x.strip() or len(x) > 4000 for x in value)
        ):
            raise Fault("فهرست معتبر یا وضعیت صریح وارد کنید.", field=key)
        if f["options"] and any(x not in f["options"] for x in value):
            raise Fault("گزینه از فهرست مجاز انتخاب شود.", field=key)
        if len(set(value)) != len(value):
            raise Fault("گزینه تکراری است.", field=key)
        return value
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise Fault("متن معتبر تا ۴۰۰۰ نویسه یا وضعیت صریح وارد کنید.", field=key)
    if f["kind"] == "enum" and value not in f["options"] and value not in STATUSES:
        raise Fault("گزینه از فهرست مجاز انتخاب شود.", field=key)
    if f["kind"] == "reference" and value not in STATUSES:
        model = {
            "province": catalog.Province,
            "county": catalog.County,
            "city": catalog.City,
            "group": catalog.Group,
            "subtype": catalog.Subtype,
        }[key]
        if len(value) > 100 or not model.objects.filter(pk=value).exists():
            raise Fault("شناسه کاتالوگ معتبر نیست.", field=key)
    return value


def effective(raw, routes, heritage_enabled):
    active = active_keys(routes, heritage_enabled, raw)
    result = {k: validate_one(k, v) for k, v in raw.items() if k in active}
    for child, parent, model, fk in [
        ("county", "province", catalog.County, "province_id"),
        ("city", "county", catalog.City, "county_id"),
        ("subtype", "group", catalog.Subtype, "group_id"),
    ]:
        v, p = result.get(child), result.get(parent)
        if (
            v
            and v not in STATUSES
            and (not p or p in STATUSES or not model.objects.filter(pk=v, **{fk: p}).exists())
        ):
            raise Fault("انتخاب فرزند با والد سازگار نیست؛ دوباره انتخاب کنید.", field=child)
    if (
        "metric_quantity" in result
        and result["metric_quantity"]["status"] == "known"
        and not result.get("metric_label")
    ):
        raise Fault("عنوان ظرفیت را مشخص کنید.", field="metric_label")
    return result, sorted(k for k in active if FIELDS[k]["required"] and k not in result)
