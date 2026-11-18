import base64
import html
import json
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from apps.core import cases
from apps.core.common import event, identifier, notify, run, text
from apps.core.models import Case, Message, Report
from apps.identity.models import User
from apps.workspace import service as ws
from apps.workspace.models import PrivateFile
from apps.workspace.schema import Fault, check_keys

from .evaluation import evaluate
from .models import ServiceSubmission
from .schemas import CATALOG, KINDS


def draft(user, id, lock=False):
    d = ws.target(user, "draft", id, lock=lock)
    if d.kind not in KINDS:
        raise Fault("این پیش‌نویس از نوع خدمت نیست.", field="kind")
    return d


def freeze(d):
    result = evaluate(d.kind, d.raw)
    attached = list(
        PrivateFile.objects.select_for_update().filter(
            draft=d,
            attached=True,
            deleted_at__isnull=True,
            replaced_at__isnull=True,
            purged_at__isnull=True,
        )
    )
    if any(f.status != "clean" for f in attached):
        raise Fault(
            (
                "پیوست\u200cهای فعال هنوز پاک و آماده نیستند؛ اسکن را پیگیری یا پیوند ف"
                "ایل را حذف کنید. متن پیش\u200cنویس قابل ذخیره است."
            ),
            field="files",
        )
    files = [str(f.pk) for f in attached]
    snapshot = {
        "subject_type": "service",
        "kind": d.kind,
        "title": d.raw.get("title") or CATALOG[d.kind]["name"],
        "draft_id": str(d.pk),
        "draft_version": d.version,
        "effective": result["effective"],
        "evaluation": result,
        "files": files,
        "file_manifest": [
            {"id": str(f.pk), "name": f.name, "media_type": f.media_type, "size": f.size}
            for f in attached
        ],
        "schema_version": 1,
        "rule_version": 1,
        "report_version": 1,
        "created_at": timezone.now().isoformat(),
        "assumptions": [
            "خوداظهاری و نیازمند بررسی؛ تایید حقوقی، مالی یا رسمی نیست.",
            "دریافت بسته ارسال درخواست نیست.",
        ],
    }
    return snapshot, result, files


def create_report(session, id, data):
    check_keys(data, ["key", "version"])
    user = session.user

    def work():
        d = draft(user, id, True)
        version(d, data)
        snapshot, _, _ = freeze(d)
        report = Report.objects.create(user=user, snapshot=snapshot)
        return {
            "id": str(report.pk),
            "download": "/api/v1/services/reports/"
            + str(report.pk)
            + ("/package" if snapshot["files"] else "/download"),
            "html_download": "/api/v1/services/reports/" + str(report.pk) + "/download",
            "submitted": False,
        }

    return run(user, data, "service_report", identifier(id), lambda: draft(user, id, True), work)


def version(d, data):
    if type(data["version"]) is not int or data["version"] != d.version:
        raise Fault(
            ("نسخه پیش\u200cنویس تغییر کرده؛ ورودی شما حفظ شده، نسخه سرور را بازبینی کنید."),
            409,
            "version",
        )


