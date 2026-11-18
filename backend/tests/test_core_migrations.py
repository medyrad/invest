import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_old_draft_and_blob_preserved_across_forward_migration():
    executor = MigrationExecutor(connection)
    before = [("core", None), ("workspace", "0002_receiveattempt")]
    after = [
        ("core", "0004_reviewevidence"),
        ("workspace", "0003_draft_kind"),
    ]
    executor.migrate(before)
    try:
        old = executor.loader.project_state(
            [("workspace", "0002_receiveattempt"), ("identity", "0004_loginflow_intent_session")]
        ).apps
        User = old.get_model("identity", "User")
        Draft = old.get_model("workspace", "Draft")
        File = old.get_model("workspace", "PrivateFile")
        user = User.objects.create(mobile="+12025550888", password="!")
        draft = Draft.objects.create(
            creator=user, raw={"title": "پیش‌نویس قدیمی مصنوعی", "description": "داده خام حفظ شود"}
        )
        f = File.objects.create(
            uploader=user,
            draft=draft,
            kind="document",
            name="synthetic.pdf",
            size=3,
            sha256="a" * 64,
            content=b"abc",
            status="pending_check",
        )
        raw = draft.raw
        fid = f.pk
        did = draft.pk
        executor = MigrationExecutor(connection)
        executor.migrate(after)
        new = executor.loader.project_state(after).apps
        new_draft = new.get_model("workspace", "Draft").objects.get(pk=did)
        assert new_draft.kind == "project" and new_draft.raw == raw
        assert (
            bytes(new.get_model("workspace", "PrivateFile").objects.get(pk=fid).content) == b"abc"
        )
    finally:
        MigrationExecutor(connection).migrate(after)
