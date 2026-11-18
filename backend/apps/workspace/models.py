import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=100)
    registration = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["country", "registration"], name="workspace_org_registration"
            )
        ]


class RepresentationRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    details = models.JSONField()
    status = models.CharField(
        max_length=16,
        default="pending",
        choices=[(x, x) for x in ["pending", "needs_info", "rejected", "approved"]],
    )
    version = models.PositiveIntegerField(default=1)


class Representation(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=16, choices=[(x, x) for x in ["active", "revoked", "hold"]]
    )
    ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization"],
                condition=Q(status="active"),
                name="workspace_one_active_representative",
            )
        ]


class Draft(models.Model):
    kind = models.CharField(
        max_length=32,
        default="project",
        choices=[
            (x, x)
            for x in [
                "project",
                "fund",
                "sale",
                "proposal",
                "ideas",
                "land-preparation",
                "foreign-investment",
                "ma-notice",
                "ma-renewal",
                "ma-manager",
                "ma-exchange",
                "charity",
            ]
        ],
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, null=True)
    application = models.ForeignKey(RepresentationRequest, on_delete=models.PROTECT, null=True)
    schema_version = models.PositiveIntegerField(default=1)
    version = models.PositiveIntegerField(default=1)
    routes = models.JSONField(default=list)
    heritage_enabled = models.BooleanField(default=False)
    raw = models.JSONField(default=dict)
    deleted_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class DraftRevision(models.Model):
    draft = models.ForeignKey(Draft, on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    raw = models.JSONField()
    effective = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["draft", "version"], name="workspace_draft_revision")
        ]


class DraftValue(models.Model):
    revision = models.ForeignKey(DraftRevision, on_delete=models.PROTECT)
    key = models.CharField(max_length=80)
    money = models.ForeignKey("catalog.MoneyValue", null=True, on_delete=models.PROTECT)
    quantity = models.ForeignKey("catalog.Quantity", null=True, on_delete=models.PROTECT)
    return_metric = models.ForeignKey("catalog.ReturnMetric", null=True, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["revision", "key"], name="workspace_value_key"),
            models.CheckConstraint(
                condition=(
                    Q(money__isnull=False, quantity__isnull=True, return_metric__isnull=True)
                    | Q(money__isnull=True, quantity__isnull=False, return_metric__isnull=True)
                    | Q(money__isnull=True, quantity__isnull=True, return_metric__isnull=False)
                ),
                name="workspace_one_value_kind",
            ),
        ]


class Operation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    receipt = models.JSONField()
    target_type = models.CharField(max_length=16)
    target_id = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "key"], name="workspace_operation_key")
        ]


class PrivateFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    draft = models.ForeignKey(Draft, null=True, on_delete=models.PROTECT)
    application = models.ForeignKey(RepresentationRequest, null=True, on_delete=models.PROTECT)
    kind = models.CharField(max_length=16, choices=[("image", "image"), ("document", "document")])
    name = models.CharField(max_length=200)
    size = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    content = models.BinaryField(null=True)
    derivative = models.BinaryField(null=True)
    media_type = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, default="pending_check")
    reason = models.CharField(max_length=300, blank=True)
    received_at = models.DateTimeField(null=True)
    checked_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True)
    replaced_at = models.DateTimeField(null=True)
    purged_at = models.DateTimeField(null=True)
    attached = models.BooleanField(default=False)
    replaces = models.ForeignKey(
        "self", null=True, on_delete=models.PROTECT, related_name="replacements"
    )
    next_check = models.DateTimeField(default=timezone.now)
    attempts = models.PositiveIntegerField(default=0)
    incident_reason = models.CharField(max_length=500, blank=True)
    incident_owner = models.CharField(max_length=200, blank=True)
    incident_review_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(draft__isnull=False, application__isnull=True)
                | Q(draft__isnull=True, application__isnull=False),
                name="workspace_file_one_target",
            )
        ]


class ReceiveAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
