from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.services.service import permitted_report
from apps.workspace.schema import Fault, check_keys

from .common import identifier, run, text
from .discovery import criteria, public_dto
from .models import LoginOperation, Notification, Personal, Report, Saved, Search
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
    from .reporting import render

    return render(snapshot)


def mutate(user, data, session=None):
    check_keys(
        data,
        ["key", "action", "id", "value"]
        + (["base"] if isinstance(data, dict) and "base" in data else []),
    )
    action = data["action"]
    target = identifier(data["key"])

    def authorize():
        bound = LoginOperation.objects.select_related("session__user").filter(key=target).first()
        if not bound:
            return
        linked = bound.session
        if (
            not session
            or linked.pk != session.pk
            or linked.user_id != user.pk
            or linked.revoked
            or not linked.user.is_active
            or linked.epoch != linked.user.auth_epoch
            or timezone.now()
            >= linked.last_activity
            + (timedelta(minutes=30) if linked.sensitive else timedelta(hours=24))
            or timezone.now()
            >= linked.created_at + (timedelta(hours=12) if linked.sensitive else timedelta(days=7))
        ):
            raise Fault("ادامه ذخیره متعلق به نشست دیگری است؛ دوباره اقدام کنید.", 403)
        op = bound.operation
        if op.get("cancelled") or timezone.now() >= bound.created_at + timedelta(minutes=10):
            raise Fault("ادامه ذخیره لغو یا منقضی شده است؛ دوباره اقدام کنید.", 409)
        expected = (
            ("save", op.get("id"), True)
            if op.get("type") == "save-listing"
            else ("search", None, {"name": op.get("name"), "criteria": op.get("criteria")})
        )
        if (action, data.get("id"), data.get("value")) != expected:
            raise Fault("اطلاعات ادامه ذخیره تغییر کرده است.", 409)

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
            base = data.get("base")

            def same(k):
                before, current = base.get(k), p.profile.get(k)
                if k == "professional" and before is not None and current is not None:
                    try:
                        return json.loads(before) == json.loads(current)
                    except TypeError, ValueError:
                        return False
                return before == current

            if base is not None and (not isinstance(base, dict) or any(not same(k) for k in v)):
                raise Fault(
                    "پروفایل در جای دیگری تغییر کرده؛ ورودی شما حفظ شد. نسخه تازه را بررسی کنید.",
                    409,
                )
            p.profile = {**p.profile, **v}
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
                    saved_search = (
                        Search.objects.select_for_update()
                        .filter(user=user, pk=identifier(data["id"]))
                        .first()
                    )
                    if not saved_search:
                        raise Fault("جست‌وجو پیدا نشد.", 404)
                    if "base" in data and data["base"] != {
                        "name": saved_search.name,
                        "criteria": saved_search.criteria,
                    }:
                        raise Fault("شرایط در جای دیگری تغییر کرده؛ ورودی شما حفظ شد.", 409)
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
            snapshot = report_snapshot(op, data["value"], target)
            report_id = target
            r = Report.objects.create(id=report_id, user=user, snapshot=snapshot)
            return {
                "report_id": str(r.pk),
                "download": "/api/v1/core/reports/" + str(r.pk),
            }
        else:
            raise Fault("اقدام معتبر نیست.")
        return state(user)

    from apps.identity.locking import identity_transaction

    with identity_transaction():
        return run(user, data, "personal", target, authorize, work)


def report_snapshot(op, value, report_id):
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
                not isinstance(k, str) or not isinstance(v, str) or len(k) > 200 or len(v) > 4000
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
            type(context["advisory_version"]) is not int or context["advisory_version"] != 1
        ):
            raise Fault("نسخه پاسخ‌های مؤثر معتبر نیست.")
        c = criteria(value["criteria"])
    else:
        c = criteria(value)
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

        advisory_key = Subtype.objects.filter(pk=subtype).values_list("raw_id", flat=True).first()
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
    from .reporting import STEPS, metadata

    snapshot["template_version"] = 2
    snapshot["title"] = snapshot["opportunity"]["fields"].get("title", "گزارش فرصت")
    snapshot["field_labels"] = metadata(snapshot["opportunity"])
    from apps.catalog import models as catalog

    for field, model in [
        ("province", catalog.Province),
        ("county", catalog.County),
        ("city", catalog.City),
        ("group", catalog.Group),
        ("subtype", catalog.Subtype),
    ]:
        value = snapshot["opportunity"]["fields"].get(field)
        if value is not None and field in snapshot["field_labels"]:
            name = model.objects.filter(pk=value).values_list("name", flat=True).first()
            if name:
                snapshot["field_labels"][field]["options"] = {str(value): name}
    snapshot["action_steps"] = STEPS.get(
        next(iter(snapshot["opportunity"].get("routes", [])), ""), []
    )
    snapshot["rendered_html"] = _report_html(snapshot)
    return snapshot
