import io
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.db import close_old_connections
from django.utils import timezone

from apps.identity.models import User
from apps.workspace import files, service
from apps.workspace.models import Draft, PrivateFile
from tests.test_workspace import create, save
from tests.test_workspace_files import image_bytes, reserve

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def definitions(db):
    import importlib

    from django.apps import apps

    from apps.catalog.models import FieldDefinition, UnitDefinition

    if not UnitDefinition.objects.exists():
        importlib.import_module("apps.catalog.migrations.0003_value_definitions").seed(apps, None)
    if not FieldDefinition.objects.filter(key="deposit").exists():
        importlib.import_module("apps.catalog.migrations.0005_project_fields").seed(apps, None)


def concurrent_pair(user_id, operation):
    barrier = threading.Barrier(2)

    def run(index):
        close_old_connections()
        try:
            user = User.objects.get(pk=user_id)
            barrier.wait(timeout=10)
            try:
                return operation(user, index)
            except service.Fault as e:
                return e.status
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(run, range(2)))


def test_atomic_account_budget(accounts, settings):
    a = accounts[0]
    ds = [create(a), create(a)]
    blob = image_bytes()
    settings.WORKSPACE_ACCOUNT_BYTES = len(blob)
    results = concurrent_pair(a.pk, lambda u, n: reserve(u, ds[n], blob)["id"])
    assert len([r for r in results if r == 429]) == 1
    assert PrivateFile.objects.count() == 1


def test_atomic_entity_count(accounts):
    a = accounts[0]
    d = create(a)
    blob = image_bytes()
    for _ in range(9):
        reserve(a, d, blob)
    results = concurrent_pair(a.pk, lambda u, n: reserve(u, d, blob)["id"])
    assert len([r for r in results if r == 429]) == 1
    assert PrivateFile.objects.count() == 10


def test_same_operation_and_concurrent_version(accounts):
    import uuid

    a = accounts[0]
    key = str(uuid.uuid4())
    results = concurrent_pair(a.pk, lambda u, n: create(u, key=key)["id"])
    assert results[0] == results[1] and Draft.objects.count() == 1
    d = service.get_draft(a, results[0])
    results = concurrent_pair(a.pk, lambda u, n: save(u, d, {"title": f"نسخه{n}"})["version"])
    assert sorted(results) == [2, 409]


def test_scan_does_not_lock_text_and_purge_wins(accounts, monkeypatch):
    a = accounts[0]
    d = create(a)
    blob = image_bytes()
    r = reserve(a, d, blob)
    files.receive(a, r["id"], io.BytesIO(blob))
    at = timezone.now() + timedelta(days=2)
    started = threading.Event()
    finish = threading.Event()

    def slow(_):
        started.set()
        assert finish.wait(10)
        return "clean"

    monkeypatch.setattr(files, "scan", slow)

    def worker():
        close_old_connections()
        try:
            return files.check_one(at)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        try:
            assert started.wait(10)
            assert save(a, d, {"title": "متن هنگام بررسی"})["version"] == 2
            assert files.purge(at) == 1
        finally:
            finish.set()
        assert future.result(timeout=15)
    f = PrivateFile.objects.get(pk=r["id"])
    assert f.purged_at and f.content is None and not f.attached