def submit(session, id, data):
    check_keys(data, ["key", "version", "text", "previous"])
    user = session.user

    def work():
        if settings.INVEST_ENV == "public":
            raise Fault("پذیرش عمومی هنوز فعال نشده است.", 503)
        d = draft(user, id, True)
        version(d, data)
        if d.organization_id and not ws.grant(user, d.organization_id):
            raise Fault("ارسال سازمانی به اختیار جاری تاییدشده نیاز دارد.", 403)
        body = text(data["text"], "text")
        prev = None
        if data["previous"]:
            prev = cases.get_case(session, data["previous"], True)
            if (
                prev.service_draft_id != d.pk
                or prev.status not in cases.TERMINAL
                or not cases.is_customer(user, prev)
            ):
                raise Fault("پیگیری مرتبط معتبر نیست.", field="previous")
        existing = Case.objects.filter(service_draft=d).exclude(status__in=cases.TERMINAL).first()
        if existing:
            return {
                "case": cases.dto(existing),
                "existing": True,
                "message": "پرونده فعال همین خدمت وجود دارد؛ پیام تازه خودکار اضافه نشد.",
            }
        snapshot, result, files = freeze(d)
        if result["missing"]:
            labels = {f["key"]: f["label"] for f in result["fields"]}
            raise Fault(
                ("پیش از ارسال پاسخ\u200cهای فعال لازم را کامل کنید: ")
                + "، ".join(labels.get(k, k) for k in result["missing"]),
                field="values",
                current={"missing": result["missing"]},
            )
        prior = ServiceSubmission.objects.filter(draft=d, draft_version=d.version).first()
        if prior and (prior.files != files or prior.snapshot["effective"] != result["effective"]):
            raise Fault(
                (
                    "پیوست یا داده مؤثر این نسخه تغییر کرده است؛ پیش\u200c"
                    "نویس را ذخیره و نسخه تازه را بازبینی کنید."
                ),
                409,
                "version",
            )
        sub, _ = ServiceSubmission.objects.get_or_create(
            draft=d,
            draft_version=d.version,
            defaults={
                "actor": user,
                "kind": d.kind,
                "snapshot": snapshot,
                "evaluation": result,
                "files": files,
            },
        )
        c = Case.objects.create(
            customer=user,
            service_draft=d,
            service_submission=sub,
            previous=prev,
            first_response_due=cases.due(timezone.now()),
        )
        Message.objects.create(case=c, actor=user, text=body)
        event(
            user,
            c.pk,
            "service_case_submitted",
            service=d.kind,
            draft=str(d.pk),
            submission=str(sub.pk),
        )
        notify(user, "درخواست خدمت با رسید ثبت شد.", "/requests/" + str(c.pk))
        for admin in User.objects.filter(role="admin", is_active=True):
            notify(admin, "درخواست خدمت برای ارجاع آماده است.", "/admin")
        return {"case": cases.dto(c), "existing": False, "submission": str(sub.pk)}

    return run(user, data, "service_submit", identifier(id), lambda: draft(user, id, True), work)


def get_report(user, id):
    r = Report.objects.filter(pk=identifier(id), snapshot__subject_type="service").first()
    if not r:
        raise Fault("گزارش پیدا نشد.", 404)
    # Current organization authority, rather than historical report creator, is authoritative.
    ws.target(user, "draft", r.snapshot["draft_id"], trash=True)
    return r


