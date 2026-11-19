"""Versioned Persian document presentation; never consult live data when re-rendering history."""

import html
import json
from pathlib import Path

from apps.workspace.other_schema import fields as schema_fields

STEPS = json.loads(Path(__file__).with_name("guide-steps-v1.json").read_text())
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


def metadata(opportunity):
    definitions = schema_fields(opportunity["kind"])
    return {
        key: {"label": f["label"], "options": f.get("options") or {}}
        for key, f in definitions.items()
    }


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
                + " "
                + UNITS.get(code, code)
                + ("؛ مبنا: " + display(value["basis"], {}) if value.get("basis") else "")
            )
        # Preserve historical basis without inventing conversion or missing details.
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
        return "؛ ".join(labels.get(k, k) + ": " + display(v, {}) for k, v in value.items())
    if isinstance(value, list):
        return "، ".join(display(v, options) for v in value)
    if isinstance(value, bool):
        return "بله" if value else "خیر"
    return (
        str(options.get(str(value), TERMS.get(str(value), value)))
        if value is not None
        else "ثبت نشده"
    )


def render(snapshot):
    def esc(value):
        return html.escape(str(value), quote=True)
    opportunity = snapshot.get("opportunity", {})
    fields = opportunity.get("fields", {})
    context = snapshot.get("guide_context", {})
    effective = snapshot.get("effective_advisory", {})
    definitions = snapshot.get("field_labels") or (
        metadata(opportunity) if opportunity.get("kind") in ("project", "fund", "sale") else {}
    )
    checked = context.get("checked", [])
    guidance = effective.get("guidance", {})
    checks = guidance.get("checks", [])
    # These static texts are versioned source content, not live opportunity data.
    steps = snapshot.get("action_steps", [])
    missing = []
    if not steps:
        missing.append(
            "گام‌های اقدام در داده تاریخی این گزارش ثبت نشده است؛ از اطلاعات زنده بازسازی نشد."
        )
    selected = []
    for item in checked:
        if item.startswith(("pre-", "step-")) and item.split("-")[-1].isdigit():
            source = checks if item.startswith("pre-") else steps
            index = int(item.split("-")[-1])
            if index < len(source):
                selected.append(source[index])
            else:
                missing.append("متن یکی از موارد علامت‌زده در snapshot تاریخی موجود نیست.")
        else:
            selected.append(item)

    def rows(items):
        return (
            "<dl>"
            + "".join("<div><dt>" + esc(k) + "</dt><dd>" + esc(v) + "</dd></div>" for k, v in items)
            + "</dl>"
        )

    def checklist(items):
        return (
            '<ul class="check">'
            + "".join(
                '<li><label><input type="checkbox" data-k="'
                + esc(v)
                + '"'
                + (" checked" if v in selected else "")
                + "><i></i>"
                + esc(v)
                + "</label></li>"
                for v in items
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

    title = fields.get("title", opportunity.get("title", "راهنمای اقدام"))
    section(
        "پروژه در یک نگاه",
        rows(
            [
                ("عنوان", title),
                (
                    "نوع",
                    {"project": "پروژه", "fund": "صندوق", "sale": "فروش"}.get(
                        opportunity.get("kind"), "ثبت نشده"
                    ),
                ),
                ("نسخه فرصت", opportunity.get("revision", "ثبت نشده")),
            ]
        ),
    )
    mine = list(context.get("mine", []))
    if context.get("kind") in FOLLOWUP:
        mine.insert(0, ("نوع پیگیری", FOLLOWUP[context["kind"]]))
    section(
        "شرایط شما",
        "<p>شرایط ثبت‌شده شما</p>" + (rows(mine) if mine else "<p>شرایط تکمیلی ثبت نشده است.</p>"),
    )
    money = [
        (definitions[k]["label"], display(v, definitions[k].get("options", {})))
        for k, v in fields.items()
        if k in definitions
        and isinstance(v, dict)
        and v.get("unit", {}).get("code") in ("TOMAN", "MILLION_TOMAN", "BILLION_TOMAN")
    ]
    section(
        "مسیر پول",
        rows(money)
        if money
        else "<p>اطلاعات مالی در این snapshot ثبت نشده است؛ فرض مالی تازه‌ای اعمال نشده است.</p>",
    )
    section(
        "پیش از اقدام بدانید",
        "<p>کنترل‌های راهنمای مؤثر</p><p>"
        + esc(guidance.get("why", snapshot.get("warning", "تضمین سود نیست.")))
        + "</p>"
        + checklist(checks),
    )
    answers = effective.get("effective_answers", {})
    questions = effective.get("questions", [])
    answer_rows = [
        (
            q["label"],
            next(
                (o["label"] for o in q["options"] if o["value"] == answers.get(q["id"])),
                "پاسخ ثبت نشده",
            ),
        )
        for q in questions
    ]
    section(
        "پرسش‌هایی که باید پاسخشان را آماده کنید",
        "<p>پاسخ‌های مؤثر ثبت‌شده؛ نسخه قواعد پاسخ‌های مؤثر: "
        + esc(effective.get("version", "در تاریخچه ثبت نشده"))
        + "</p>"
        + rows(answer_rows),
    )
    dossier = [
        (
            definitions.get(k, {}).get("label", "فیلد تاریخی: " + k),
            display(v, definitions.get(k, {}).get("options", {})),
        )
        for k, v in fields.items()
    ]
    section("پرونده کامل", rows(dossier))
    section("گام‌های اقدام", checklist(steps))
    if selected:
        section("موارد بررسی‌شده", rows([("بررسی شد", v) for v in selected]))
    if not effective and context.get("answers"):
        missing.append(
            "نسخه قواعد و پاسخ‌های مؤثر تاریخی در دسترس نیست؛ پاسخ خام به‌عنوان مؤثر معرفی نشده است."
        )
    if missing:
        section("محدودیت داده تاریخی", "<p>" + esc(" ".join(dict.fromkeys(missing))) + "</p>")
    section(
        "رسید و مبنای ثابت گزارش",
        rows(
            [
                ("شناسه گزارش", snapshot.get("report_id", "ثبت نشده")),
                ("زمان ثبت", snapshot.get("created_at", "ثبت نشده")),
            ]
        ),
    )
    return (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>'
        + esc(title)
        + "</title><style>"
        + CSS
        + '</style></head><body><div class="sheet"><header class="doc-head">'
        '<div class="doc-logo">سرمایه‌گزین</div><p class="doc-kicker">راهنمای اقدام</p><h1>'
        + esc(title)
        + '</h1></header><main class="doc-body">'
        + "".join(sections)
        + '</main><footer class="doc-foot">'
        + esc(snapshot.get("warning", "این راهنما تضمین سود نیست."))
        + "<br>این دریافت پرونده یا درخواست تازه‌ای ایجاد نمی‌کند.</footer></div></body></html>"
    )
