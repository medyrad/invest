from django.db import migrations, models


def copy_month(apps, schema_editor):
    GuestMerge = apps.get_model("assistant", "GuestMerge")
    for row in GuestMerge.objects.all().iterator():
        row.month_utc = row.day_utc.replace(day=1)
        row.save(update_fields=["month_utc"])


class Migration(migrations.Migration):
    dependencies = [("assistant", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="quotapolicy",
            name="principal_monthly_usd",
            field=models.DecimalField(decimal_places=4, default="10.0000", max_digits=6),
        ),
        migrations.AddField(model_name="usagereservation", name="route_code", field=models.CharField(default="legacy", max_length=40)),
        migrations.AddField(model_name="usagereservation", name="route_reason", field=models.CharField(default="legacy_policy", max_length=80)),
        migrations.AddField(model_name="usagereservation", name="router_version", field=models.CharField(default="assistant-router-v1", max_length=40)),
        migrations.AddField(model_name="usageledger", name="route_code", field=models.CharField(default="legacy", max_length=40)),
        migrations.AddField(model_name="usageledger", name="route_reason", field=models.CharField(default="legacy_policy", max_length=80)),
        migrations.AddField(model_name="usageledger", name="router_version", field=models.CharField(default="assistant-router-v1", max_length=40)),
        migrations.AddField(model_name="guestmerge", name="month_utc", field=models.DateField(null=True)),
        migrations.RunPython(copy_month, migrations.RunPython.noop),
        migrations.RemoveConstraint(model_name="guestmerge", name="assistant_guest_merge_once"),
        migrations.RemoveConstraint(model_name="guestmerge", name="assistant_guest_one_account"),
        migrations.RemoveField(model_name="guestmerge", name="day_utc"),
        migrations.AlterField(model_name="guestmerge", name="month_utc", field=models.DateField()),
        migrations.AddConstraint(model_name="guestmerge", constraint=models.UniqueConstraint(fields=("user", "guest_hash", "month_utc"), name="assistant_guest_merge_once")),
        migrations.AddConstraint(model_name="guestmerge", constraint=models.UniqueConstraint(fields=("guest_hash", "month_utc"), name="assistant_guest_one_account")),
    ]
