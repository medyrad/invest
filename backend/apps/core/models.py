import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

U = settings.AUTH_USER_MODEL


class Opportunity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft = models.OneToOneField("workspace.Draft", on_delete=models.PROTECT)
    public_revision = models.ForeignKey(
        "Submission", null=True, on_delete=models.PROTECT, related_name="+"
    )
    availability = models.CharField(max_length=20, default="active")
    version = models.PositiveIntegerField(default=1)
    expires_at = models.DateTimeField(null=True)
    synthetic = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    availability__in=[
                        "active",
                        "owner_paused",
                        "admin_suspended",
                        "expired",
                        "archived",
                    ]
                ),
                name="core_availability",
            )
        ]


class Submission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.PROTECT)
    draft_version = models.PositiveIntegerField()
    kind = models.CharField(max_length=12)
    routes = models.JSONField()
    snapshot = models.JSONField()
    files = models.JSONField(default=list)
    submitted_by = models.ForeignKey(U, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["opportunity", "draft_version"], name="core_submission_version"
            )
        ]


class Review(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.PROTECT)
    actor = models.ForeignKey(U, on_delete=models.PROTECT)
    decision = models.CharField(max_length=24)
    reason = models.TextField()
    public_files = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)


class Event(models.Model):
    actor = models.ForeignKey(U, on_delete=models.PROTECT, null=True)
    target = models.UUIDField(db_index=True)
    action = models.CharField(max_length=40)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)


class Receipt(models.Model):
    user = models.ForeignKey(U, on_delete=models.PROTECT)
    key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    target = models.UUIDField()
    data = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "key"], name="core_receipt_key")]


class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(U, on_delete=models.PROTECT, related_name="customer_cases")
    opportunity = models.ForeignKey(Opportunity, null=True, on_delete=models.PROTECT)
    submission = models.ForeignKey(Submission, null=True, on_delete=models.PROTECT)
    service_submission = models.ForeignKey(
        "services.ServiceSubmission", null=True, on_delete=models.PROTECT
    )
    service_draft = models.ForeignKey("workspace.Draft", null=True, on_delete=models.PROTECT)
    expert = models.ForeignKey(U, null=True, on_delete=models.PROTECT, related_name="expert_cases")
    previous = models.ForeignKey("self", null=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default="submitted")
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    first_response_due = models.DateTimeField()
    first_response_at = models.DateTimeField(null=True)
    answered_at = models.DateTimeField(null=True)
    next_action = models.TextField(blank=True)
    next_followup_at = models.DateTimeField(null=True)
    followup_notified = models.BooleanField(default=False)
    calendar_version = models.PositiveIntegerField(default=1)
    overdue_notified = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        opportunity__isnull=False,
                        submission__isnull=False,
                        service_submission__isnull=True,
                        service_draft__isnull=True,
                    )
                    | Q(
                        opportunity__isnull=True,
                        submission__isnull=True,
                        service_submission__isnull=False,
                        service_draft__isnull=False,
                    )
                ),
                name="core_case_subject",
            ),
            models.UniqueConstraint(
                fields=["service_draft"],
                condition=Q(service_draft__isnull=False)
                & ~Q(status__in=["closed", "cancelled", "terminated"]),
                name="core_one_live_service_case",
            ),
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        "submitted",
                        "assigned",
                        "in_review",
                        "awaiting_user",
                        "answered",
                        "closed",
                        "cancelled",
                        "terminated",
                    ]
                ),
                name="core_case_status",
            ),
            models.UniqueConstraint(
                fields=["customer", "opportunity"],
                condition=~Q(status__in=["closed", "cancelled", "terminated"]),
                name="core_one_live_case",
            ),
        ]


class Message(models.Model):
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    actor = models.ForeignKey(U, on_delete=models.PROTECT)
    text = models.TextField()
    files = models.JSONField(default=list)
    final = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)


class Consent(models.Model):
    case = models.ForeignKey(Case, on_delete=models.PROTECT)
    recipient = models.ForeignKey(U, on_delete=models.PROTECT)
    kind = models.CharField(max_length=12)
    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True)


class Notification(models.Model):
    user = models.ForeignKey(U, on_delete=models.PROTECT)
    text = models.CharField(max_length=300)
    path = models.CharField(max_length=200)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)


class Personal(models.Model):
    user = models.OneToOneField(
        U, on_delete=models.PROTECT, primary_key=True, related_name="core_personal"
    )
    profile = models.JSONField(default=dict)


class LoginOperation(models.Model):
    """Permanent binding of a consumed save intent, including after flow cancellation."""

    key = models.UUIDField(primary_key=True)
    session = models.ForeignKey("identity.AuthSession", on_delete=models.PROTECT)
    operation = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)


class Saved(models.Model):
    user = models.ForeignKey(U, on_delete=models.PROTECT)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "opportunity"], name="core_saved_unique")
        ]


class Search(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(U, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    criteria = models.JSONField()
    policy_version = models.PositiveIntegerField(default=1)
    last_seen = models.DateTimeField(default=timezone.now)


class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(U, on_delete=models.PROTECT)
    snapshot = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)


class ReviewEvidence(models.Model):
    review = models.OneToOneField(Review, on_delete=models.PROTECT)
    source = models.TextField()
    result = models.TextField()
    files = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