def report_html(report):
    snap, result = report.snapshot, report.snapshot["evaluation"]

    def esc(x):
        return html.escape(str(x), quote=True)

    units = {
        "TOMAN": "تومان",
        "MILLION_TOMAN": "میلیون تومان",
        "BILLION_TOMAN": "میلیارد تومان",
        "MONTH": "ماه",
        "YEAR": "سال",
        "DAY": "روز",
        "ITEM": "عدد",
        "SHARE_PERCENT": "درصد سهم",
        "PERCENTAGE": "درصد",
        "SESSION": "نوبت / جلسه خدمت",
        "SERVICE_HOUR": "ساعت خدمت",
        "SQUARE_METRE": "مترمربع",
    }

    def display(f, value):
        options = f.get("options") or {}
        if f.get("options_by_parent"):
            options = dict(f["options_by_parent"].get(snap["effective"].get(f.get("parent")), []))
        if isinstance(value, dict):
            if value.get("status") != "known":
                return "نامعلوم" if value.get("status") == "unknown" else "نامربوط"
            code = value.get("unit", value.get("currency", {})).get("code", "")
            return str(value.get("source_value")) + " " + units.get(code, code)
        if isinstance(value, list):
            return "، ".join(options.get(v, v) for v in value)
        if type(value) is bool:
            return "بله" if value else "خیر"
        return options.get(value, value)

    def listing(items):
        return "<ul>" + "".join("<li>" + esc(x) + "</li>" for x in items) + "</ul>"

    rows = "".join(
        "<div><dt>"
        + esc(f["label"])
        + "</dt><dd>"
        + esc(display(f, snap["effective"][f["key"]]))
        + "</dd></div>"
        for f in result["fields"]
        if f["key"] in snap["effective"]
    )
    body = "<h2>پاسخ‌های فعال در زمان تهیه</h2><dl>" + rows + "</dl>"
    if result["missing"]:
        labels = {f["key"]: f["label"] for f in result["fields"]}
        body += "<h2>موارد لازم برای ارسال</h2>" + listing(
            labels.get(k, k) for k in result["missing"]
        )
    labels = {
        "deposit_total": "ودیعه قابل بازگشت کل",
        "rent_total": "اجاره کل دوره",
        "resource_difference": "تفاوت نیاز کل و منابع موجود",
        "value_difference": "تفاوت ارزش دارایی‌ها",
    }
    for key, calculation in result["calculations"].items():
        body += (
            '<p class="note">'
            + esc(labels.get(key, key))
            + ": "
            + esc(calculation["value"] if calculation["value"] is not None else "نامعلوم")
            + " تومان</p>"
        )
    if result["barriers"]:
        body += (
            "<h2>مانع انتخاب قطعی ساختار یا تعهد</h2>"
            + listing(result["barriers"])
            + ("<p>درخواست کمک از کارشناس برای رفع مانع مجاز است.</p>")
        )
    for entry in result["entries"]:
        body += (
            "<section><h2>"
            + esc(entry["name"])
            + "</h2><p>"
            + esc(entry["why"])
            + "</p>"
            + listing(entry["models"])
            + listing(entry["checks"])
            + "<p>"
            + esc(entry["next"])
            + "</p></section>"
        )
    if result.get("impact"):
        impact = result["impact"]
        body += (
            ("<h2>اثر اجتماعی: نیازمند برآورد کارشناس</h2><p>")
            + esc(impact.get("outcome") or "")
            + "</p><p>"
            + esc(impact.get("limit") or "")
            + ("</p><p>ضریب مستند محلی موجود نیست؛ اثر عددی و IRR تولید نشده است.</p>")
        )
    if result.get("qualification"):
        q = result["qualification"]
        body += (
            "<h2>"
            + esc(q["title"])
            + "</h2><p>"
            + esc(q["text"])
            + '</p><a href="'
            + esc(q["source"])
            + ('">فهرست معرفی\u200cشده دارندگان صلاحیت ماده۴</a>')
        )
    if result.get("passport"):
        passport = result["passport"]
        example = passport.get("example", {})
        body += (
            "<dl>"
            + "".join(
                "<div><dt>"
                + esc(label)
                + "</dt><dd>"
                + esc(
                    example.get(key) or ("طبق اسناد همان فراخوان تعیین شود؛ هنوز احراز نشده است.")
                )
                + "</dd></div>"
                for key, label in [
                    ("officialNoticeId", "شناسه رسمی فراخوان"),
                    ("issuer", "دستگاه طرف قرارداد"),
                    ("published", "منبع و تاریخ انتشار"),
                    ("portal", "درگاه رسمی اقدام"),
                    ("signature", "ثبت‌نام و امضای الکترونیکی"),
                    ("qualification", "صلاحیت و ظرفیت ورود"),
                    ("guarantee", "تضمین شرکت و انجام تعهد"),
                ]
            )
            + "</dl>"
        )

        body += (
            ("<h2>پرونده ورود، صلاحیت و مهلت\u200cها</h2><p>تعداد علامت\u200cزده توسط شما: ")
            + esc(passport["self_marked_count"])
            + "؛ درصد موفقیت یا تایید صلاحیت نیست.</p>"
            + listing(x["step"] + ": " + x["status"] for x in passport["milestones"])
            + listing(passport["scope"])
        )
    body += (
        "<h2>بررسی‌های قدم بعد</h2>"
        + listing(result["checks"])
        + listing(result["conditions"])
        + "<p><b>قدم بعد: </b>"
        + esc(result["next"])
        + "</p>"
    )
    font = base64.b64encode(Path(__file__).with_name("report-font.woff2").read_bytes()).decode(
        "ascii"
    )
    mark = Path(__file__).with_name("report-brand.html").read_text()
    if snap.get("file_manifest"):
        body += (
            "<h2>پیوست‌های خصوصی ثبت‌شده در بسته</h2>"
            + listing(f["name"] for f in snap["file_manifest"])
            + (
                "<p>در بسته ZIP، محتوای پاک و مجاز همراه این سند "
                "است؛ دسترسی به گزارش و دریافت بسته در سامانه مجو"
                "ز جاری لازم دارد.</p>"
            )
        )
    css = (
        ("@font-face{font-family:Vazirmatn;src:url(data:font/woff2;base64,")
        + font
        + (") format('woff2');font-weight:100 900;font-display:swap}")
        + Path(__file__).with_name("report.css").read_text()
    )
    return (
        (
            '<!doctype html><html lang="fa" dir="rtl"><head><'
            'meta charset="utf-8"><meta name="viewport" conte'
            'nt="width=device-width,initial-scale=1"><title>'
        )
        + esc(snap["title"])
        + "</title><style>"
        + css
        + (
            (
                '</style></head><body><div class="sheet"><header '
                'class="doc-head"><div class="doc-brand"><span cl'
                'ass="doc-logo"><i>__BRAND_MARK__</i><span>سرمایه'
                "\u200cگزین<small>مشاور فرصت\u200cهای سرمایه\u200cگذاری</small><"
                '/span></span><span class="doc-stamp">بسته ثابت خ'
                "دمت · قرارداد۱ / قاعده۱<br>"
            ).replace("__BRAND_MARK__", mark)
        )
        + esc(snap["created_at"])
        + "</span></div><h1>"
        + esc(snap["title"])
        + (
            '</h1></header><main class="doc-body"><p class="n'
            'ote">دریافت بسته به معنی ارسال درخواست نیست. این'
            " گزارش خوداظهاری است و مجوز، تایید مالی یا پذیرش"
            " رسمی ایجاد نمی\u200cکند.</p>"
        )
        + body
        + (
            '</main><footer class="doc-foot">سرمایه\u200cگزین · ای'
            "ن بسته از داده ذخیره\u200cشده همان نسخه تهیه شده؛ تعه"
            "د پرداخت یا تضمین سود نیست.</footer></div></body"
            "></html>"
        )
    )


