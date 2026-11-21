import hashlib
import hmac
import uuid
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core import signing
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.identity.sessions import current_session

from .models import GuestMerge, QuotaPolicy, UsageLedger, UsageReservation
from .routing import ROUTER_VERSION

PROMPT_VERSION = "assistant-fa-v2"
TOOL_VERSION = "assistant-tools-v2"
SCHEMA_VERSION = "assistant-response-v2"
PRICE_VERSION = "openai-standard-2026-11-20"
COOKIE = "invest_ai_guest"


class QuotaError(Exception):
    def __init__(self, code, message, status=429, retry_after=None):
        self.code = code
        self.message = message
        self.status = status
        self.retry_after = retry_after


@dataclass(frozen=True)
class Principal:
    digest: str
    kind: str
    guest_value: str | None
    user: object | None


def _digest(value):
    return hmac.new(settings.SECRET_KEY.encode(), str(value).encode(), hashlib.sha256).hexdigest()


def principal(request, at=None):
    at = at or timezone.now()
    session = current_session(request.COOKIES.get("invest_session"), at)
    raw = request.COOKIES.get(COOKIE)
    guest = None
    if raw:
        try:
            guest = signing.loads(raw, salt="assistant-guest", max_age=400 * 86400)
        except signing.BadSignature:
            guest = None
    if not isinstance(guest, str):
        guest = str(uuid.uuid4())
    if session:
        return Principal(_digest("account:" + str(session.user_id)), "account", guest, session.user)
    return Principal(_digest("guest:" + guest), "guest", guest, None)


def internal_evaluation_principal(identity):
    """Create the server-only principal used by the locked evaluation harness."""
    if not isinstance(identity, str) or not identity.startswith("s09:"):
        raise ValueError("invalid_internal_evaluation_identity")
    return Principal(_digest("internal-evaluation:" + identity), "eval", None, None)


def signed_guest(value):
    return signing.dumps(value, salt="assistant-guest", compress=True)


def _policy_locked():
    policy = (
        QuotaPolicy.objects.select_for_update().filter(active=True).order_by("-version").first()
    )
    if not policy:
        created = QuotaPolicy.objects.create(version=1)
        policy = QuotaPolicy.objects.select_for_update().get(pk=created.pk)
    return policy


def _merged_guest_hashes(user, month):
    return list(
        GuestMerge.objects.filter(user=user, month_utc=month).values_list("guest_hash", flat=True)
    )


def merge_guest_if_needed(p, at):
    if not p.user or not p.guest_value:
        return None
    guest_hash = _digest("guest:" + p.guest_value)
    month = at.date().replace(day=1)
    existing = (
        GuestMerge.objects.select_for_update()
        .filter(guest_hash=guest_hash, month_utc=month)
        .first()
    )
    if existing:
        return guest_hash if existing.user_id == p.user.pk else None
    GuestMerge.objects.create(user=p.user, guest_hash=guest_hash, month_utc=month)
    return guest_hash


def _spent_rows(rows):
    completed = rows.filter(status="completed").aggregate(total=Sum("actual_usd"))[
        "total"
    ] or Decimal(0)
    held = rows.filter(status__in=["reserved", "held"]).aggregate(total=Sum("reserved_usd"))[
        "total"
    ] or Decimal(0)
    return completed + held


def _spent(month):
    rows = UsageReservation.objects.filter(month_utc=month).exclude(
        status__in=["failed", "cancelled"]
    )
    return _spent_rows(rows)


