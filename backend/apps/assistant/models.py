import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class QuotaPolicy(models.Model):
    version = models.PositiveIntegerField(unique=True)
    active = models.BooleanField(default=True)
    guest_daily = models.PositiveIntegerField(default=3)
    account_daily = models.PositiveIntegerField(default=20)
    concurrent_turns = models.PositiveIntegerField(default=2)
    guest_hourly_starts = models.PositiveIntegerField(default=10)
    account_hourly_starts = models.PositiveIntegerField(default=60)
    monthly_usd = models.DecimalField(max_digits=8, decimal_places=4, default="100.0000")
    turn_reserve_usd = models.DecimalField(max_digits=6, decimal_places=4, default="0.1000")
    smoke_usd = models.DecimalField(max_digits=6, decimal_places=4, default="5.0000")
    eval_usd = models.DecimalField(max_digits=6, decimal_places=4, default="15.0000")
    max_input_tokens = models.PositiveIntegerField(default=8000)
    max_output_tokens = models.PositiveIntegerField(default=1000)
    max_provider_calls = models.PositiveIntegerField(default=4)
    deadline_seconds = models.PositiveIntegerField(default=45)
    safe_retries = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)


class UsageReservation(models.Model):
    STATUS = [
        ("reserved", "reserved"),
        ("completed", "completed"),
        ("failed", "failed"),
        ("held", "held"),
        ("cancelled", "cancelled"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    principal_hash = models.CharField(max_length=64, db_index=True)
    principal_kind = models.CharField(max_length=8)
    day_utc = models.DateField(db_index=True)
    month_utc = models.DateField(db_index=True)
    idempotency_hash = models.CharField(max_length=64)
    payload_hash = models.CharField(max_length=64)
    policy_version = models.PositiveIntegerField()
    model = models.CharField(max_length=80)
    purpose = models.CharField(max_length=12, default="product")
    status = models.CharField(max_length=12, choices=STATUS, default="reserved")
    reserved_usd = models.DecimalField(max_digits=7, decimal_places=4)
    actual_usd = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    provider_calls = models.PositiveIntegerField(default=0)
    provider_request_hash = models.CharField(max_length=64, blank=True)
    failure_code = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    finished_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["principal_hash", "idempotency_hash"], name="assistant_idempotency"
            )
        ]


class UsageLedger(models.Model):
    reservation = models.OneToOneField(
        UsageReservation, on_delete=models.PROTECT, related_name="ledger"
    )
    model_requested = models.CharField(max_length=80)
    model_returned = models.CharField(max_length=80, blank=True)
    prompt_version = models.CharField(max_length=40)
    tool_version = models.CharField(max_length=40)
    schema_version = models.CharField(max_length=40)
    policy_version = models.PositiveIntegerField()
    price_version = models.CharField(max_length=40)
    retention_until = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)


class GuestMerge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    guest_hash = models.CharField(max_length=64)
    day_utc = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "guest_hash", "day_utc"], name="assistant_guest_merge_once"
            ),
            models.UniqueConstraint(
                fields=["guest_hash", "day_utc"], name="assistant_guest_one_account"
            ),
        ]
