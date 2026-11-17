"""D29 primitives; no FX, financial calculator, form engine or ranking."""

import re
from datetime import date
from decimal import Decimal, Inexact, Rounded, localcontext

MAX_VALUE = Decimal("999999999999999999999999.999999999")
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
STATUSES = {"known", "unknown", "not_applicable"}


class ValueErrorDetail(ValueError):
    def __init__(self, code, message, field="source_value"):
        super().__init__(message)
        self.code, self.message, self.field = code, message, field


def fail(code, message, field="source_value"):
    raise ValueErrorDetail(code, message, field)


def decimal_string(value):
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def parse_number(value, *, places=9, signed=False):
    if not isinstance(value, str) or len(value) > 100:
        fail("decimal_string_required", "مقدار را به‌صورت رشته اعشاری وارد کنید.")
    text = value.strip().translate(DIGITS)
    if not text or any(c.isspace() for c in text):
        fail("ambiguous_number", "عدد خالی یا دارای فاصله داخلی معتبر نیست.")
    if "." in text and "٫" in text or "," in text and "٬" in text:
        fail("ambiguous_number", "از یک شیوه جداکردن رقم‌ها و یک ممیز استفاده کنید.")
    text = text.replace("٫", ".").replace("٬", ",")
    if not re.fullmatch(r"-?(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?", text):
        fail("ambiguous_number", "عدد معتبر نیست؛ ممیز نقطه یا ٫ و گروه‌های سه‌رقمی مجازند.")
    if text.startswith("-") and not signed:
        fail("negative_not_allowed", "مقدار منفی برای این فیلد مجاز نیست.")
    if "." in text and len(text.split(".")[1]) > places:
        fail("excess_precision", f"حداکثر {places} رقم اعشار مجاز است؛ مقدار گرد نمی‌شود.")
    number = Decimal(text.replace(",", ""))
    if number.copy_abs() > MAX_VALUE:
        fail("out_of_range", "عدد از ظرفیت پشتیبانی‌شده بزرگ‌تر است.")
    return number


def exact_product(a, b):
    with localcontext() as ctx:
        ctx.prec = 80
        ctx.traps[Inexact] = True
        ctx.traps[Rounded] = True
        return a * b


def check_ref(value, keys, field):
    if not isinstance(value, dict) or set(value) != set(keys):
        fail("invalid_reference", "شناسه و نسخه تعریف را صریح وارد کنید.", field)
    version = value.get("version")
    if type(version) is not int or not 1 <= version <= 9999:
        fail("invalid_version", "نسخه تعریف معتبر نیست.", field)
    if any(not isinstance(value[k], str) or not value[k] for k in keys if k != "version"):
        fail("invalid_reference", "شناسه تعریف معتبر نیست.", field)


def return_basis(basis):
    keys = {
        "version",
        "metric_type",
        "period",
        "horizon",
        "basis_date",
        "price_basis",
        "scope",
        "observation",
        "source",
    }
    if not isinstance(basis, dict) or set(basis) != keys:
        fail("incomplete_basis", "نوع، دوره، افق، تاریخ و منبع بازده را کامل وارد کنید.", "basis")
    enums = {
        "metric_type": {"irr", "simple_rate", "effective_rate"},
        "period": {"annual", "monthly", "total"},
        "price_basis": {"nominal", "real"},
        "scope": {"project", "investor"},
        "observation": {"forecast", "observed", "claimed"},
    }
    if (
        type(basis["version"]) is not int
        or basis["version"] != 1
        or any(
            not isinstance(basis[k], str) or basis[k] not in options for k, options in enums.items()
        )
    ):
        fail("invalid_basis", "نسخه یا مبنای بازده پشتیبانی نمی‌شود.", "basis")
    horizon = basis["horizon"]
    if not isinstance(horizon, dict) or set(horizon) != {"value", "unit"}:
        fail("invalid_basis", "مقدار و واحد نسخه‌دار افق بازده را مشخص کنید.", "basis")
    check_ref(horizon["unit"], ("code", "version"), "basis")
    from .models import UnitDefinition

    if (
        horizon["unit"]["code"] not in ("DAY", "MONTH", "YEAR")
        or not UnitDefinition.objects.filter(**horizon["unit"], kind="quantity").exists()
    ):
        fail("invalid_basis", "واحد یا نسخه افق بازده شناخته‌شده نیست.", "basis")
    h = parse_number(horizon["value"])
    if h <= 0:
        fail("invalid_basis", "افق بازده باید مثبت باشد.", "basis")
    try:
        if not isinstance(basis["basis_date"], str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", basis["basis_date"]
        ):
            raise ValueError
        date.fromisoformat(basis["basis_date"])
    except ValueError:
        fail("invalid_basis", "تاریخ مبنا باید تاریخ میلادی معتبر YYYY-MM-DD باشد.", "basis")
    if (
        not isinstance(basis["source"], str)
        or not basis["source"].strip()
        or len(basis["source"]) > 2000
    ):
        fail("incomplete_basis", "منبع ادعای بازده را مشخص کنید.", "basis")
    return {**basis, "horizon": {"value": decimal_string(h), "unit": dict(horizon["unit"])}}


