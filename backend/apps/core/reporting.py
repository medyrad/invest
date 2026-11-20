"""Versioned Persian report rendering from immutable snapshots only."""

import copy
import html
import json
from pathlib import Path

STEPS = json.loads(Path(__file__).with_name("guide-steps-v1.json").read_text())
FIELD_DEFINITIONS = json.loads(
    Path(__file__).with_name("guide-fields-v1.json").read_text()
)
ROUTE_VOCABULARY = json.loads(
    Path(__file__).with_name("report-routes-v1.json").read_text()
)
ROUTE_LABELS = ROUTE_VOCABULARY["routes"]
SEARCH_ROUTE_CONTRACT = json.loads(
    Path(__file__).with_name("search_fields.json").read_text()
)
ALLOWED_REPORT_ROUTES = frozenset(
    route for field in SEARCH_ROUTE_CONTRACT for route in field.get("routes", [])
)
if set(ROUTE_LABELS) != ALLOWED_REPORT_ROUTES:
    raise RuntimeError("واژه‌نامه مسیر گزارش با قرارداد مسیرهای جست‌وجو همگام نیست.")
CSS = Path(__file__).with_name("guide-v1.css").read_text()
UNITS = {
    "TOMAN": "تومان",
    "MILLION_TOMAN": "میلیون تومان",
    "BILLION_TOMAN": "میلیارد تومان",
    "MONTH": "ماه",
    "YEAR": "سال",
    "DAY": "روز",
    "SQUARE_METRE": "مترمربع",
    "PERCENTAGE": "درصد",
    "SHARE_PERCENT": "درصد سهم",
    "ITEM": "عدد",
    "PERSON": "نفر",
    "TONNE": "تن",
}
FOLLOWUP = {
    "visit": "بررسی امکان بازدید",
    "documents": "درخواست بررسی اسناد و شرایط",
    "interest": "اعلام علاقه‌مندی به همکاری",
}
TERMS = {
    "unknown": "نامعلوم",
    "not_applicable": "نامربوط",
    "irr": "بازده داخلی IRR",
    "simple_rate": "نرخ ساده",
    "effective_rate": "نرخ مؤثر",
    "annual": "سالانه",
    "monthly": "ماهانه",
    "total": "کل دوره",
    "nominal": "اسمی",
    "real": "واقعی",
    "project": "پروژه",
    "investor": "سرمایه‌گذار",
    "forecast": "پیش‌بینی",
    "observed": "عملکرد",
    "claimed": "ادعایی",
    "unspecified": "اعلام نشده",
}
KIND_LABELS = {"project": "پروژه", "fund": "صندوق", "sale": "فروش"}
IDENTITY_KEYS = {
    "title",
    "description",
    "group",
    "subtype",
    "category",
    "phase",
    "stage",
    "model",
    "model_id",
    "usage",
    "fund_kind",
    "fund_type",
    "asset_sector",
    "building_type",
    "scrap_type",
    "subject",
}
LOCATION_KEYS = {"province", "county", "city", "neighborhood"}
MONEY_TIME_KEYS = {
    "min_capital",
    "budget",
    "monthly_rent",
    "working_capital_min",
    "purchase_price",
    "deposit",
    "lump_rent",
    "minimum_investment",
    "price",
    "price_mode",
    "price_quantity",
    "area",
    "land_area",
    "quantity",
    "metric_quantity",
    "execution_months",
    "payback_years",
    "payback_downside_years",
    "lockup_months",
    "first_income_months",
    "duration_years",
    "duration_months",
    "heritage_years",
    "operator_work_period",
    "partner_share",
    "government_share",
    "irr",
    "forecast",
    "forecast_irr",
    "forecast_simple_rate",
    "forecast_effective_rate",
    "payout",
    "income",
}


def metadata(opportunity):
    """Return the frozen v1 label/option dictionary, never a live catalog definition."""

    return copy.deepcopy(FIELD_DEFINITIONS.get(opportunity.get("kind"), {}))


def display(value, options):
    if isinstance(value, dict):
        if value.get("status") in ("unknown", "not_applicable"):
            return "نامعلوم" if value["status"] == "unknown" else "نامربوط"
        unit = value.get("source_unit", value.get("unit", {}))
        code = unit.get("code", "") if isinstance(unit, dict) else unit
        number = value.get("source_value", value.get("value"))
        if number is not None:
            return (
                str(number)
                + (" " + UNITS.get(code, code) if code else "")
                + (
                    "؛ مبنا: " + display(value["basis"], {})
                    if value.get("basis")
                    else ""
                )
            )
        labels = {
            "version": "نسخه",
            "start_basis": "مبدأ دوره",
            "basis_date": "تاریخ مبنا",
            "period": "دوره",
            "horizon": "افق",
            "source": "منبع",
            "scope": "دامنه",
            "price_basis": "مبنای قیمت",
            "metric_type": "نوع شاخص",
            "observation": "نوع مشاهده",
        }
        return "؛ ".join(
            labels.get(key, key) + ": " + display(item, {})
            for key, item in value.items()
        )
    if isinstance(value, list):
        return "، ".join(display(item, options) for item in value)
    if isinstance(value, bool):
        return "بله" if value else "خیر"
    return (
        str(options.get(str(value), TERMS.get(str(value), value)))
        if value is not None
        else "ثبت نشده"
    )


