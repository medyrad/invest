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
        elif action == "search":
            v = data["value"]
            check_keys(v, ["name", "criteria"])
            criteria(v["criteria"])
            if Search.objects.filter(user=user).count() >= 100:
                raise Fault("سقف فنی جست‌وجوی ذخیره‌شده پر است.", 429)
            Search.objects.create(
                user=user, name=text(v["name"], "name", 100), criteria=v["criteria"]
            )
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
                    or set(context) - {"mine", "answers", "kind", "checked"}
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
                c = criteria(value["criteria"])
            else:
                c = criteria(value)
            r = Report.objects.create(
                user=user,
                snapshot={
                    "template_version": 1,
                    "policy_version": 1,
                    "opportunity": public_dto(op),
                    "assumptions": c,
                    "guide_context": context,
                    "warning": (
                        "داده و ادعاهای صاحب فرصت؛ تضمین سود یا توصیه قطعی نیست. "
                        "مبلغ و واحد و مبنا مطابق همین snapshot است."
                    ),
                    "created_at": timezone.now().isoformat(),
                },
            )
            return {"report_id": str(r.pk)}
        else:
            raise Fault("اقدام معتبر نیست.")
        return state(user)

    return run(user, data, "personal", target, lambda: None, work)
