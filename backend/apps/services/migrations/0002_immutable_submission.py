from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("services", "0001_initial"), ("core", "0002_immutable_history")]
    operations = [
        migrations.RunSQL(
            (
                "CREATE TRIGGER service_submission_immutable BEFO"
                "RE UPDATE OR DELETE ON services_servicesubmissio"
                "n FOR EACH ROW EXECUTE FUNCTION core_immutable_h"
                "istory();"
            ),
            "DROP TRIGGER service_submission_immutable ON services_servicesubmission;",
        )
    ]
