import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models

MOBILE_PATTERN = r"\A\+[1-9][0-9]{7,14}\Z"
validate_mobile = RegexValidator(MOBILE_PATTERN, "شماره باید در قالب بین‌المللی باشد.")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, mobile, password=None, **extra_fields):
        validate_mobile(mobile)
        user = self.model(mobile=mobile, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superuser requires staff and superuser flags")
        return self.create_user(mobile, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mobile = models.CharField(max_length=16, unique=True, validators=[validate_mobile])
    mobile_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.CharField(
        max_length=16,
        default="user",
        choices=[(r, r) for r in ("user", "owner", "expert", "admin")],
    )
    auth_epoch = models.PositiveIntegerField(default=0)
    objects = UserManager()

    def save(self, *args, **kwargs):
        from .locking import identity_transaction

        with identity_transaction():
            previous = (
                type(self).objects.filter(pk=self.pk).first() if not self._state.adding else None
            )
            if previous:
                changed = any(
                    getattr(previous, field) != getattr(self, field)
                    for field in ("is_active", "role", "is_staff", "is_superuser")
                )
                self.auth_epoch = max(previous.auth_epoch, self.auth_epoch) + int(changed)
                if changed and kwargs.get("update_fields"):
                    kwargs["update_fields"] = set(kwargs["update_fields"]) | {"auth_epoch"}
            super().save(*args, **kwargs)

    USERNAME_FIELD = "mobile"

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(mobile__regex=MOBILE_PATTERN),
                name="identity_user_mobile_canonical",
            )
        ]

    def __str__(self):
        return str(self.pk)


class LoginFlow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    digest = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    epoch = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    intent = models.JSONField(null=True)
    intent_at = models.DateTimeField(null=True)
    intent_account = models.UUIDField(null=True)
    intent_session = models.ForeignKey(
        "AuthSession", null=True, on_delete=models.SET_NULL, related_name="intents"
    )
    intent_consumed = models.BooleanField(default=False)


class OTPChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flow = models.ForeignKey(LoginFlow, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    epoch = models.PositiveIntegerField()
    operation_key = models.UUIDField()
    nonce = models.CharField(max_length=64)
    code_digest = models.CharField(max_length=64)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    state = models.CharField(max_length=16, default="active")
    delivery = models.CharField(max_length=16, default="pending")
    session = models.ForeignKey("AuthSession", null=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["flow", "operation_key"], name="identity_flow_operation_unique"
            )
        ]


class IssueEvent(models.Model):
    flow = models.ForeignKey(LoginFlow, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_digest = models.CharField(max_length=64)
    at = models.DateTimeField(db_index=True)


class CheckEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    at = models.DateTimeField(db_index=True)
    failed = models.BooleanField(default=False)


class AuthSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    digest = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    epoch = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    last_activity = models.DateTimeField()
    sensitive = models.BooleanField(default=False)
    assurance = models.CharField(max_length=16, default="test")
    reauthenticated_at = models.DateTimeField(null=True)
    revoked = models.BooleanField(default=False)


class AuditEvent(models.Model):
    kind = models.CharField(max_length=40)
    account_id = models.UUIDField(null=True)
    at = models.DateTimeField()