def permitted_report(user, report):
    if report.snapshot.get("subject_type") != "service":
        return report.user_id == user.pk
    try:
        ws.target(user, "draft", report.snapshot["draft_id"], trash=True)
        return True
    except Fault:
        return False


def report_package(report):
    """An authorized, bounded package of this frozen report and its clean private references."""
    import hashlib
    import io
    import zipfile

    snapshot = report.snapshot
    ids = snapshot["files"]
    rows = {
        str(f.pk): f
        for f in PrivateFile.objects.filter(
            pk__in=ids, draft_id=snapshot["draft_id"], status="clean", purged_at__isnull=True
        )
    }
    if set(rows) != set(ids):
        raise Fault(
            ("پیوست ثبت\u200cشده اکنون پاک و قابل دریافت نیست؛ وضعیت بررسی را پیگیری کنید."),
            409,
            "files",
        )
    output = io.BytesIO()
    manifest = {
        "format": "invest-private-service-package",
        "version": 1,
        "report": str(report.pk),
        "snapshot": snapshot,
        "files": [],
    }
    extensions = {
        "application/pdf": "pdf",
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("report.html", report_html(report))
        for index, fid in enumerate(ids):
            f = rows[fid]
            data = bytes(f.derivative if f.derivative is not None else f.content or b"")
            if not data or f.media_type not in extensions:
                raise Fault("محتوای بررسی‌شده پیوست آماده دریافت نیست.", 409, "files")
            name = "attachments/" + str(index + 1) + "-" + fid + "." + extensions[f.media_type]
            archive.writestr(name, data)
            manifest["files"].append(
                {
                    "id": fid,
                    "original_name": f.name,
                    "path": name,
                    "media_type": f.media_type,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return output.getvalue()
