"""Service-specific source semantics. All arithmetic uses exact decimal strings."""

import json
from decimal import Decimal, localcontext
from pathlib import Path

from apps.catalog.values import decimal_string
from apps.workspace.schema import Fault

from . import advisories, schemas


def number(values, key):
    value = values.get(key)
    if isinstance(value, dict) and value.get("status") == "known":
        return Decimal(value["value"])
    return None


def money(value):
    return {
        "status": "unknown" if value is None else "known",
        "value": None if value is None else decimal_string(value),
        "unit": {"code": "TOMAN", "version": 1},
    }


def evaluate(kind, raw):
    if kind not in schemas.KINDS:
        raise Fault("نوع خدمت معتبر نیست.", field="kind")
    effective, missing = schemas.effective(kind, raw)
    v = effective
    result = {
        "kind": kind,
        "schema_version": 1,
        "rule_version": 1,
        "effective": v,
        "missing": missing,
        "fields": list(schemas.current_fields(kind, raw).values()),
        "checks": [],
        "barriers": [],
        "conditions": [],
        "calculations": {},
        "entries": [],
        "verified": False,
        "irr": None,
        "success_probability": None,
        "expert_request_allowed": True,
        "next": "مدارک و حدود خدمت را برای بررسی کارشناس تکمیل کنید.",
    }
    checks, barriers, conditions = result["checks"], result["barriers"], result["conditions"]
    if kind == "proposal":
        if v.get("land") in ["dispute", "none"]:
            barriers.append(
                "حق یا امکان استفاده از زمین و دارایی پیش از تعهد نهایی تعیین تکلی"
                "ف شود؛ درخواست کمک برای رفع مانع مجاز است."
            )
        if v.get("need") == "loan" and v.get("revenue") in [None, "unknown", "donation"]:
            barriers.append("برای تامین مالی بازپرداخت‌پذیر، منبع بازپرداخت معتبر هنوز روشن نیست.")
        if v.get("need") == "operator":
            checks.append(
                "مسیر O&M؛ شرح خدمت، حق\u200cالزحمه، مسئول پرداخت و نگ"
                "هداری مستقل از تامین مالی ساخت مشخص شوند."
            )
        if v.get("need") == "support" or v.get("revenue") == "donation":
            checks.append("مسیر حمایتی و پوشش هزینه؛ بازده تجاری فرض نمی‌شود.")
        if v.get("utilities") == "pending":
            checks.append("تامین زیرساخت و هزینه و مسئول اجرای آن پیش‌نیاز بررسی است.")
        if v.get("stage") in ["idea", "study"]:
            checks.append(
                "ابتدا امکان\u200cسنجی، اطلاعات فنی و مطالعات لازم تکمیل شوند؛ انتخاب ق"
                "طعی تامین مالی زودهنگام است."
            )
        checks.extend(
            [
                "مجوزها، حقوق زمین، منبع درآمد، بهره‌بردار و اسناد همان طرح مستقلاً بررسی شوند.",
                (
                    "کسری اعلامی، منابع موجود و نیاز کل سه مفهوم مستق"
                    "ل\u200cاند؛ منابع احتمالی، وجه نقد آماده نیستند."
                ),
            ]
        )
        resources, need = number(v, "existing_resources"), number(v, "total_need")
        with localcontext() as ctx:
            ctx.prec = 80
            difference = need - resources if need is not None and resources is not None else None
        result["calculations"]["resource_difference"] = {
            **money(difference),
            "meaning": "unknown"
            if difference is None
            else "deficit"
            if difference > 0
            else "surplus"
            if difference < 0
            else "balanced",
        }
    elif kind == "ideas":
        checks.extend(
            [
                (
                    "شرح ایده، مرحله توسعه، نیاز، سرمایه اعلامی و مدا"
                    "رک برای بررسی کارشناس آماده می\u200cشوند."
                ),
                "دریافت بسته و ذخیره پیش‌نویس، ارسال درخواست یا پذیرش ایده نیستند.",
            ]
        )
    elif kind == "land-preparation":
        answers = {
            k.removeprefix("answer_"): val for k, val in v.items() if k.startswith("answer_")
        }
        added = {t["id"]: t for t in schemas.SOURCE[kind]["service_types"]}
        for key in v.get("types", []):
            typ = added[key]
            if key in advisories.CONFIGS:
                allowed = {q["id"] for q in advisories.questions(key, {}, all_fields=True)}
                a = {k: value for k, value in answers.items() if k in allowed}
                # Additional-service owner options are not guessed into a technical owner type.
                if a.get("owner") in ["endowment", "unknown"]:
                    a.pop("owner")
                g = advisories.evaluate(
                    key,
                    a,
                    "unknown" if number(v, "budget") is None or v.get("role") == "owner" else "own",
                )["guidance"]
                if v.get("role") == "contractor" and not g["blocked"]:
                    g.update(
                        models=[
                            "قرارداد خدمات مطالعات و طراحی آماده‌سازی"
                            if key == "lhstudy"
                            else "پیمان اجرای بسته مشخص آماده‌سازی"
                        ],
                        why=(
                            "مسیر شما اجرای کار است؛ صلاحیت، ظرفیت، دامنه پیم"
                            "ان، پرداخت کارفرما و تضمین\u200cها بررسی شوند."
                        ),
                        finance=[
                            "منبع پرداخت کارفرما طبق اعتبار و قرارداد معتبر",
                            "نقدینگی اجرای پیمانکار، مستقل از هزینه کل پروژه",
                        ],
                    )
            else:
                g = {
                    "models": [typ["output"]],
                    "checks": typ["checks"],
                    "why": typ["examples"],
                    "next": typ["output"],
                    "finance": ["دامنه، حق‌الزحمه و هزینه‌های پیگیری طبق توافق معتبر مشخص شوند."],
                    "blocked": False,
                }
                if answers.get("lpServiceRight") == "disputed":
                    g["checks"] = g["checks"] + [
                        (
                            "خدمات رفع مانع از تعهد عملیات جداست؛ اختلاف به م"
                            "عنی منع درخواست بررسی حقوقی نیست."
                        )
                    ]
            result["entries"].append({"id": key, "name": typ["name"], **g})
            checks.extend(g["checks"])
            if g["blocked"]:
                barriers.append("تعهد اجرایی «" + typ["name"] + "» تا رفع مانع اعلامی متوقف بماند.")
        conditions.append(
            "ترتیب خدمات اولویت انتخابی شماست؛ برنامه اجرا و وابستگی\u200cها، مسئول"
            "، هزینه، زمان و معیار تحویل هر جزء جدا بررسی شوند."
        )
        if v.get("role") == "owner":
            conditions.append("کسری منابع معرفی‌شده سرمایه قابل تعهد شما فرض نمی‌شود.")
        if v.get("role") == "explore":
            conditions.append("توان مالی در این مسیر شناخت سنجیده نشده است.")
    elif kind == "foreign-investment":
        foreign(v, result)
    elif kind == "ma-notice":
        result["passport"] = {
            "project": v.get("project"),
            "official_notice_id": None,
            "verified": False,
            "milestones": [
                {"step": s, "status": "نیازمند استعلام اسناد معتبر"}
                for s in [
                    "دریافت اسناد",
                    "ارائه پیشنهاد",
                    "تحویل اصل تضمین در صورت الزام",
                    "بارگذاری تضمین در صورت الزام",
                    "گشایش و بررسی پیشنهادها",
                ]
            ],
            "scope": [
                "مسئول اخذ مجوز و طراحی",
                "آورده، تامین منابع و اجرای کار",
                "بهره‌برداری و نگهداری در صورت شمول",
                "تحویل، پایان‌کار و اسناد مالکیت",
            ],
            "self_marked_count": len(v.get("ready", [])),
        }
        if v.get("project") == "REF-SIROS5":
            example = json.loads(Path(__file__).with_name("notice-example.json").read_text())
            result["passport"].update(
                example=example,
                scope=example["scope"],
                milestones=[
                    {"step": x, "status": y + " — فقط الگوی تاریخی، وضعیت جاری احراز نشده"}
                    for x, y in example["milestones"]
                ],
            )
        checks.extend(
            [
                (
                    "آخرین اسناد، اصلاحیه\u200cها، مهلت\u200cها، تضمین، امضای الکترونیکی و صلاحی"
                    "ت مرتبط از درگاه همان فراخوان دریافت و تطبیق شوند."
                ),
                (
                    "تعداد علامت\u200cهای شما درصد موفقیت یا احراز صلاحیت نیست؛ پیگیری داخل"
                    "ی ارائه رسمی پیشنهاد در درگاه دیگر نیست."
                ),
            ]
        )
    elif kind == "ma-renewal":
        checks.extend(
            [
                "حقوق مالکان و مستاجران، رضایت‌ها، اختیار تجمیع و توافق تخلیه و بازگشت بررسی شوند.",
                (
                    "محدوده با نقشه مصوب یا پاسخ مرجع ذی\u200cصلاح تطبیق د"
                    "اده شود؛ استعلام خودکار انجام نمی\u200cشود."
                ),
                "مشوق، ضوابط ساخت و تسهیلات با مصوبه همین ملک و صلاحیت و ظرفیت شریک بررسی شوند.",
            ]
        )
        if v.get("gis") == "inside" and (not v.get("authority") or not v.get("evidenceDate")):
            checks.insert(0, "داخل محدوده بودن خوداظهاری است؛ مرجع و تاریخ استعلام هنوز کامل نیست.")
        if v.get("gis") == "outside":
            barriers.append(
                "شمول برنامه ویژه بازآفرینی تایید نمی\u200cشود؛ نوسازی"
                " عادی و درخواست بررسی مستقل ممکن است."
            )
        if v.get("incentive") == "available" and not v.get("incentiveRef"):
            checks.append("مستند مشوق ثبت نشده؛ میزان و تعلق آن احراز نمی‌شود.")
        deposit = rent = None
        if v.get("displacement") == "yes":
            h, m, d, r = (number(v, k) for k in ["households", "months", "deposit", "rent"])
            if h == 0:
                raise Fault(
                    (
                        "برای اسکان موقت تعداد خانوار باید بیشتر از صفر باشد؛ اگر معلوم نی"
                        "ست وضعیت نامعلوم را انتخاب کنید."
                    ),
                    field="households",
                )
            with localcontext() as ctx:
                ctx.prec = 110
                deposit = h * d if h is not None and d is not None else None
                rent = h * r * m if h is not None and r is not None and m is not None else None
            if v.get("payer") in [None, "unknown"]:
                checks.append("مسئول تامین ودیعه و اجاره پیش از تعهد ساخت مشخص شود.")
            conditions.append(
                "ودیعه قابل بازگشت از اجاره دوره جداست؛ جمع، هزینه خالص نیست. ماه "
                "تقویمی روزسازی نشده و کمک/وام کسر نشده است؛ جابه\u200cجایی و خسارت در "
                "این دو عدد نیستند."
            )
        result["calculations"].update(deposit_total=money(deposit), rent_total=money(rent))
    elif kind == "ma-manager":
        checks.extend(
            [
                (
                    "اختیار مالک و حدود نمایندگی مدیر در انتخاب مستاجر، امضا، دریافت و"
                    "جوه و پیگیری مطالبات مشخص شوند."
                ),
                (
                    "حق\u200cالزحمه، خدمات مشمول و هزینه\u200cهای خارج قرارداد،"
                    " تعمیرات و منابع جاری و تسویه تعیین شوند."
                ),
                "شاخص وصول اجاره، خالی‌ماندن، پاسخ تعمیرات و گزارش‌دهی تعیین شوند.",
                "صلاحیت تیم، دسترسی به داده مستاجر و محرمانگی و نگهداری اسناد بررسی شوند.",
            ]
        )
    elif kind == "ma-exchange":
        checks.extend(
            [
                "حقوق دارایی، رهن، بدهی، تصرف و حقوق مستاجر و اشخاص ثالث بررسی شوند.",
                (
                    "ارزش خوداظهاری تایید نشده؛ هر دو دارایی و هزینه "
                    "انتقال باید مستقل ارزش\u200cگذاری شوند."
                ),
                "دارایی مطلوب متن است؛ ارزش طرف مقابل موجود نیست و تفاضل عددی محاسبه نمی‌شود.",
            ]
        )
        result["calculations"]["value_difference"] = money(None)
    elif kind == "charity":
        cause = schemas.SOURCE[kind].get("causes", {}).get(v.get("cause"), {})
        result["impact"] = {
            "status": "needs_expert_estimate",
            "value": None,
            "coefficient": None,
            "outcome": cause.get("outcome"),
            "unit": cause.get("unit"),
            "sources": cause.get("sources", []),
            "limit": cause.get("limit"),
        }
        if v.get("demo"):
            result["educational_example"] = {
                "label": ("فقط نمونه آموزشی فرضی؛ مربوط به محل و کمک شما نیست"),
                "formula": cause.get("formula"),
                "actual_impact": None,
            }
        if cause.get("condition"):
            checks.append(cause["condition"])
        checks.extend(
            [
                (
                    "ضریب مستند محلی موجود نیست؛ اثر نیازمند برآورد ک"
                    "ارشناس است و IRR یا سود مالی محاسبه نمی\u200cشود."
                ),
                "ظرفیت خدمت با افراد یکتا و اثر قطعی یکی نیست؛ دوره از آغاز بهره‌برداری خدمت است.",
            ]
        )
        if v.get("type") != "cash" and any(
            k in v for k in ["noncash_capacity", "noncash_unit", "noncash_period"]
        ):
            missing.extend(
                k for k in ["noncash_capacity", "noncash_unit", "noncash_period"] if k not in v
            )
    if kind in ["ma-notice", "ma-renewal", "ma-manager"]:
        result["qualification"] = {
            "title": "صلاحیت مرتبط با همان فرصت",
            "text": (
                "نوع گواهینامه، مرجع صادرکننده، شماره، تاریخ اعتب"
                "ار، ظرفیت و وضعیت استعلام جدا ثبت و بررسی شوند. "
                "در پروژه\u200cهای مربوط، صلاحیت موضوع ماده۴ نیز می\u200cتو"
                "اند مطرح باشد؛ برای همه پروژه\u200cها الزامی فرض نمی\u200c"
                "شود."
            ),
            "profile": "/tools/ma-profile",
            "source": "https://udrc.ir/حقوق-شهروندی/made4_list",
        }
    result["checks"] = list(dict.fromkeys(checks))
    result["assessment_blocked"] = bool(barriers)
    result["ready_to_submit"] = not missing
    return result


