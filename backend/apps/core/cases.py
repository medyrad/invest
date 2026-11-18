from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.identity.models import User
from apps.workspace import service as ws
from apps.workspace.models import PrivateFile
from apps.workspace.schema import Fault, check_keys

from .common import event, identifier, notify, owner, role, run, text
from .models import Case, Consent, Message
from .publication import active, get_op

TERMINAL = ["closed", "cancelled", "terminated"]


def due(at):
    # Development calendar v1: Saturday–Wednesday, 09–17 Tehran; no real service promise.
    zone = ZoneInfo("Asia/Tehran")
    local = at.astimezone(zone)
    remaining = timedelta(hours=8)
    for _ in range(15):
        if local.weekday() not in [3, 4]:
            start = datetime.combine(local.date(), time(9), zone)
            end = datetime.combine(local.date(), time(17), zone)
            local = max(local, start)
            span = max(end - local, timedelta())
            if span >= remaining:
                return local + remaining
            remaining -= span
        local = datetime.combine(local.date() + timedelta(days=1), time(9), zone)
    raise Fault("تقویم پاسخ تنظیم نشده است.", 503)


def get_case(session, id, lock=False):
    qs = Case.objects.select_for_update(of=("self",)) if lock else Case.objects
    try:
        c = qs.select_related("customer", "expert", "opportunity__draft", "submission").get(
            pk=identifier(id)
        )
    except Case.DoesNotExist as e:
        raise Fault("پرونده پیدا نشد.", 404) from e
    if session.user.pk not in [c.customer_id, c.expert_id]:
        role(session, "admin")
    elif session.user.pk == c.expert_id:
        role(session, "expert")
    return c


def dto(c):
    consents = c.consent_set.filter(revoked_at__isnull=True)
    return {
        "id": str(c.pk),
        "customer_id": str(c.customer_id),
        "opportunity_id": str(c.opportunity_id),
        "title": c.submission.snapshot.get("title"),
        "status": c.status,
        "version": c.version,
        "expert": {
            "id": str(c.expert_id),
            "name": c.expert.core_personal.profile.get("name", "کارشناس")
            if hasattr(c.expert, "core_personal")
            else "کارشناس " + str(c.expert_id)[:6],
        }
        if c.expert_id
        else None,
        "owner": {
            "id": str(owner(c.opportunity).pk),
            "name": "صاحب فرصت " + str(owner(c.opportunity).pk)[:6],
        }
        if owner(c.opportunity)
        else None,
        "next_action": c.next_action,
        "next_followup_at": c.next_followup_at.isoformat() if c.next_followup_at else None,
        "opportunity_availability": c.opportunity.availability,
        "history": [
            {"action": e.action, "data": e.data, "at": e.created_at.isoformat()}
            for e in c_events(c.pk)
        ],
        "first_response_due": c.first_response_due.isoformat(),
        "calendar": "تقویم مصنوعی توسعه نسخه۱؛ وعده عرضه نیست",
        "previous": str(c.previous_id) if c.previous_id else None,
        "consents": [
            {"id": s.pk, "recipient": str(s.recipient_id), "kind": s.kind} for s in consents
        ],
        "messages": [
            {
                "id": m.pk,
                "actor": str(m.actor_id),
                "text": m.text,
                "files": m.files,
                "final": m.final,
                "at": m.created_at.isoformat(),
            }
            for m in c.message_set.order_by("id")
        ],
    }


def create(session, data):
    check_keys(data, ["key", "opportunity", "text", "previous"])
    user = session.user
    oid = identifier(data["opportunity"])

    def auth():
        if not user.is_active:
            raise Fault("حساب فعال نیست.", 403)

    def work():
        if settings.INVEST_ENV == "public":
            raise Fault("پذیرش عمومی تا تعیین تیم، جانشین، تقویم و گیت عرضه فعال نیست.", 503)
        op = get_op(oid, True)
        if not active(op):
            raise Fault("فرصت اکنون درخواست تازه نمی‌پذیرد.", 409)
        prev = None
        if data["previous"]:
            prev = get_case(session, data["previous"], True)
            if (
                prev.customer_id != user.pk
                or prev.opportunity_id != op.pk
                or prev.status not in TERMINAL
            ):
                raise Fault("پرونده مرتبط معتبر نیست.")
        existing = (
            Case.objects.filter(customer=user, opportunity=op).exclude(status__in=TERMINAL).first()
        )
        if existing:
            return {
                "case": dto(existing),
                "existing": True,
                "message": (
                    "پرونده فعال مشابه وجود دارد؛ درخواست تازه ثبت و متن جدید به گفتگو اضافه نشد."
                ),
            }
        at = timezone.now()
        c = Case.objects.create(
            customer=user,
            opportunity=op,
            submission=op.public_revision,
            previous=prev,
            first_response_due=due(at),
        )
        Message.objects.create(case=c, actor=user, text=text(data["text"], "text"))
        event(user, c.pk, "case_submitted", opportunity=str(op.pk))
        notify(user, "درخواست شما با رسید ثبت شد.", "/requests/" + str(c.pk))
        for admin in User.objects.filter(role="admin", is_active=True):
            notify(admin, "درخواست تازه برای ارجاع آماده است.", "/admin")
        return {"case": dto(c), "existing": False}

    return run(user, data, "case_create", oid, auth, work)