def render(snapshot):
    """Render v1 legacy snapshots or non-frozen previews without reading live data."""

    def esc(value):
        return html.escape(str(value), quote=True)

    opportunity = snapshot.get("opportunity") or {}
    fields = opportunity.get("fields") or {}
    context = snapshot.get("guide_context") or {}
    effective = snapshot.get("effective_advisory") or {}
    frozen_labels = snapshot.get("field_labels")
    definitions = frozen_labels or metadata(opportunity)
    guidance = effective.get("guidance") or {}
    checks = [str(item) for item in guidance.get("checks") or []]
    steps = [str(item) for item in snapshot.get("action_steps") or []]
    missing = []

    if not frozen_labels:
        missing.append(
            "برچسب فیلدها در snapshot قالب تاریخی نسخه ۱ ذخیره نشده بود؛ "
            "فقط واژه‌نامه ایستای همان قالب استفاده شد و نام زنده‌ای خوانده نشد."
        )
    if not steps:
        missing.append(
            "گام‌های اقدام در داده تاریخی این گزارش ثبت نشده است؛ از اطلاعات زنده بازسازی نشد."
        )
    if not snapshot.get("report_id"):
        missing.append("شناسه گزارش در شکل قدیمی snapshot ذخیره نشده بود.")

    selected = []
    for item in context.get("checked") or []:
        item = str(item)
        if item.startswith(("pre-", "step-")) and item.rsplit("-", 1)[-1].isdigit():
            source = checks if item.startswith("pre-") else steps
            index = int(item.rsplit("-", 1)[-1])
            if index < len(source):
                selected.append(source[index])
            else:
                missing.append("متن یکی از موارد علامت‌زده در snapshot تاریخی موجود نیست.")
        else:
            selected.append(item)

    def value_for(key, value):
        definition = definitions.get(key, {})
        options = definition.get("options") or {}
        if key in LOCATION_KEYS and value not in (None, "") and str(value) not in options:
            missing.append(
                "نام فارسی یکی از موقعیت‌های تاریخی در snapshot ذخیره نشده است؛ "
                "فقط شناسه تاریخی نمایش داده شد."
            )
            return "شناسه تاریخی: " + str(value)
        return display(value, options)

    def row_list(items):
        return "".join(
            '<div class="row"><span>'
            + esc(label)
            + "</span><strong>"
            + esc(value)
            + "</strong></div>"
            for label, value in items
        )

    def card(title, items, note=""):
        return (
            '<div class="card"><h3>'
            + esc(title)
            + "</h3>"
            + (('<p class="card-note">' + esc(note) + "</p>") if note else "")
            + row_list(items)
            + "</div>"
        )

    def checklist(items):
        return (
            '<ul class="check">'
            + "".join(
                '<li><label><input type="checkbox" data-k="'
                + esc(value)
                + '"'
                + (" checked" if value in selected else "")
                + "><i></i>"
                + esc(value)
                + "</label></li>"
                for value in items
            )
            + "</ul>"
        )

    sections = []

    def section(title, body):
        sections.append(
            "<section><h2><b>"
            + str(len(sections) + 1)
            + "</b>"
            + esc(title)
            + "</h2>"
            + body
            + "</section>"
        )

    title = value_for("title", fields.get("title", opportunity.get("title", "راهنمای اقدام")))
    overview_groups = []
    for group_title, keys in [
        ("مشخصات فرصت", IDENTITY_KEYS),
        ("موقعیت", LOCATION_KEYS),
        ("مبلغ و زمان", MONEY_TIME_KEYS),
    ]:
        rows = [
            (
                definitions.get(key, {}).get("label", "فیلد تاریخی: " + key),
                value_for(key, fields[key]),
            )
            for key in fields
            if key in keys
        ]
        if rows:
            overview_groups.append(card(group_title, rows))
    if not overview_groups:
        overview_groups.append(
            card(
                "مشخصات فرصت",
                [
                    ("عنوان", title),
                    ("نوع", KIND_LABELS.get(opportunity.get("kind"), "ثبت نشده")),
                    ("نسخه فرصت", opportunity.get("revision", "ثبت نشده")),
                ],
            )
        )
    section("پروژه در یک نگاه", '<div class="grid">' + "".join(overview_groups) + "</div>")

    mine = []
    if context.get("kind") in FOLLOWUP:
        mine.append(("نوع پیگیری", FOLLOWUP[context["kind"]]))
    for item in context.get("mine") or []:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            mine.append((str(item[0]), str(item[1])))
    section(
        "شرایط ثبت‌شده شما",
        ('<div class="mine">' + row_list(mine) + "</div>")
        if mine
        else '<p class="note">شرایط تکمیلی در این snapshot ثبت نشده است.</p>',
    )

    flow = []
    for key, label in [
        ("finance", "پول از کجا می‌آید"),
        ("repay", "چطور برمی‌گردد"),
        ("ownership", "مالکیت و سهم"),
    ]:
        if fields.get(key) not in (None, "", []):
            flow.append((label, value_for(key, fields[key])))
    money = [
        (
            definitions.get(key, {}).get("label", "فیلد تاریخی: " + key),
            value_for(key, value),
        )
        for key, value in fields.items()
        if key in MONEY_TIME_KEYS
        and isinstance(value, dict)
        and (value.get("unit") or value.get("source_unit"))
    ]
    if flow:
        body = '<div class="flow" style="grid-template-columns:' + " auto ".join(
            "1fr" for _ in flow
        ) + '">'
        body += "".join(
            (('<div class="arrow">←</div>') if index else "")
            + '<div class="card"><h3>'
            + esc(label)
            + "</h3><p>"
            + esc(value)
            + "</p></div>"
            for index, (label, value) in enumerate(flow)
        )
        body += "</div>"
    elif money:
        body = card("مبلغ‌ها با واحد تاریخی", money)
    else:
        body = (
            '<p class="note">اطلاعات مالی در این snapshot ثبت نشده است؛ '
            "فرض مالی تازه‌ای اعمال نشده است.</p>"
        )
    section("مسیر پول", body)

    warning = guidance.get("why") or snapshot.get("warning") or "تضمین سود نیست."
    section(
        "پیش از اقدام بدانید",
        '<div class="note">' + esc(warning) + "</div>" + (checklist(checks) if checks else ""),
    )

    answers = effective.get("effective_answers") or {}
    questions = effective.get("questions") or []
    question_html = []
    for question in questions:
        question_id = question.get("id")
        options = question.get("options") or []
        answer = answers.get(question_id)
        chosen = next(
            (str(option.get("label")) for option in options if option.get("value") == answer),
            None,
        )
        question_html.append(
            '<div class="q"><p>'
            + esc(question.get("label", "پرسش تاریخی"))
            + "</p>"
            + (
                '<div class="ans"><b>پاسخ شما:</b> ' + esc(chosen) + "</div>"
                if chosen is not None
                else "<small>پاسخ مؤثری ثبت نشده است؛ گزینه‌ها: "
                + esc(" / ".join(str(option.get("label", "")) for option in options))
                + "</small>"
            )
            + "</div>"
        )
    section(
        "پاسخ‌های مؤثر ثبت‌شده",
        '<h3>کنترل‌های راهنمای مؤثر</h3>'
        '<p class="effective-version">نسخه قواعد پاسخ‌های مؤثر: '
        + esc(effective.get("version", "در تاریخچه ثبت نشده"))
        + "</p>"
        + (
            "".join(question_html)
            if question_html
            else '<p class="note">پرسش مؤثر نسخه‌داری در این snapshot موجود نیست.</p>'
        ),
    )

    dossier_groups = {"مشخصات و موقعیت": [], "مبلغ، زمان و بازده": [], "شرایط، حقوق و بررسی‌ها": []}
    for key, value in fields.items():
        item = (
            definitions.get(key, {}).get("label", "فیلد تاریخی: " + key),
            value_for(key, value),
        )
        if key in IDENTITY_KEYS or key in LOCATION_KEYS:
            dossier_groups["مشخصات و موقعیت"].append(item)
        elif key in MONEY_TIME_KEYS:
            dossier_groups["مبلغ، زمان و بازده"].append(item)
        else:
            dossier_groups["شرایط، حقوق و بررسی‌ها"].append(item)
    dossier_cards = [card(label, items) for label, items in dossier_groups.items() if items]
    section(
        "پرونده کامل",
        "".join(dossier_cards) or '<p class="note">فیلدی در snapshot موجود نیست.</p>',
    )

    section(
        "گام‌های اقدام",
        (
            '<ol class="steps">'
            + "".join(
                '<li><label><input type="checkbox" data-k="'
                + esc(value)
                + '"'
                + (" checked" if value in selected else "")
                + "><span>"
                + esc(value)
                + "</span><em></em></label></li>"
                for value in steps
            )
            + "</ol>"
        )
        if steps
        else '<p class="note">متن گام‌های اقدام در این snapshot تاریخی وجود ندارد.</p>',
    )
    if selected:
        section("موارد بررسی‌شده", card("ثبت تاریخی", [("بررسی شد", value) for value in selected]))
    if not effective and context.get("answers"):
        missing.append(
            "نسخه قواعد و پاسخ‌های مؤثر تاریخی در دسترس نیست؛ پاسخ خام به‌عنوان مؤثر معرفی نشده است."
        )
    meta = [KIND_LABELS.get(opportunity.get("kind"), "نوع ثبت نشده")]
    routes = opportunity.get("routes") or []
    if routes:
        route_labels = []
        for route in routes:
            route = str(route)
            if route in ROUTE_LABELS:
                route_labels.append(ROUTE_LABELS[route])
            else:
                route_labels.append("شناسه تاریخی ناشناخته: " + route)
                missing.append(
                    "واژه فارسی یکی از مسیرهای تاریخی در واژه‌نامه نسخه "
                    + str(ROUTE_VOCABULARY["version"])
                    + " موجود نیست؛ مسیر شناخته‌شده‌ای حدس زده نشد."
                )
        meta.append("مسیر: " + "، ".join(route_labels))
    if opportunity.get("revision"):
        meta.append("نسخه فرصت: " + str(opportunity["revision"]))

    if missing:
        section(
            "محدودیت داده تاریخی",
            '<div class="note historical-limit">'
            + esc(" ".join(dict.fromkeys(missing)))
            + "</div>",
        )
    section(
        "رسید و مبنای ثابت گزارش",
        card(
            "snapshot این سند",
            [
                ("شناسه گزارش", snapshot.get("report_id", "در شکل تاریخی ثبت نشده")),
                ("زمان ثبت", snapshot.get("created_at", "در شکل تاریخی ثبت نشده")),
                ("نسخه قالب", snapshot.get("template_version", 1)),
                ("نسخه فرصت", opportunity.get("revision", "ثبت نشده")),
            ],
            "دریافت دوباره از همین snapshot انجام می‌شود و پرونده تازه‌ای ایجاد نمی‌کند.",
        ),
    )

    mark = (
        '<svg viewBox="150 60 800 380" width="22" height="22" fill="none" '
        'stroke="currentColor" stroke-width="34" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M232 248C302 248 '
        "332 292 360 342C386 386 414 393 440 390C466 387 490 372 502 357L703 "
        '92V395M585 250H703M703 395C703 300 742 250 880 250"/></svg>'
    )
    node = (
        '<svg viewBox="60 70 1090 350" width="62" height="20" fill="none" '
        'stroke="currentColor" stroke-width="24" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true"><path d="M168 248H232C302 248 '
        "332 292 360 342C386 386 414 393 440 390C466 387 490 372 502 357L703 "
        '92V395"/><path d="M585 250H703M703 395C703 300 742 250 900 250H1042"/>'
        '<circle cx="120" cy="250" r="50" fill="currentColor" stroke="none"/>'
        '<circle cx="1087" cy="250" r="44"/></svg>'
    )
    return (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>راهنمای اقدام | '
        + esc(title)
        + "</title><style>"
        + CSS
        + '</style></head><body><div class="sheet"><header class="doc-head">'
        + '<div class="doc-brand"><span class="doc-logo"><i>'
        + mark
        + "</i><span>سرمایه‌گزین<small>سرمایه، تخصص و دارایی در مسیر خلق ارزش</small></span></span>"
        + '<span class="doc-stamp"><b>راهنمای اقدام</b>زمان ثبت snapshot: '
        + esc(snapshot.get("created_at", "ثبت نشده"))
        + "</span></div>"
        + '<p class="doc-kicker">'
        + node
        + "راهنمای اقدام</p><h1>"
        + esc(title)
        + '</h1><div class="doc-meta">'
        + "".join('<span class="pill">' + esc(item) + "</span>" for item in meta)
        + '</div></header><main class="doc-body">'
        + "".join(sections)
        + '</main><footer class="doc-foot"><span><b>سرمایه‌گزین</b><br>'
        + esc(snapshot.get("warning", "این راهنما تضمین سود نیست."))
        + '</span><span class="doc-foot-end">این فایل از snapshot تاریخی ساخته شده است'
        + "<br>این دریافت پرونده یا درخواست تازه‌ای ایجاد نمی‌کند."
        + "</span></footer></div></body></html>"
    )
