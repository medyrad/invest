import json
from pathlib import Path

from apps.catalog import models as catalog
from apps.catalog.values import ValueErrorDetail, normalize

from . import schema

SCHEMAS = json.loads(Path(__file__).with_name("other_schemas.json").read_text())


def definition(kind):
    return schema.SCHEMA if kind == "project" else SCHEMAS[kind]


def fields(kind):
    return {f["key"]: f for f in definition(kind)["fields"]}


def active(kind, routes, heritage, raw):
    if kind == "project":
        return schema.active_keys(routes, heritage, raw)
    flags = {
        "always": True,
        "bank": raw.get("bank_exists") == "yes",
        "property": raw.get("category") == "property",
        "scrap": raw.get("category") == "scrap",
        "area": raw.get("category") in ["property", "land"],
        "per_unit": raw.get("price_mode") == "per_unit",
    }
    return {k for k, f in fields(kind).items() if flags.get(f["when"], False)}


def validate(kind, key, value):
    if kind == "project":
        return schema.validate_one(key, value)
    f = fields(kind)[key]
    if f["unit"]:
        try:
            if not isinstance(value, dict) or value.get("field") != {
                "namespace": "invest.opportunity." + kind,
                "key": key,
                "version": 1,
            }:
                raise schema.Fault("تعریف فیلد با این کنترل سازگار نیست.", field=key)
            return normalize(value)
        except ValueErrorDetail as e:
            raise schema.Fault(e.message, field=key + "." + e.field) from e
    if (
        f["kind"] == "lines"
        and isinstance(value, list)
        and 0 < len(value) <= 50
        and all(isinstance(x, str) and x.strip() and len(x) <= 4000 for x in value)
    ):
        return value
    if not isinstance(value, str) or not value.strip() or len(value) > 4000:
        raise schema.Fault("متن معتبر یا وضعیت صریح وارد کنید.", field=key)
    if f["options"] and value not in f["options"] and value not in schema.STATUSES:
        raise schema.Fault("گزینه معتبر انتخاب کنید.", field=key)
    if f["kind"] == "reference" and value not in schema.STATUSES:
        model = {"province": catalog.Province, "county": catalog.County, "city": catalog.City}[key]
        if len(value) > 100 or not model.objects.filter(pk=value).exists():
            raise schema.Fault("شناسه مکان معتبر نیست.", field=key)
    return value


def effective(kind, raw, routes, heritage):
    if kind == "project":
        return schema.effective(raw, routes, heritage)
    fs = fields(kind)
    keys = active(kind, routes, heritage, raw)
    result = {k: validate(kind, k, v) for k, v in raw.items() if k in keys}
    for child, parent, model, fk in [
        ("county", "province", catalog.County, "province_id"),
        ("city", "county", catalog.City, "county_id"),
    ]:
        v, p = result.get(child), result.get(parent)
        if (
            v
            and v not in schema.STATUSES
            and (
                not p or p in schema.STATUSES or not model.objects.filter(pk=v, **{fk: p}).exists()
            )
        ):
            raise schema.Fault("انتخاب فرزند با والد سازگار نیست.", field=child)
    if (
        "price_quantity" in result
        and result["price_quantity"]["status"] == "known"
        and result["price_quantity"]["value"] == "0"
    ):
        raise schema.Fault("مقدار مبنای قیمت واحد باید بیش از صفر باشد.", field="price_quantity")
    return result, sorted(k for k in keys if fs[k]["required"] and k not in result)
