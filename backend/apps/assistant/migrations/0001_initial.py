# Generated for PROGRAMMER-COMP-AI-COMPLETE-01.
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("identity", "0004_loginflow_intent_session"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="QuotaPolicy",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("version", models.PositiveIntegerField(unique=True)),
                ("active", models.BooleanField(default=True)),
                ("guest_daily", models.PositiveIntegerField(default=3)),
                ("account_daily", models.PositiveIntegerField(default=20)),
                ("concurrent_turns", models.PositiveIntegerField(default=2)),
                ("guest_hourly_starts", models.PositiveIntegerField(default=10)),
                ("account_hourly_starts", models.PositiveIntegerField(default=60)),
                (
                    "monthly_usd",
                    models.DecimalField(decimal_places=4, default="100.0000", max_digits=8),
                ),
                (
                    "turn_reserve_usd",
                    models.DecimalField(decimal_places=4, default="0.1000", max_digits=6),
                ),
                (
                    "smoke_usd",
                    models.DecimalField(decimal_places=4, default="5.0000", max_digits=6),
                ),
                (
                    "eval_usd",
                    models.DecimalField(decimal_places=4, default="15.0000", max_digits=6),
                ),
                ("max_input_tokens", models.PositiveIntegerField(default=8000)),
                ("max_output_tokens", models.PositiveIntegerField(default=1000)),
                ("max_provider_calls", models.PositiveIntegerField(default=4)),
                ("deadline_seconds", models.PositiveIntegerField(default=45)),
                ("safe_retries", models.PositiveIntegerField(default=1)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name="UsageReservation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("principal_hash", models.CharField(db_index=True, max_length=64)),
                ("principal_kind", models.CharField(max_length=8)),
                ("day_utc", models.DateField(db_index=True)),
                ("month_utc", models.DateField(db_index=True)),
                ("idempotency_hash", models.CharField(max_length=64)),
                ("payload_hash", models.CharField(max_length=64)),
                ("policy_version", models.PositiveIntegerField()),
                ("model", models.CharField(max_length=80)),
                ("purpose", models.CharField(default="product", max_length=12)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("reserved", "reserved"),
                            ("completed", "completed"),
                            ("failed", "failed"),
                            ("held", "held"),
                            ("cancelled", "cancelled"),
                        ],
                        default="reserved",
                        max_length=12,
                    ),
                ),
                ("reserved_usd", models.DecimalField(decimal_places=4, max_digits=7)),
                ("actual_usd", models.DecimalField(decimal_places=6, max_digits=9, null=True)),
                ("input_tokens", models.PositiveIntegerField(default=0)),
                ("output_tokens", models.PositiveIntegerField(default=0)),
                ("provider_calls", models.PositiveIntegerField(default=0)),
                ("provider_request_hash", models.CharField(blank=True, max_length=64)),
                ("failure_code", models.CharField(blank=True, max_length=40)),
                (
                    "created_at",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                ("finished_at", models.DateTimeField(null=True)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("principal_hash", "idempotency_hash"), name="assistant_idempotency"
                    )
                ]
            },
        ),
        migrations.CreateModel(
            name="UsageLedger",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("model_requested", models.CharField(max_length=80)),
                ("model_returned", models.CharField(blank=True, max_length=80)),
                ("prompt_version", models.CharField(max_length=40)),
                ("tool_version", models.CharField(max_length=40)),
                ("schema_version", models.CharField(max_length=40)),
                ("policy_version", models.PositiveIntegerField()),
                ("price_version", models.CharField(max_length=40)),
                ("retention_until", models.DateField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "reservation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ledger",
                        to="assistant.usagereservation",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GuestMerge",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("guest_hash", models.CharField(max_length=64)),
                ("day_utc", models.DateField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("user", "guest_hash", "day_utc"), name="assistant_guest_merge_once"
                    ),
                    models.UniqueConstraint(
                        fields=("guest_hash", "day_utc"), name="assistant_guest_one_account"
                    ),
                ]
            },
        ),
    ]
