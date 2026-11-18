from django.db import migrations

SQL = """
CREATE FUNCTION core_immutable_history() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'core history is immutable'; END $$;
""" + "".join(
    (
        f"CREATE TRIGGER {t}_immutable BEFORE UPDATE OR DELETE ON core_{t} FOR "
        f"EACH ROW EXECUTE FUNCTION core_immutable_history();\n"
    )
    for t in ["submission", "review", "event", "message", "report"]
)
REVERSE = (
    "".join(
        f"DROP TRIGGER {t}_immutable ON core_{t};\n"
        for t in ["submission", "review", "event", "message", "report"]
    )
    + "DROP FUNCTION core_immutable_history();"
)


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