def action(session, id, data):
    check_keys(
        data,
        [
            "key",
            "version",
            "action",
            "text",
            "next_action",
            "expert",
            "recipient",
            "kind",
            "files",
            "next_followup_at",
        ],
    )
    user = session.user

    def auth():
        get_case(session, id, True)

    def work():
        c = get_case(session, id, True)
        if type(data["version"]) is not int or data["version"] != c.version:
            raise Fault("نسخه پرونده تغییر کرده؛ تازه‌سازی کنید.", 409)
        act = data["action"]
        at = timezone.now()
        if act == "assign":
            role(session, "admin")
            if c.status in TERMINAL:
                raise Fault("پرونده بسته قابل ارجاع نیست.", 409)
            try:
                expert = User.objects.get(
                    pk=identifier(data["expert"]), role="expert", is_active=True
                )
            except User.DoesNotExist as e:
                raise Fault("کارشناس فعال انتخاب کنید.") from e
            if expert.pk == c.customer_id:
                raise Fault("کارشناس با مشتری پرونده یکسان نیست.")
            if c.expert_id != expert.pk:
                c.consent_set.filter(kind="expert", revoked_at__isnull=True).update(revoked_at=at)
                c.expert = expert
            if c.status == "submitted":
                c.status = "assigned"
            text(data["text"], "text")
            notify(expert, "پرونده به شما ارجاع شد.", "/requests/" + str(c.pk))
        elif act in ["message", "answer", "awaiting_user", "start_review"]:
            if c.status in TERMINAL:
                raise Fault("پرونده بسته است؛ پیگیری مرتبط تازه بسازید.", 409)
            customer = user.pk == c.customer_id
            if not customer:
                role(session, "expert")
                if user.pk != c.expert_id:
                    raise Fault("فقط کارشناس جاری پاسخ می‌دهد.", 403)
            if customer and act != "message":
                raise Fault("اقدام فقط برای کارشناس است.", 403)
            body = text(data["text"], "text")
            if (
                not isinstance(data["files"], list)
                or len(data["files"]) > 10
                or len(set(data["files"])) != len(data["files"])
            ):
                raise Fault("فهرست پیوست معتبر نیست.")
            for fid in data["files"]:
                try:
                    f = PrivateFile.objects.get(
                        pk=identifier(fid),
                        uploader=user,
                        status="clean",
                        attached=True,
                        deleted_at__isnull=True,
                        replaced_at__isnull=True,
                        purged_at__isnull=True,
                    )
                except PrivateFile.DoesNotExist as e:
                    raise Fault("پیوست پاک و مجاز خود را انتخاب کنید.", 403) from e
                if f.draft_id:
                    ws.target(user, "draft", f.draft_id)
                else:
                    ws.target(user, "request", f.application_id)
            if act in ["answer", "awaiting_user"]:
                try:
                    followup = datetime.fromisoformat(data["next_followup_at"])
                    if timezone.is_naive(followup) or followup <= at:
                        raise ValueError()
                except (ValueError, TypeError) as exc:
                    raise Fault(
                        "موعد معتبر آینده برای پیگیری بعد لازم است.", field="next_followup_at"
                    ) from exc
                c.next_followup_at = followup
                c.followup_notified = False
            final = act == "answer"
            if final:
                c.next_action = text(data["next_action"], "next_action")
                c.answered_at = at
                c.status = "answered"
            elif act == "awaiting_user":
                c.next_action = text(data["next_action"], "next_action")
                c.status = "awaiting_user"
                c.answered_at = None
            else:
                c.status = "in_review" if c.expert_id else "submitted"
                c.answered_at = None
            Message.objects.create(case=c, actor=user, text=body, files=data["files"], final=final)
            if not customer and not c.first_response_at:
                c.first_response_at = at
            recipient = c.expert if customer else c.customer
            if recipient:
                notify(recipient, "پیام تازه در پرونده دارید.", "/requests/" + str(c.pk))
        elif act in ["grant", "revoke"]:
            if user.pk != c.customer_id:
                raise Fault("فقط مشتری رضایت را مدیریت می‌کند.", 403)
            recipient = identifier(data["recipient"])
            kind = data["kind"]
            expected = (
                c.expert_id
                if kind == "expert"
                else owner(c.opportunity).pk
                if kind == "owner" and owner(c.opportunity)
                else None
            )
            if kind not in ["owner", "expert"] or not expected or recipient != expected:
                raise Fault("گیرنده جاری و نام‌دار لازم است.")
            if act == "grant":
                if c.status in TERMINAL:
                    raise Fault("پرونده بسته رضایت تازه نمی‌پذیرد.")
                if not Consent.objects.filter(
                    case=c, recipient_id=recipient, kind=kind, revoked_at__isnull=True
                ).exists():
                    Consent.objects.create(case=c, recipient_id=recipient, kind=kind)
            else:
                Consent.objects.filter(
                    case=c, recipient_id=recipient, kind=kind, revoked_at__isnull=True
                ).update(revoked_at=at)
        elif act == "confirm":
            if user.pk != c.customer_id or c.status != "answered":
                raise Fault("تأیید فقط پس از پاسخ نهایی توسط مشتری است.", 403)
            c.status = "closed"
        elif act == "cancel":
            if user.pk != c.customer_id or c.status in TERMINAL:
                raise Fault("لغو مجاز نیست.", 403)
            c.status = "cancelled"
        elif act == "terminate":
            role(session, "admin")
            text(data["text"], "text")
            if c.status in TERMINAL:
                raise Fault("پرونده بسته است.", 409)
            if data["next_action"] not in ["duplicate", "abuse", "withdrawn"]:
                raise Fault("علت متمایز خاتمه را انتخاب کنید.", field="next_action")
            c.status = "terminated"
        else:
            raise Fault("اقدام معتبر نیست.")
        c.version += 1
        c.save()
        event(
            user,
            c.pk,
            "case_" + act,
            reason=data["text"] if act in ["assign", "terminate"] else "",
            termination_kind=data["next_action"] if act == "terminate" else None,
            recipient=data["recipient"] if act in ["grant", "revoke"] else None,
        )
        return dto(c)

    return run(user, data, "case_action", identifier(id), auth, work)