def normalize(payload):
    from .models import FieldDefinition, UnitDefinition

    if not isinstance(payload, dict) or set(payload) != {
        "field",
        "unit",
        "status",
        "source_value",
        "basis",
    }:
        fail(
            "invalid_payload", "فیلد، واحد، نسخه، وضعیت، مقدار و مبنا را صریح وارد کنید.", "payload"
        )
    check_ref(payload["field"], ("namespace", "key", "version"), "field")
    check_ref(payload["unit"], ("code", "version"), "unit")
    try:
        definition = FieldDefinition.objects.get(**payload["field"])
    except FieldDefinition.DoesNotExist:
        fail("unknown_field_version", "فیلد یا نسخه آن شناخته‌شده نیست.", "field")
    try:
        unit = UnitDefinition.objects.get(**payload["unit"])
    except UnitDefinition.DoesNotExist:
        fail("unknown_unit_version", "واحد یا نسخه آن شناخته‌شده نیست.", "unit")
    if unit.kind != definition.kind or payload["unit"] not in definition.allowed_units:
        fail("unit_not_allowed", "این واحد برای معنای این فیلد مجاز نیست.", "unit")
    status = payload["status"]
    if not isinstance(status, str) or status not in STATUSES:
        fail("invalid_status", "وضعیت باید معلوم، نامعلوم یا نامربوط باشد.", "status")
    if (
        status == "unknown"
        and not definition.allow_unknown
        or status == "not_applicable"
        and not definition.allow_not_applicable
    ):
        fail("status_not_allowed", "این وضعیت برای فیلد مجاز نیست.", "status")
    source = value = None
    if status == "known":
        source = parse_number(
            payload["source_value"],
            places=0 if unit.base_code == "ITEM" else definition.decimal_places,
            signed=unit.kind == "return",
        )
        value = exact_product(source, unit.factor)
        # Validate the normalized value as well, without discarding trailing precision in input.
        if value.copy_abs() > MAX_VALUE or value.as_tuple().exponent < -9:
            # A factor can add only insignificant zeros; those do not lose numeric precision.
            canonical = decimal_string(value)
            if (
                value.copy_abs() > MAX_VALUE
                or "." in canonical
                and len(canonical.split(".")[1]) > 9
            ):
                fail("out_of_range", "مقدار پایه از حد یا دقت مجاز خارج است.")
        if value < definition.minimum or value > definition.maximum:
            fail("out_of_range", "مقدار از حدود اعلام‌شده این فیلد خارج است.")
    elif payload["source_value"] is not None:
        fail("value_not_applicable", "برای مقدار نامعلوم یا نامربوط، عدد وارد نکنید.")
    basis = payload["basis"]
    if unit.kind == "money" and basis is not None:
        fail("invalid_basis", "مبلغ، مبنای بازده یا مدت نمی‌پذیرد.", "basis")
    if unit.kind == "return" and (status == "known" or basis is not None):
        basis = return_basis(basis)
        if basis["metric_type"] != definition.return_type:
            fail("return_type_mismatch", "نوع بازده با معنای این فیلد یکسان نیست.", "basis")
    if unit.kind == "quantity":
        if unit.base_code in ("DAY", "MONTH", "YEAR"):
            if (
                not isinstance(basis, dict)
                or set(basis) != {"start_basis"}
                or not isinstance(basis["start_basis"], str)
                or not basis["start_basis"].strip()
                or len(basis["start_basis"]) > 200
            ):
                fail(
                    "invalid_basis",
                    "مبنای شروع مدت را صریح بنویسید؛ اگر معلوم نیست unspecified وارد کنید.",
                    "basis",
                )
            basis = {"start_basis": basis["start_basis"].strip()}
        elif basis is not None:
            fail("invalid_basis", "این واحد مقدار، مبنای شروع مدت ندارد.", "basis")
    return {
        "contract_version": 1,
        "kind": unit.kind,
        "field": dict(payload["field"]),
        "unit": dict(payload["unit"]),
        "status": status,
        "source_value": decimal_string(source) if source is not None else None,
        "value": decimal_string(value) if value is not None else None,
        "base_unit": unit.base_code,
        "base_version": unit.base_version,
        "conversion_factor": decimal_string(unit.factor),
        "basis": basis,
    }


def input_from_dto(dto):
    return {k: dto[k] for k in ("field", "unit", "status", "source_value", "basis")}


def compare(left, right):
    """Only comparable scalar facts; never an investment recommendation."""
    a, b = normalize(input_from_dto(left)), normalize(input_from_dto(right))
    if a != left or b != right:
        fail("invalid_snapshot", "مقدار یا قرارداد ذخیره‌شده با تعریف نسخه‌دار سازگار نیست.")
    reason = None
    if a["status"] != "known" or b["status"] != "known":
        reason = "unknown_or_not_applicable"
    elif a["field"] != b["field"]:
        reason = "different_field_or_version"
    elif (a["base_unit"], a["base_version"], a["unit"]["version"]) != (
        b["base_unit"],
        b["base_version"],
        b["unit"]["version"],
    ):
        reason = "different_unit_or_version"
    elif (
        a["basis"] != b["basis"]
        or isinstance(a["basis"], dict)
        and a["basis"].get("start_basis") == "unspecified"
    ):
        reason = "different_or_unspecified_basis"
    if reason:
        return {"comparable": False, "reason": reason, "relation": None}
    x, y = Decimal(a["value"]), Decimal(b["value"])
    return {
        "comparable": True,
        "reason": None,
        "relation": "equal" if x == y else "less" if x < y else "greater",
    }
