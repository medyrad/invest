import secrets
from datetime import timedelta

from django.conf import settings

from . import otp
from .locking import identity_transaction
from .models import AuthSession, User


def current_session(token, at):
    if not isinstance(token, str) or len(token) > 100:
        return None
    session = AuthSession.objects.select_related("user").filter(digest=otp.digest(token)).first()
    if (
        not session
        or session.revoked
        or not session.user.is_active
        or session.epoch != session.user.auth_epoch
    ):
        return None
    if session.assurance == "test" and settings.INVEST_ENV == "public":
        return None
    idle = timedelta(minutes=30) if session.sensitive else timedelta(hours=24)
    absolute = timedelta(hours=12) if session.sensitive else timedelta(days=7)
    if at >= session.last_activity + idle or at >= session.created_at + absolute:
        return None
    return session


def mint_session(user, at, sensitive=False, assurance="test"):
    token = secrets.token_urlsafe(32)
    session = AuthSession.objects.create(
        digest=otp.digest(token),
        user=user,
        epoch=user.auth_epoch,
        created_at=at,
        last_activity=at,
        sensitive=sensitive,
        assurance=assurance,
        reauthenticated_at=at,
    )
    return session, token


def me(token):
    with identity_transaction():
        session = current_session(token, otp.now())
        if not session:
            return {"authenticated": False}
        return {
            "authenticated": True,
            "user": {
                "id": str(session.user_id),
                "mobile": session.user.mobile,
                "role": session.user.role,
            },
            "assurance": session.assurance,
        }


def operate(token, action, owner=None):
    with identity_transaction():
        at = otp.now()
        session = current_session(token, at)
        if action == "logout":
            if session:
                session.revoked = True
                session.save(update_fields=["revoked"])
                otp.audit("logged_out", session.user)
            return {"logged_out": True}, None
        if not session:
            raise otp.Fault("forbidden", 403)
        if action == "activity":
            session.last_activity = at
            session.save(update_fields=["last_activity"])
        elif action == "revoke-all":
            session.user.auth_epoch += 1
            session.user.save(update_fields=["auth_epoch"])
            otp.audit("sessions_revoked", session.user)
        elif action == "rotate":
            fresh = secrets.token_urlsafe(32)
            session.digest = otp.digest(fresh)
            session.save(update_fields=["digest"])
            otp.audit("session_rotated", session.user)
            return {"rotated": True}, fresh
        elif action == "private":
            if str(session.user_id) != str(owner):
                raise otp.Fault("forbidden", 403)
            return {"owner_id": str(session.user_id), "synthetic": True}, None
        elif action == "sensitive":
            if (
                session.user.role not in ("expert", "admin")
                or not session.sensitive
                or session.assurance != "real"
                or not session.reauthenticated_at
                or at >= session.reauthenticated_at + timedelta(minutes=5)
            ):
                raise otp.Fault("forbidden", 403)
            otp.audit("synthetic_sensitive_action", session.user)
        else:
            raise otp.Fault("invalid_request")
        return {"ok": True}, None


def change_authority(user_id, *, active=None, role=None):
    """Internal administrative service; never accepts a role from an auth API payload."""
    with identity_transaction():
        user = User.objects.get(pk=user_id)
        if role is not None:
            if role not in ("user", "owner", "expert", "admin"):
                raise otp.Fault("invalid_request")
            user.role = role
        if active is not None:
            user.is_active = active
        user.save()
        otp.audit("authority_changed", user)