def contact(session, id):
    # Owner is not a participant. A separate endpoint checks ONLY named consent and authority.
    try:
        c = Case.objects.select_related("opportunity__draft").get(pk=identifier(id))
    except Case.DoesNotExist as e:
        raise Fault("پرونده پیدا نشد.", 404) from e
    user = session.user
    allowed = (c.expert_id == user.pk and user.role == "expert") or owner(c.opportunity) == user
    if c.expert_id == user.pk:
        role(session, "expert")
    if not allowed or not c.consent_set.filter(recipient=user, revoked_at__isnull=True).exists():
        raise Fault("رضایت معتبر برای شما وجود ندارد.", 403)
    event(user, c.pk, "contact_read")
    return {"mobile": c.customer.mobile}


def jobs(at=None):
    at = at or timezone.now()
    count = 0
    for id in Case.objects.exclude(status__in=TERMINAL).values_list("id", flat=True):
        with transaction.atomic():
            c = Case.objects.select_for_update().get(pk=id)
            if c.status == "answered" and c.answered_at and at >= c.answered_at + timedelta(days=7):
                c.status = "closed"
                c.version += 1
                c.save()
                event(None, c.pk, "case_closed_after_answer")
                notify(
                    c.customer, "پرونده هفت روز پس از پاسخ نهایی بسته شد.", "/requests/" + str(c.pk)
                )
                count += 1
            if (
                c.status not in TERMINAL
                and c.next_followup_at
                and at >= c.next_followup_at
                and not c.followup_notified
            ):
                c.followup_notified = True
                c.save()
                recipients = list(User.objects.filter(role="admin", is_active=True))
                if c.expert_id:
                    recipients.append(c.expert)
                for user in recipients:
                    notify(user, "موعد پیگیری داخلی پرونده رسیده است.", "/requests/" + str(c.pk))
            if (
                c.status not in TERMINAL
                and not c.first_response_at
                and at >= c.first_response_due
                and not c.overdue_notified
            ):
                c.overdue_notified = True
                c.save()
                for admin in User.objects.filter(role="admin", is_active=True):
                    notify(
                        admin,
                        "مهلت داخلی پاسخ گذشته؛ پیگیری و جانشین را بررسی کنید.",
                        "/requests/" + str(c.pk),
                    )
    return count


def c_events(id):
    from .models import Event

    return Event.objects.filter(target=id).order_by("id")
