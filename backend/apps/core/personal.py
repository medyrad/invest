import html
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.services.service import permitted_report
from apps.workspace.schema import Fault, check_keys

from .common import identifier, run, text
from .discovery import criteria, public_dto
from .models import Notification, Personal, Report, Saved, Search
from .publication import get_op


def state(user):
    p, _ = Personal.objects.get_or_create(user=user)
    return {
        "profile": {k: v for k, v in p.profile.items() if k != "local_role"},
        "saved": [
            public_dto(s.opportunity)
            for s in Saved.objects.filter(user=user).select_related(
                "opportunity__public_revision", "opportunity__draft"
            )
            if s.opportunity.public_revision_id
        ],
        "searches": [
            {
                "id": str(s.pk),
                "name": s.name,
                "criteria": s.criteria,
                "policy_version": s.policy_version,
                "last_seen": s.last_seen.isoformat(),
            }
            for s in Search.objects.filter(user=user)
        ],
        "notifications": [
            {**n, "created_at": n["created_at"].isoformat()}
            for n in Notification.objects.filter(user=user)
            .order_by("-id")
            .values("id", "text", "path", "read", "created_at")[:100]
        ],
        "reports": [
            {
                "id": str(r.pk),
                "created_at": r.created_at.isoformat(),
                "subject_type": r.snapshot.get("subject_type", "opportunity"),
                "title": r.snapshot.get("title", "گزارش فرصت"),
                "download": "/api/v1/services/reports/"
                + str(r.pk)
                + ("/package" if r.snapshot.get("files") else "/download")
                if r.snapshot.get("subject_type") == "service"
                else "/api/v1/core/reports/" + str(r.pk),
            }
            for r in Report.objects.filter(
                Q(user=user) | Q(snapshot__subject_type="service")
            ).order_by("-created_at")
            if permitted_report(user, r)
        ],
    }


def _report_html(snapshot):
    """Render the immutable opportunity snapshot as a readable, inert Persian report."""

    opportunity = snapshot["opportunity"]
    context = snapshot.get("guide_context", {})
    effective = snapshot.get("effective_advisory", {})
    def esc(value):
        return html.escape(str(value), quote=True)

    advisory_version = effective.get("version", context.get("advisory_version", 1))

    def rows(items):
        return "".join(
            f"<div><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>"
            for label, value in items
            if value not in (None, "", [], {})
        )

    mine = context.get("mine", [])
    answers = context.get("answers", {})
    checked = context.get("checked", [])
    guidance = effective.get("guidance", {}) if isinstance(effective, dict) else {}
    checks = guidance.get("checks", []) if isinstance(guidance, dict) else []
    overview = [
        ("عنوان", opportunity.get("title")),
        ("نوع", opportunity.get("kind")),
        ("استان", opportunity.get("province")),
        ("شهر", opportunity.get("city")),
        ("نسخه فرصت", opportunity.get("revision")),
    ]
    sections = [
        "<section><h2>فرصت در یک نگاه</h2><dl>" + rows(overview) + "</dl></section>"
    ]
    if mine:
        sections.append(
            "<section><h2>شرایط ثبت‌شده شما</h2><dl>"
            + rows(mine)
            + "</dl></section>"
        )
    if answers:
        sections.append(
            "<section><h2>پاسخ‌های مؤثر ثبت‌شده</h2><dl>"
            + rows(answers.items())
            + f"</dl><p>نسخه قواعد: {esc(advisory_version)}</p></section>"
        )
    if guidance.get("why") or checks:
        sections.append(
            "<section><h2>کنترل‌های راهنمای مؤثر</h2>"
            + f"<p>نسخه قواعد: {esc(advisory_version)}</p>"
            + (f"<p>{esc(guidance['why'])}</p>" if guidance.get("why") else "")
            + (
                "<ul>"
                + "".join(f"<li>{esc(item)}</li>" for item in checks)
                + "</ul>"
                if checks
                else ""
            )
            + "</section>"
        )
    if checked:
        sections.append(
            "<section><h2>موارد بررسی‌شده</h2><ul>"
            + "".join(f"<li>{esc(item)}</li>" for item in checked)
            + "</ul></section>"
        )
    sections.append(
        "<section><h2>رسید و مبنای ثابت گزارش</h2>"
        f"<p>شناسه گزارش: {esc(snapshot['report_id'])}</p>"
        f"<p>زمان ثبت: {esc(snapshot['created_at'])}</p>"
        f"<p>{esc(snapshot['warning'])}</p>"
        "<p>این دریافت پرونده یا درخواست تازه‌ای ایجاد نمی‌کند.</p></section>"
    )
    head = (
        '<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>راهنمای اقدام سرمایه‌گزین</title><style>"
        "body{max-width:900px;margin:32px auto;padding:20px;color:#17343b;"
        "background:#f5f6f2;font:14px/2 Tahoma,Arial,sans-serif}"
        "header,section{background:#fff;border:1px solid #dce3df;border-radius:16px;"
        "padding:22px;margin:14px 0}h1,h2{margin:0 0 14px}h1{font-size:24px}"
        "h2{font-size:18px;color:#0e6266}dl>div{display:grid;"
        "grid-template-columns:minmax(9rem,1fr) 2fr;gap:14px;"
        "border-bottom:1px solid #edf0ee;padding:8px 0}dt{color:#657774}"
        "dd{margin:0;font-weight:700;overflow-wrap:anywhere}@media(max-width:600px){"
        "body{margin:0;padding:12px}dl>div{grid-template-columns:1fr;gap:2px}}"
        "</style></head><body>"
    )
    return head + (
        f"<header><h1>{esc(opportunity.get('title', 'راهنمای اقدام'))}</h1>"
        "<p>گزارش فارسی نسخه‌دار از snapshot تاریخی؛ اختیار دریافت با حساب جاری "
        "بررسی می‌شود.</p></header>"
        + "".join(sections)
        + "</body></html>"
    )