def reserve(
    p,
    key,
    payload_hash,
    model,
    purpose="product",
    at=None,
    *,
    route_code="legacy",
    route_reason="legacy_policy",
    router_version=ROUTER_VERSION,
):
    at = at or timezone.now()
    if not isinstance(key, str) or not 8 <= len(key) <= 200 or "\0" in key:
        raise QuotaError("invalid_idempotency_key", "کلید تکرار معتبر نیست.", 400)
    key_hash = _digest("idempotency:" + key)
    month = at.date().replace(day=1)
    with transaction.atomic():
        policy = _policy_locked()
        merged_guest = merge_guest_if_needed(p, at)
        old = UsageReservation.objects.filter(
            principal_hash=p.digest, idempotency_hash=key_hash
        ).first()
        if not old and merged_guest:
            old = UsageReservation.objects.filter(
                principal_hash=merged_guest, idempotency_hash=key_hash
            ).first()
        if old:
            if old.payload_hash != payload_hash:
                raise QuotaError(
                    "idempotency_conflict", "این کلید برای درخواست دیگری استفاده شده است.", 409
                )
            return old, policy, True
        if p.kind != "eval":
            active = UsageReservation.objects.filter(principal_hash=p.digest, status="reserved").count()
            if active >= policy.concurrent_turns:
                raise QuotaError("concurrency_exhausted", "دو نوبت هنوز در حال پردازش است.")
            hour = (
                UsageReservation.objects.filter(
                    principal_hash=p.digest, created_at__gte=at - timedelta(hours=1)
                ).aggregate(total=Sum("provider_calls"))["total"]
                or 0
            )
            hourly = policy.account_hourly_starts if p.kind == "account" else policy.guest_hourly_starts
            if hour >= hourly:
                raise QuotaError("rate_limited", "شروع‌های این ساعت به سقف رسیده است.", retry_after=3600)
        hashes = [p.digest]
        if p.user:
            hashes.extend(_merged_guest_hashes(p.user, month))
        if p.kind != "eval":
            completed = UsageReservation.objects.filter(
                principal_hash__in=hashes, day_utc=at.date(), status="completed"
            ).count()
            reserved = UsageReservation.objects.filter(
                principal_hash__in=hashes, day_utc=at.date(), status__in=["reserved", "held"]
            ).count()
            daily = policy.account_daily if p.kind == "account" else policy.guest_daily
            if completed + reserved >= daily:
                tomorrow = at.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                raise QuotaError(
                    "quota_exhausted",
                    "سهمیه پاسخ کامل امروز به پایان رسیده است.",
                    retry_after=max(1, int((tomorrow - at).total_seconds())),
                )
        total = _spent(month)
        if total + policy.turn_reserve_usd > policy.monthly_usd:
            raise QuotaError("budget_exhausted", "بودجه ماهانه سرویس به پایان رسیده است.")
        if p.kind != "eval":
            principal_rows = UsageReservation.objects.filter(
                principal_hash__in=hashes, month_utc=month
            ).exclude(status__in=["failed", "cancelled"])
            principal_total = _spent_rows(principal_rows)
            if principal_total + policy.turn_reserve_usd > policy.principal_monthly_usd:
                raise QuotaError(
                    "principal_budget_exhausted",
                    "سقف هزینه ماهانه این حساب یا مهمان به پایان رسیده است.",
                )
        if purpose in {"smoke", "eval"}:
            purpose_cap = policy.smoke_usd if purpose == "smoke" else policy.eval_usd
            purpose_rows = UsageReservation.objects.filter(
                month_utc=month, purpose=purpose
            ).exclude(status__in=["failed", "cancelled"])
            purpose_used = _spent_rows(purpose_rows)
            if purpose_used + policy.turn_reserve_usd > purpose_cap:
                raise QuotaError("purpose_budget_exhausted", "بودجه این اجرای ارزیابی کافی نیست.")
        item = UsageReservation.objects.create(
            principal_hash=p.digest,
            principal_kind=p.kind,
            day_utc=at.date(),
            month_utc=month,
            idempotency_hash=key_hash,
            payload_hash=payload_hash,
            policy_version=policy.version,
            model=model,
            route_code=route_code,
            route_reason=route_reason,
            router_version=router_version,
            purpose=purpose,
            reserved_usd=policy.turn_reserve_usd,
        )
        return item, policy, False


