"""FIX-01: two real connections, proven lock ordering and actual response bytes."""

import io
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest
from django.db import close_old_connections, connection, transaction

from apps.identity.models import User
from apps.services import service
from apps.workspace.models import Draft, Organization, PrivateFile, Representation
from apps.workspace.schema import Fault
from tests.test_services import complete_raw

pytestmark = pytest.mark.django_db(transaction=True)


def setup_report(organization=False):
    u = User.objects.create_user(mobile="+12025550871")
    org = (
        Organization.objects.create(name="سازمان مصنوعی", country="ایران", registration="FIX")
        if organization
        else None
    )
    if org:
        Representation.objects.create(user=u, organization=org, status="active")
    d = Draft.objects.create(kind="ideas", creator=u, organization=org, raw=complete_raw("ideas"))
    data = (Path(__file__).parent / "fixtures/s08/synthetic.pdf").read_bytes()
    f = PrivateFile.objects.create(
        draft=d,
        uploader=u,
        kind="document",
        name="synthetic.pdf",
        size=len(data),
        sha256="a" * 64,
        status="clean",
        attached=True,
        media_type="application/pdf",
        content=data,
    )
    receipt = service.create_report(
        SimpleNamespace(user=u), d.pk, {"key": str(uuid.uuid4()), "version": 1}
    )
    return u, org, f, receipt["id"], data


def connected(fn):
    close_old_connections()
    try:
        return fn()
    finally:
        close_old_connections()


def wait_for_database_block(pid):
    # Observe an actual PostgreSQL lock wait; elapsed timeout is a failure, never evidence.
    deadline = time.monotonic() + 5
    with connection.cursor() as cursor:
        while time.monotonic() < deadline:
            cursor.execute("SELECT cardinality(pg_blocking_pids(%s))", [pid])
            if cursor.fetchone()[0]:
                return
    pytest.fail("contending connection never reached a database lock wait")


@pytest.mark.parametrize("package", [False, True, "json"])
def test_download_holds_org_until_bytes_and_revoked_customer_is_rejected(package, monkeypatch):
    u, org, f, rid, data = setup_report(True)
    entered, release, writer_started = Event(), Event(), Event()
    writer_pid = []
    original = service.get_report

    def paused(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)

    def replacement():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            writer_pid.append(cursor.fetchone()[0])
        writer_started.set()
        with transaction.atomic():
            Organization.objects.select_for_update().get(pk=org.pk)
            Representation.objects.filter(user=u, organization=org).update(status="revoked")

    monkeypatch.setattr(service, "get_report", paused)
    with ThreadPoolExecutor(2) as pool:
        download = pool.submit(
            connected,
            lambda: service.render_report(u, rid, package is True, as_json=package == "json"),
        )
        assert entered.wait(5)
        writer = pool.submit(connected, replacement)
        try:
            assert writer_started.wait(5)
            wait_for_database_block(writer_pid[0])
            assert not writer.done()
        finally:
            release.set()
        body = download.result(timeout=5)
        writer.result(timeout=5)
    if package is True:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            assert (
                archive.read(next(n for n in archive.namelist() if n.startswith("attachments/")))
                == data
            )
    else:
        assert "دریافت بسته" in body
    monkeypatch.setattr(service, "get_report", original)
    with pytest.raises(Fault) as error:
        service.render_report(u, rid, package is True, as_json=package == "json")
    assert error.value.status == 403


def test_package_serializes_quarantine_until_actual_archive_is_complete(monkeypatch):
    u, _, f, rid, data = setup_report()
    entered, release, started = Event(), Event(), Event()
    pid = []
    original = service.report_html

    def paused(report):
        entered.set()
        assert release.wait(5)
        return original(report)

    def quarantine():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            pid.append(cursor.fetchone()[0])
        started.set()
        PrivateFile.objects.filter(pk=f.pk).update(status="quarantined")

    monkeypatch.setattr(service, "report_html", paused)
    with ThreadPoolExecutor(2) as pool:
        download = pool.submit(connected, lambda: service.render_report(u, rid, True))
        assert entered.wait(5)
        change = pool.submit(connected, quarantine)
        try:
            assert started.wait(5)
            wait_for_database_block(pid[0])
            assert not change.done()
        finally:
            release.set()
        body = download.result(timeout=5)
        change.result(timeout=5)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        assert (
            archive.read(next(n for n in archive.namelist() if n.startswith("attachments/")))
            == data
        )
    with pytest.raises(Fault) as error:
        service.render_report(u, rid, True)
    assert error.value.status == 409


@pytest.mark.parametrize("state", ["quarantined", "pending_check", "deleted"])
def test_file_change_committed_first_rejects_package(state):
    u, _, f, rid, _ = setup_report()
    from django.utils import timezone

    update = {"deleted_at": timezone.now()} if state == "deleted" else {"status": state}
    with ThreadPoolExecutor(1) as pool:
        pool.submit(connected, lambda: PrivateFile.objects.filter(pk=f.pk).update(**update)).result(
            timeout=5
        )
    with pytest.raises(Fault) as error:
        service.render_report(u, rid, True)
    assert error.value.status == 409


@pytest.mark.parametrize("value,label", [(True, "بله"), (False, "خیر")])
def test_boolean_report_preserves_false_and_persian_label(value, label):
    from apps.core.models import Report

    u = User.objects.create_user(mobile="+12025550872")
    d = Draft.objects.create(kind="charity", creator=u, raw={"demo": value})
    receipt = service.create_report(
        SimpleNamespace(user=u), d.pk, {"key": str(uuid.uuid4()), "version": 1}
    )
    report = Report.objects.get(pk=receipt["id"])
    assert report.snapshot["effective"]["demo"] is value
    assert ">" + label + "</dd>" in service.render_report(u, receipt["id"])


def test_download_transaction_only_translates_lock_timeout():
    from django.db import OperationalError

    from apps.workspace.downloads import download_transaction

    class PgError(Exception):
        sqlstate = "55P03"

    @download_transaction
    def failing(cause):
        raise OperationalError("synthetic") from cause

    with pytest.raises(Fault) as error:
        failing(PgError())
    assert error.value.status == 409
    with pytest.raises(OperationalError):
        failing(ValueError("unrelated"))