def mutate(user, data):
    check_keys(data, ["key", "action", "id", "value"])
    action = data["action"]
    target = identifier(data["key"])

    def work():
        if action == "save":
            op = get_op(data["id"])
            if not op.public_revision_id:
                raise Fault("فرصت عمومی نیست.", 404)
            if type(data["value"]) is not bool:
                raise Fault("انتخاب معتبر نیست.")
            if data["value"]:
                Saved.objects.get_or_create(user=user, opportunity=op)
            else:
                Saved.objects.filter(user=user, opportunity=op).delete()
        elif action == "profile":
            v = data["value"]
            if (
                not isinstance(v, dict)
                or set(v)
                - {"name", "profession", "experience", "interests", "description", "professional"}
                or any(not isinstance(x, str) or len(x) > 2000 or "\0" in x for x in v.values())
            ):
                raise Fault("پروفایل معتبر نیست؛ نقش از پروفایل تغییر نمی‌کند.")
            if "professional" in v:
                import json

                try:
                    professional = json.loads(v["professional"])
                except (ValueError, TypeError) as exc:
                    raise Fault("اطلاعات حرفه‌ای معتبر نیست.") from exc
                keys = {
                    "name",
                    "entity",
                    "roles",
                    "province",
                    "specialty",
                    "capacity",
                    "capital",
                    "certificate",
                    "certificateNo",
                    "issuer",
                    "expiry",
                    "validity",
                    "references",
                }
                if not isinstance(professional, dict) or set(professional) - keys:
                    raise Fault("فیلد حرفه‌ای ناشناخته است.")
                if professional.get("entity") not in [None, "", "company", "individual"]:
                    raise Fault("نوع فعالیت معتبر نیست.", field="professional.entity")
                if professional.get("validity") not in [
                    None,
                    "",
                    "unknown",
                    "reported",
                    "expired",
                    "none",
                ]:
                    raise Fault("وضعیت اعتبار معتبر نیست.", field="professional.validity")
                if professional.get("province") not in [None, "", "all"]:
                    from apps.catalog.models import Province

                    if not Province.objects.filter(name=professional["province"]).exists():
                        raise Fault("استان فعالیت معتبر نیست.", field="professional.province")
                if professional.get("capital") not in [None, ""]:
                    try:
                        capital = Decimal(str(professional["capital"]))
                    except (InvalidOperation, ValueError) as exc:
                        raise Fault(
                            "سرمایه قابل تخصیص معتبر نیست.", field="professional.capital"
                        ) from exc
                    if (
                        not capital.is_finite()
                        or capital < 0
                        or capital > Decimal("999999999999999")
                    ):
                        raise Fault("سرمایه قابل تخصیص معتبر نیست.", field="professional.capital")
                if professional.get("certificateNo") and not professional.get("issuer"):
                    raise Fault(
                        "برای گواهینامه دارای شماره، مرجع صادرکننده را نیز مشخص کنید.",
                        field="professional.issuer",
                    )
                for k, item in professional.items():
                    if k == "roles":
                        if not isinstance(item, list) or any(
                            x not in ["investor", "builder", "contractor", "manager", "consultant"]
                            for x in item
                        ):
                            raise Fault("نقش حرفه‌ای معتبر نیست.")
                    elif (
                        not isinstance(item, (str, int, float))
                        or isinstance(item, bool)
                        or len(str(item)) > 2000
                    ):
                        raise Fault("مقدار حرفه‌ای معتبر نیست.")
            p, _ = Personal.objects.get_or_create(user=user)
            p.profile = {
                **({"local_role": p.profile["local_role"]} if "local_role" in p.profile else {}),
                **v,
            }
            p.save()
        elif action in ["search", "search_update"]:
            v = data["value"]
            check_keys(v, ["name", "criteria"])
            criteria(v["criteria"])
            name = text(v["name"], "name", 100)
            if action == "search":
                if Search.objects.filter(user=user).count() >= 100:
                    raise Fault("سقف فنی جست‌وجوی ذخیره‌شده پر است.", 429)
                Search.objects.create(user=user, name=name, criteria=v["criteria"])
            else:
                with transaction.atomic():
                    saved_search = Search.objects.select_for_update().filter(
                        user=user, pk=identifier(data["id"])
                    ).first()
                    if not saved_search:
                        raise Fault("جست‌وجو پیدا نشد.", 404)
                    saved_search.name = name
                    saved_search.criteria = v["criteria"]
                    saved_search.save(update_fields=["name", "criteria"])
        elif action in ["search_delete", "search_seen"]:
            q = Search.objects.filter(user=user, pk=identifier(data["id"]))
            if not q.exists():
                raise Fault("جست‌وجو پیدا نشد.", 404)
            if action == "search_delete":
                q.delete()
            else:
                q.update(last_seen=timezone.now())
        elif action == "notification_read":
            if type(data["id"]) is not int or data["id"] <= 0:
                raise Fault("شناسه اعلان معتبر نیست.", field="id")
            Notification.objects.filter(user=user, pk=data["id"]).update(read=True)
        elif action == "report":
            op = get_op(data["id"])
            if not op.public_revision_id:
                raise Fault("فرصت عمومی نیست.", 404)
            value = data["value"]
            context = {}
            if isinstance(value, dict) and "criteria" in value:
                check_keys(value, ["criteria", "guide_context"])
                context = value["guide_context"]
                import json

                if (
                    not isinstance(context, dict)
                    or set(context) - {"mine", "answers", "kind", "checked", "advisory_version"}
                    or len(json.dumps(context, ensure_ascii=True)) > 50000
                ):
                    raise Fault("اطلاعات تکمیلی گزارش معتبر نیست.")
                mine = context.get("mine", [])
                answers = context.get("answers", {})
                checked = context.get("checked", [])
                if (
                    not isinstance(mine, list)
                    or len(mine) > 100
                    or any(
                        not isinstance(pair, list)
                        or len(pair) != 2
                        or any(not isinstance(x, str) or len(x) > 4000 for x in pair)
                        for pair in mine
                    )
                ):
                    raise Fault("شرایط گزارش معتبر نیست.")
                if (
                    not isinstance(answers, dict)
                    or len(answers) > 100
                    or any(
                        not isinstance(k, str)
                        or not isinstance(v, str)
                        or len(k) > 200
                        or len(v) > 4000
                        for k, v in answers.items()
                    )
                ):
                    raise Fault("پاسخ‌های گزارش معتبر نیست.")
                if (
                    not isinstance(checked, list)
                    or len(checked) > 300
                    or any(not isinstance(x, str) or len(x) > 200 for x in checked)
                ):
                    raise Fault("چک‌لیست گزارش معتبر نیست.")
                if "kind" in context and (
                    not isinstance(context["kind"], str) or len(context["kind"]) > 100
                ):
                    raise Fault("نوع پیگیری گزارش معتبر نیست.")
                if "advisory_version" in context and (
                    type(context["advisory_version"]) is not int
                    or context["advisory_version"] != 1
                ):
                    raise Fault("نسخه پاسخ‌های مؤثر معتبر نیست.")
                c = criteria(value["criteria"])
            else:
                c = criteria(value)
            report_id = identifier(data["key"])
            snapshot = {
                    "template_version": 1,
                    "policy_version": 1,
                    "report_id": str(report_id),
                    "opportunity": public_dto(op),
                    "assumptions": c,
                    "guide_context": context,
                    "warning": (
                        "داده و ادعاهای صاحب فرصت؛ تضمین سود یا توصیه قطعی نیست. "
                        "مبلغ و واحد و مبنا مطابق همین snapshot است."
                    ),
                    "created_at": timezone.now().isoformat(),
                }
            subtype = snapshot["opportunity"].get("fields", {}).get("subtype")
            if subtype:
                from apps.catalog.models import Subtype
                from apps.services import advisories

                advisory_key = Subtype.objects.filter(pk=subtype).values_list(
                    "raw_id", flat=True
                ).first()
                if advisory_key:
                    try:
                        snapshot["effective_advisory"] = advisories.evaluate(
                            advisory_key,
                            answers=context.get("answers", {}),
                            funding="own",
                            role="investor",
                        )
                    except Fault:
                        raise Fault("راهنمای مؤثر این فرصت قابل بازیابی نیست.", 409) from None
            snapshot["rendered_html"] = _report_html(snapshot)
            r = Report.objects.create(id=report_id, user=user, snapshot=snapshot)
            return {
                "report_id": str(r.pk),
                "download": "/api/v1/core/reports/" + str(r.pk),
            }
        else:
            raise Fault("اقدام معتبر نیست.")
        return state(user)

    return run(user, data, "personal", target, lambda: None, work)
