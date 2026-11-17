"""Server-owned trial OTP. No provider calls, raw codes or bearer tokens are persisted."""

import hashlib
import hmac
import math
import re
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .locking import identity_transaction
from .models import AuditEvent, CheckEvent, IssueEvent, LoginFlow, OTPChallenge, User

now = timezone.now
DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


class Fault(Exception):
    def __init__(self, code, status=400, retry_after=None):
        super().__init__(code)
        self.code, self.status, self.retry_after = code, status, retry_after


def digest(value):
    return hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


def canonical_mobile(value):
    if not isinstance(value, str) or len(value) > 64 or re.search(r"[^0-9۰-۹٠-٩+ \-]", value):
        raise Fault("invalid_mobile")
    value = value.translate(DIGITS).replace(" ", "").replace("-", "")
    if re.fullmatch(r"09[0-9]{9}", value):
        value = "+98" + value[1:]
    elif re.fullmatch(r"00989[0-9]{9}", value):
        value = "+" + value[2:]
    if not re.fullmatch(r"\+989[0-9]{9}", value):
        raise Fault("invalid_mobile")
    return value


def normalized_code(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9۰-۹٠-٩]{6}", value):
        raise Fault("invalid_code")
    return value.translate(DIGITS)


def audit(kind, user=None):
    AuditEvent.objects.create(kind=kind, account_id=user.pk if user else None, at=now())


def new_flow():
    token = secrets.token_urlsafe(32)
    with identity_transaction():
        at = now()
        flow = LoginFlow.objects.create(
            digest=digest(token), created_at=at, expires_at=at + timedelta(minutes=30)
        )
        return {"flow_token": token, "expires_at": flow.expires_at.isoformat()}


def get_flow(token, at):
    if not isinstance(token, str) or len(token) > 100:
        raise Fault("flow_expired", 410)
    flow = LoginFlow.objects.filter(digest=digest(token)).first()
    if not flow or at >= flow.expires_at:
        raise Fault("flow_expired", 410)
    return flow


def uuid_value(value):
    try:
        return uuid.UUID(str(value))
    except ValueError, TypeError, AttributeError:
        raise Fault("invalid_request") from None


def trial_enabled():
    return (
        settings.INVEST_ENV in ("development", "test")
        and settings.OTP_DELIVERY_MODE == "notification"
    )


def code_for(challenge):
    # Random 256-bit nonce + keyed pseudorandom generation; stable for scoped delivery retries.
    return f"{int(digest('otp:' + str(challenge.id) + ':' + challenge.nonce), 16) % 1000000:06d}"


def state_of(challenge, at):
    if not challenge.user.is_active or challenge.epoch != challenge.user.auth_epoch:
        return "revoked"
    if challenge.state != "active":
        return challenge.state
    if challenge.attempts >= 5:
        return "exhausted"
    if at >= challenge.expires_at:
        return "expired"
    return "active"


def receipt(challenge, at):
    state = state_of(challenge, at)
    result = {
        "challenge_id": str(challenge.id),
        "state": state,
        "expires_at": challenge.expires_at.isoformat(),
        "resend_at": (challenge.issued_at + timedelta(seconds=60)).isoformat(),
        "delivery": challenge.delivery,
    }
    if state == "active" and challenge.delivery == "test" and trial_enabled():
        result["notification"] = {"code": code_for(challenge), "mode": "test-notification"}
    return result


def window_wait(query, at, seconds, limit):
    times = list(
        query.filter(at__gt=at - timedelta(seconds=seconds))
        .order_by("at")
        .values_list("at", flat=True)
    )
    if len(times) < limit:
        return 0
    return max(0, (times[len(times) - limit] + timedelta(seconds=seconds) - at).total_seconds())


def delivery_adapter(challenge):
    if trial_enabled():
        return "test"
    # No configured SMS adapter: never claim a message was sent.
    return "failed"


def issue(token, mobile, key, ip):
    mobile, key = canonical_mobile(mobile), uuid_value(key)
    with identity_transaction():
        at = now()
        flow = get_flow(token, at)
        previous = (
            OTPChallenge.objects.select_related("user").filter(flow=flow, operation_key=key).first()
        )
        if previous:
            if previous.user.mobile != mobile:
                raise Fault("payload_conflict", 409)
            return receipt(previous, at)
        if flow.completed:
            raise Fault("flow_completed", 409)
        user, _ = User.objects.get_or_create(mobile=mobile, defaults={"password": "!"})
        if not user.is_active:
            raise Fault("forbidden", 403)
        flow_events = IssueEvent.objects.filter(flow=flow)
        last = flow_events.order_by("-at").first()
        waits = [
            max(0, (last.at + timedelta(seconds=60) - at).total_seconds()) if last else 0,
            window_wait(flow_events, at, 900, 3),
            window_wait(IssueEvent.objects.filter(user=user), at, 900, 10),
            window_wait(IssueEvent.objects.filter(user=user), at, 86400, 10),
            window_wait(IssueEvent.objects.filter(ip_digest=digest("ip:" + ip)), at, 900, 30),
        ]
        if max(waits):
            raise Fault("rate_limited", 429, math.ceil(max(waits)))
        OTPChallenge.objects.filter(flow=flow, state="active").update(state="replaced")
        if flow.user_id and flow.user_id != user.pk:
            flow.intent = None
            flow.intent_account = None
        flow.user, flow.epoch = user, user.auth_epoch
        flow.save()
        challenge = OTPChallenge(
            id=uuid.uuid4(),
            flow=flow,
            user=user,
            epoch=user.auth_epoch,
            operation_key=key,
            nonce=secrets.token_hex(32),
            issued_at=at,
            expires_at=at + timedelta(seconds=120),
        )
        challenge.code_digest = digest(f"check:{challenge.id}:{code_for(challenge)}")
        challenge.save()
        IssueEvent.objects.create(flow=flow, user=user, ip_digest=digest("ip:" + ip), at=at)
        try:
            challenge.delivery = delivery_adapter(challenge)
        except TimeoutError:
            challenge.delivery = "unknown"
        except Exception:
            challenge.delivery = "failed"
        challenge.save(update_fields=["delivery"])
        audit("otp_issued", user)
        return receipt(challenge, at)