def foreign(v, result):
    checks, barriers, conditions = (result[k] for k in ["checks", "barriers", "conditions"])
    route = v.get("route")
    checks.extend(
        [
            "اسناد معرفی متقاضی، منشأ منابع و امکان عملی انتقال ارز یا تجهیزات بررسی شوند.",
            "مجوز تخصصی، اختیار طرف ایرانی و شیوه مجاز انتخاب شریک یا مجری احراز شوند.",
            "ارز درآمد و هزینه و ریسک نرخ و بازگشت منابع جدا بررسی شوند؛ تبدیل ارز انجام نشده است.",
        ]
    )
    route_checks = {
        "equity": [
            (
                "ساختار شرکت، ترکیب سهام، ارزش\u200cگذاری آورده، حاکمی"
                "ت شرکتی، تقسیم منافع و خروج تعیین شوند."
            ),
            "پذیرش و ثبت آورده نقدی و غیرنقدی در چارچوب مجوز بررسی شود.",
        ],
        "contract": [
            "دامنه تعهد، دوره، حق بهره‌برداری، تقسیم ریسک و تکلیف دارایی در پایان تعیین شوند.",
            (
                "در بررسی بند ب ماده۳ فیپا، بازیافت منابع از عملک"
                "رد اقتصادی طرح و شرایط همان بند بررسی شود."
            ),
        ],
        "credit": [
            (
                "اعتباردهنده و گیرنده، ارز، کارمزد، نرخ، تنفس و برنامه پرداخت و با"
                "زپرداخت در موافقت\u200cنامه مشخص شوند."
            ),
            "پذیرش بانک، مجوز تعهد و تضمین و امکان انتقال و بازپرداخت بررسی شوند.",
        ],
        "execution": [
            (
                "صلاحیت، سوابق، خدمات، برنامه اجرا، مسئولیت، تضمین و پرداخت مشخص ش"
                "وند؛ تعهد مالی از اجرای کار جداست."
            )
        ],
        "support": [
            "نیاز محلی، داده پایه، جامعه هدف و محدوده با منبع و تاریخ مستند شوند.",
            "خروجی، شاخص اثر، اندازه‌گیری و مسئول گزارش مشخص شوند.",
            "بودجه مطالعات، اجرا، نگهداری و آورده داخلی و استمرار خدمت جدا ثبت شوند.",
            "اهلیت مجری، برنامه معتبر، شرایط پذیرش، مصارف مجاز و گزارش‌دهی احراز شوند.",
        ],
    }
    checks.extend(route_checks.get(route, []))
    if route != "support":
        if v.get("rights") == "direct":
            barriers.append(
                "هدف تملک زمین به نام سرمایه\u200cگذار خارجی در چارچوب فیپا نیازمند باز"
                "نگری حقوقی است؛ این راهنما مجوز انتقال نیست."
            )
        if v.get("rights") == "unknown":
            barriers.append("حقوق زمین و دارایی پیش از انتخاب قطعی روش روشن شود.")
        if v.get("revenue") in [None, "unknown"]:
            barriers.append(
                "منبع بازگشت یا پرداخت معلوم نیست؛ قابلیت تامین مالی نتیجه\u200cگیری نمی\u200cشود."
            )
        if v.get("permit") != "reported":
            checks.append("مرجع، فهرست و وضعیت مجوزهای پروژه تعیین شوند.")
        if v.get("license") == "issued":
            checks.append(
                "اصل فیپا، شرایط، مهلت و آورده مصوب با سرمایه واقعاً واردشده تطبیق"
                " داده شوند؛ خوداظهاری تایید نیست."
            )
        elif route != "execution" or v.get("specific_execution_commitment") != "no":
            checks.append("امکان و ضرورت مجوز فیپا جدا از مجوز تخصصی بررسی شود.")
        if v.get("license") == "not-investment" and route != "execution":
            barriers.append("وضعیت همکاری اجرایی بدون سرمایه با مسیر مالی هماهنگ نیست.")
    else:
        if v.get("specific_support_continuity") == "unknown":
            barriers.append("برنامه استمرار و نگهداری پیش از تعهد منابع تکمیل شود.")
        if v.get("specific_support_supportType") == "unknown":
            barriers.append("کمک بلاعوض، خدمت فنی و اعتبار بازپرداخت‌پذیر تفکیک شوند.")
        if v.get("rights") == "direct":
            barriers.append("حمایت توسعه‌ای مجوز تملک زمین ایجاد نمی‌کند؛ هدف حقوقی بازنگری شود.")
        if v.get("specific_support_beneficiaries"):
            conditions.append("تعداد بهره‌مندان برآورد خوداظهاری است؛ اثر واقعی تایید نشده است.")
    if route == "equity" and v.get("contributions") == ["services"]:
        barriers.append("پذیرش خدمت به‌عنوان سرمایه و ارزش‌گذاری و تعهد مالی احراز شود.")
    if v.get("specific_equity_risk") == "low":
        checks.append("ریسک‌پذیری کم با ریسک واقعی ساخت، تقاضا و ارز تطبیق داده شود.")
    if v.get("specific_credit_guarantee") == "state":
        barriers.append("تضمین دولتی درخواست است؛ اختیار و مجوز صدور احراز نشده است.")
    if v.get("rights") == "public":
        checks.append(
            "اختیار واگذاری دارایی عمومی و حقوق قابل اعطا احراز شوند؛ انتقال خودکار نیست."
        )
    if not v.get("country"):
        checks.append("کشور مبدا و مسیر عملی انتقال و بازگشت هنوز تعیین نشده است.")
    if v.get("source_kind") in [None, "unknown"]:
        checks.append("نوع و هویت منبع یا حامی تعیین نشده؛ معرفی نهاد به معنی تعهد آن نیست.")
    if v.get("insurance") == "yes":
        checks.append(
            "بیمه‌گر، ذی‌نفع، ریسک، سقف، مدت، استثنا و هزینه احراز شوند؛ صدور تضمین فرض نشود."
        )
    if v.get("blended") or v.get("specific_support_supportType") == "blended":
        checks.append("سهم حمایت و سرمایه تجاری، شروط، قراردادها و تخصیص ریسک جدا طراحی شوند.")
    if route == "credit" and "credit" not in v.get("contributions", []):
        conditions.append("آورده شامل اعتبار نیست؛ نقش تامین‌کننده و منشأ اعتبار روشن شود.")
    if route == "execution" and v.get("specific_execution_settlement") == "operation":
        checks.append(
            "دریافت از بهره‌برداری نیازمند بررسی ساختار سرمایه‌گذاری قراردادی و حق معتبر است."
        )
    if (
        route == "support"
        and v.get("source_kind") in ["bank", "private"]
        and v.get("specific_support_supportType") == "grant"
    ):
        conditions.append("کمک از طرف تجاری نیازمند برنامه یا تعهد روشن است.")
    if v.get("sector") in ["land", "landhousing"]:
        checks.append(
            "حقوق زمین، هزینه شبکه‌ها، تحویل و جبران هزینه از فروش مجاز یا پرداخت مستقل تعیین شوند."
        )
    references = json.loads(Path(__file__).with_name("international-references.json").read_text())
    sector = v.get("sector")
    topic = (
        v.get("specific_support_focus")
        if route == "support"
        else (
            "housing"
            if sector in ["land", "landhousing"]
            or sector == "building"
            and v.get("type") == "residential"
            else "disaster"
            if sector == "building" and v.get("type") == "medical"
            else {
                "transport": "transport",
                "energy": "energy",
                "water": "basic",
                "heritage": "heritage",
            }.get(sector, "urban")
        )
    )
    category = "development" if route == "support" else "finance" if route == "credit" else None
    result["references"] = [
        r for r in references["sources"] if r["kind"] == category and topic in r["topics"]
    ]
    result["reference_library"] = references["sources"]
    result["historical_examples"] = references["cases"]
    amount = v.get("amount")
    if amount and v.get("currency") and amount["currency"]["code"] != v["currency"]:
        raise Fault("ارز مبلغ با ارز انتخابی یکسان نیست.", field="amount.currency")
    conditions.append(
        "مدت و نرخ پیشنهادی و دوره تنفس هدف خوداظهاری\u200cاند؛ بدون جریان نقدی"
        " بازگشت/IRR تولید نمی\u200cشود و ماه به روز تبدیل نشده است."
    )
    result["next"] = (
        "دامنه، حقوق دارایی، اهلیت طرفین، مدارک و منبع پرداخت یا حمایت پیش"
        " از تعهد از مرجع مربوط بررسی شوند."
    )
