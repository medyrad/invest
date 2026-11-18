import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ServiceSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    draft = models.ForeignKey("workspace.Draft", on_delete=models.PROTECT)
    draft_version = models.PositiveIntegerField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(max_length=32)
    snapshot = models.JSONField()
    evaluation = models.JSONField()
    files = models.JSONField(default=list)
    schema_version = models.PositiveIntegerField(default=1)
    rule_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["draft", "draft_version"], name="services_submission_revision"
            )
        ]
