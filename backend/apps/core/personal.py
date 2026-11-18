from django.utils import timezone

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
            {"id": str(r.pk), "created_at": r.created_at.isoformat()}
            for r in Report.objects.filter(user=user).order_by("-created_at")[:50]
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