def edit(token):
    with identity_transaction():
        flow = get_flow(token, now())
        OTPChallenge.objects.filter(flow=flow, state="active").update(state="cancelled")
        return {"cancelled": True}


def verify(token, challenge_id, code, current=None, reauth=False):
    from .sessions import current_session, mint_session

    if not trial_enabled():
        raise Fault("delivery_unavailable", 503)
    failure = None
    result = None
    with identity_transaction():
        at = now()
        flow = get_flow(token, at)
        challenge = (
            OTPChallenge.objects.select_related("user")
            .filter(pk=uuid_value(challenge_id), flow=flow)
            .first()
        )
        if not challenge:
            raise Fault("invalid_code")
        state = state_of(challenge, at)
        if state == "consumed":
            session = current_session(current, at)
            if session and challenge.session_id == session.pk:
                return {"authenticated": True, "recovered": True}, None
            raise Fault("recovery_required", 409)
        if state != "active":
            raise Fault("challenge_" + state, 410)
        failures = CheckEvent.objects.filter(
            user=challenge.user, failed=True, at__gt=at - timedelta(minutes=15)
        )
        last_check = CheckEvent.objects.filter(user=challenge.user).order_by("-at").first()
        if failures.count() >= 10 and last_check:
            cooldown = (last_check.at + timedelta(seconds=30) - at).total_seconds()
            # The limit disappears as soon as the failure window drops below ten.
            exit_window = window_wait(failures, at, 900, 10)
            if cooldown > 0:
                raise Fault("rate_limited", 429, math.ceil(min(cooldown, exit_window)))
        try:
            normalized = normalized_code(code)
        except Fault:
            normalized = ""
        valid = hmac.compare_digest(
            challenge.code_digest, digest(f"check:{challenge.id}:{normalized}")
        )
        CheckEvent.objects.create(user=challenge.user, at=at, failed=not valid)
        if not valid:
            challenge.attempts += 1
            challenge.save(update_fields=["attempts"])
            audit("otp_rejected", challenge.user)
            failure = Fault("invalid_code")
        else:
            if reauth:
                session = current_session(current, at)
                if not session or session.user_id != challenge.user_id:
                    raise Fault("forbidden", 403)
                session.reauthenticated_at = at
                session.assurance = "test"
                session.save(update_fields=["reauthenticated_at", "assurance"])
                secret = None
            else:
                old = current_session(current, at)
                if old:
                    old.revoked = True
                    old.save(update_fields=["revoked"])
                    if old.user_id != challenge.user_id:
                        flow.intent = None
                session, secret = mint_session(challenge.user, at)
            challenge.state, challenge.session = "consumed", session
            challenge.save(update_fields=["state", "session"])
            flow.completed = True
            if flow.intent_account and flow.intent_account != challenge.user_id:
                flow.intent = None
            flow.intent_account = challenge.user_id
            flow.intent_session = session
            flow.save()
            audit("reauthenticated" if reauth else "logged_in", challenge.user)
            result = ({"authenticated": True}, secret)
    # Persist rejected attempts; never raise inside the transaction that records them.
    if failure:
        raise failure
    return result


def intent(token, action, payload=None, session_token=None):
    from .sessions import current_session

    with identity_transaction():
        at = now()
        flow = get_flow(token, at)
        session = current_session(session_token, at)
        if action == "cancel":
            flow.intent = None
            flow.save()
            return {"cancelled": True}
        if action == "set":
            if payload.get("destination") != "/saved" or not isinstance(
                payload.get("snapshot"), dict
            ):
                raise Fault("invalid_request")
            import json

            if len(json.dumps(payload["snapshot"])) > 4096:
                raise Fault("invalid_request")
            flow.intent = {"destination": "/saved", "snapshot": payload["snapshot"]}
            flow.intent_at, flow.intent_consumed = at, False
            flow.intent_account = session.user_id if session else None
            flow.intent_session = session
            flow.save()
            return {"expires_at": (at + timedelta(minutes=10)).isoformat()}
        if (
            not session
            or not flow.intent
            or flow.intent_consumed
            or at >= flow.intent_at + timedelta(minutes=10)
            or flow.intent_account != session.user_id
            or flow.intent_session_id != session.pk
            or flow.intent["destination"] != "/saved"
        ):
            raise Fault("intent_unavailable", 409)
        flow.intent_consumed = True
        flow.save(update_fields=["intent_consumed"])
        return {"handoff": flow.intent, "persisted": False}