def claim_provider_call(item):
    with transaction.atomic():
        policy = _policy_locked()
        row = UsageReservation.objects.select_for_update().get(pk=item.pk)
        if row.status != "reserved":
            raise QuotaError("reservation_inactive", "رزرو این نوبت فعال نیست.", 409)
        if row.principal_kind == "eval":
            row.provider_calls += 1
            row.save(update_fields=["provider_calls"])
            return row.provider_calls
        used = (
            UsageReservation.objects.filter(
                principal_hash=row.principal_hash,
                created_at__gte=timezone.now() - timedelta(hours=1),
            ).aggregate(total=Sum("provider_calls"))["total"]
            or 0
        )
        limit = (
            policy.account_hourly_starts
            if row.principal_kind == "account"
            else policy.guest_hourly_starts
        )
        if used >= limit:
            raise QuotaError("rate_limited", "شروع‌های provider در این ساعت به سقف رسیده است.")
        row.provider_calls += 1
        row.save(update_fields=["provider_calls"])
        return row.provider_calls


def settle(item, *, status, usage=None, model_returned="", request_id="", failure_code=""):
    usage = usage or {}
    with transaction.atomic():
        row = UsageReservation.objects.select_for_update().get(pk=item.pk)
        if row.status != "reserved":
            return row
        row.status = status
        row.input_tokens = int(usage.get("input_tokens", 0))
        row.output_tokens = int(usage.get("output_tokens", 0))
        row.provider_calls = int(usage.get("calls", 0))
        actual = usage.get("cost_usd")
        row.actual_usd = Decimal(str(actual)) if actual is not None else None
        row.provider_request_hash = _digest(request_id) if request_id else ""
        row.failure_code = failure_code
        row.finished_at = timezone.now()
        row.save()
        UsageLedger.objects.get_or_create(
            reservation=row,
            defaults={
                "model_requested": row.model,
                "model_returned": model_returned,
                "route_code": row.route_code,
                "route_reason": row.route_reason,
                "router_version": row.router_version,
                "prompt_version": PROMPT_VERSION,
                "tool_version": TOOL_VERSION,
                "schema_version": SCHEMA_VERSION,
                "policy_version": row.policy_version,
                "price_version": PRICE_VERSION,
                "retention_until": timezone.now().date() + timedelta(days=365),
            },
        )
        return row


def usage_view(p, at=None):
    at = at or timezone.now()
    policy = QuotaPolicy.objects.filter(active=True).order_by("-version").first()
    if not policy:
        policy = QuotaPolicy(version=1)
    month = at.date().replace(day=1)
    if p.user and p.guest_value:
        with transaction.atomic():
            merge_guest_if_needed(p, at)
    hashes = [p.digest]
    if p.user:
        hashes.extend(_merged_guest_hashes(p.user, month))
    used = UsageReservation.objects.filter(
        principal_hash__in=hashes, day_utc=at.date(), status="completed"
    ).count()
    limit = policy.account_daily if p.kind == "account" else policy.guest_daily
    reset = at.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    monthly_rows = UsageReservation.objects.filter(
        principal_hash__in=hashes, month_utc=month
    ).exclude(status__in=["failed", "cancelled"])
    spent = monthly_rows.filter(status="completed").aggregate(total=Sum("actual_usd"))["total"] or Decimal(0)
    held = monthly_rows.filter(status__in=["reserved", "held"]).aggregate(total=Sum("reserved_usd"))["total"] or Decimal(0)
    cap = Decimal(str(policy.principal_monthly_usd))
    return {
        "principal": p.kind,
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
        "reset_at": reset.isoformat(),
        "policy_version": policy.version,
        "monthly": {
            "spent_usd": str(spent),
            "held_usd": str(held),
            "cap_usd": str(cap),
            "remaining_usd": str(max(Decimal(0), cap - spent - held)),
            "reset_at": (month + timedelta(days=32)).replace(day=1).isoformat(),
        },
    }
