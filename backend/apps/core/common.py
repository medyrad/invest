import hashlib
import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.identity.models import User
from apps.workspace import service as workspace
from apps.workspace.schema import Fault

from .models import Event, Notification, Receipt


def role(session, name):
    if not session or session.user.role != name:
        raise Fault("دسترسی به این نقش مجاز نیست.", 403)
    if name in ["admin", "expert"]:
        local = (
            settings.INVEST_ENV in ["development", "test"]
            and session.assurance == "test"
            and session.sensitive
        )
        real = (
            session.assurance == "real"
            and session.sensitive
            and session.reauthenticated_at
            and timezone.now() < session.reauthenticated_at + timedelta(minutes=5)
        )
        if not (local or real):
            raise Fault("احراز مجدد نقش حساس لازم است.", 403)


def text(value, field, limit=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or "\0" in value:
        raise Fault("متن معتبر و غیرخالی وارد کنید.", field=field)
    return value.strip()


def identifier(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as e:
        raise Fault("شناسه معتبر نیست.") from e


def event(user, target, action, **data):
    Event.objects.create(actor=user, target=target, action=action, data=data)


def notify(user, text, path):
    Notification.objects.create(user=user, text=text, path=path)


def owner(op):
    if op is None:
        return None
    if not op.draft.organization_id:
        return op.draft.creator
    from apps.workspace.models import Representation

    g = Representation.objects.filter(organization=op.draft.organization, status="active").first()
    return g.user if g and workspace.grant(g.user, op.draft.organization_id) else None


def owned(user, op):
    if owner(op) != user:
        raise Fault("اختیار جاری مالک برقرار نیست.", 403)


def run(user, data, action, target, authorize, work):
    identifier(data.get("key"))
    fingerprint = hashlib.sha256(
        json.dumps([action, str(target), data], sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()
    with transaction.atomic():
        User.objects.select_for_update().get(pk=user.pk)
        authorize()
        old = Receipt.objects.filter(user=user, key=data["key"]).first()
        if old:
            if old.fingerprint != fingerprint:
                raise Fault("کلید برای ورودی دیگری استفاده شده است.", 409, field="key")
            return old.data
        result = work()
        Receipt.objects.create(
            user=user, key=data["key"], fingerprint=fingerprint, target=target, data=result
        )
        return result
