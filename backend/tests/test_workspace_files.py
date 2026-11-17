import hashlib
import io
import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from PIL import Image

from apps.workspace import files, service
from apps.workspace.models import PrivateFile
from tests.test_workspace import create

pytestmark = pytest.mark.django_db


def image_bytes():
    b = io.BytesIO()
    Image.new("RGB", (20, 20), "green").save(b, format="PNG")
    return b.getvalue()


def reserve(user, d, content, kind="image", name="test.png", replaces=None):
    return files.reserve(
        user,
        {
            "key": str(uuid.uuid4()),
            "target_type": "draft",
            "target_id": d["id"],
            "kind": kind,
            "name": name,
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "replaces": replaces,
        },
    )


def test_pending_private_and_outage(accounts, monkeypatch):
    a, b = accounts
    d = create(a)
    blob = image_bytes()
    r = reserve(a, d, blob)
    files.receive(a, r["id"], io.BytesIO(blob))
    with pytest.raises(service.Fault):
        files.download(a, r["id"])
    monkeypatch.setattr(files, "scan", lambda data: (_ for _ in ()).throw(OSError()))
    files.check_one()
    f = PrivateFile.objects.get(pk=r["id"])
    assert f.status == "pending_check" and f.attempts == 1
    assert service.get_draft(a, d["id"])["files"][0]["status"] == "pending_check"
    with pytest.raises(service.Fault):
        files.download(b, r["id"])


def test_replace_delete_restore_purge(accounts, monkeypatch):
    a = accounts[0]
    d = create(a)
    blob = image_bytes()
    monkeypatch.setattr(files, "scan", lambda data: "clean")
    old = reserve(a, d, blob)
    files.receive(a, old["id"], io.BytesIO(blob))
    files.check_one()
    assert files.download(a, old["id"])[1] == "image/jpeg"
    new = reserve(a, d, b"bad", replaces=old["id"])
    files.receive(a, new["id"], io.BytesIO(b"bad"))
    files.check_one()
    assert PrivateFile.objects.get(pk=old["id"]).attached
    files.action(a, old["id"], "file-delete", {})
    with pytest.raises(service.Fault):
        files.download(a, old["id"])
    files.action(a, old["id"], "file-restore", {})
    assert files.download(a, old["id"])[0]
    files.action(a, old["id"], "file-delete", {})
    files.purge(timezone.now() + timedelta(days=31))
    assert PrivateFile.objects.get(pk=old["id"]).purged_at


def test_checksum_limit_and_idempotency(accounts):
    a = accounts[0]
    d = create(a)
    blob = image_bytes()
    r = reserve(a, d, blob)
    with pytest.raises(service.Fault):
        files.receive(a, r["id"], io.BytesIO(blob + b"x"))
    files.receive(a, r["id"], io.BytesIO(blob))
    files.receive(a, r["id"], io.BytesIO(blob))
    assert PrivateFile.objects.count() == 1


def test_real_scanner_clean_and_eicar(accounts, settings):
    settings.CLAMAV_HOST = "scanner"
    assert files.scan(image_bytes()) == "clean"
    # Standard harmless 68-byte anti-malware test string; never executable malware.
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    assert files.scan(eicar) == "quarantined"
    a = accounts[0]
    d = create(a)
    r = reserve(a, d, eicar, kind="document", name="test.pdf")
    files.receive(a, r["id"], io.BytesIO(eicar))
    files.check_one()
    assert PrivateFile.objects.get(pk=r["id"]).status == "quarantined"
    with pytest.raises(service.Fault):
        files.download(a, r["id"])


def test_real_connection_outage_text_save_and_retry(accounts, settings):
    from tests.test_workspace import save

    a = accounts[0]
    d = create(a)
    blob = image_bytes()
    r = reserve(a, d, blob)
    files.receive(a, r["id"], io.BytesIO(blob))
    settings.CLAMAV_HOST = "127.0.0.1"
    settings.CLAMAV_PORT = 1
    assert files.check_one()
    row = PrivateFile.objects.get(pk=r["id"])
    assert row.status == "pending_check" and not row.attached
    assert save(a, d, {"title": "متن هنگام قطعی واقعی اسکن"})["version"] == 2
    with pytest.raises(service.Fault):
        files.download(a, r["id"])
    settings.CLAMAV_HOST = "scanner"
    settings.CLAMAV_PORT = 3310
    assert files.check_one(row.next_check + timedelta(seconds=1))
    row.refresh_from_db()
    assert row.status == "clean" and row.attached


@pytest.mark.parametrize(
    "state,days", [("rejected", 7), ("quarantined", 7), ("replaced", 30), ("deleted", 30)]
)
def test_each_retention_boundary(accounts, state, days):
    a = accounts[0]
    at = timezone.now()
    r = reserve(a, create(a), image_bytes())
    f = PrivateFile.objects.get(pk=r["id"])
    f.created_at = at
    if state in ["rejected", "quarantined"]:
        f.status = state
        f.checked_at = at
    elif state == "replaced":
        f.status = "clean"
        f.replaced_at = at
    else:
        f.status = "clean"
        f.deleted_at = at
        f.attached = True
    f.save()
    assert files.purge(at + timedelta(days=days) - timedelta(microseconds=1)) == 0
    assert files.purge(at + timedelta(days=days)) == 1
