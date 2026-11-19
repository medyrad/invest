import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_case_service_draft_case_service_submission_and_more"),
        ("identity", "0004_loginflow_intent_session"),
    ]
    operations = [
        migrations.CreateModel(
            name="LoginOperation",
            fields=[
                ("key", models.UUIDField(primary_key=True, serialize=False)),
                ("operation", models.JSONField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="identity.authsession"
                    ),
                ),
            ],
        ),
    ]
