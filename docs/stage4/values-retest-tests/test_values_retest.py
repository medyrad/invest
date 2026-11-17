"""TEST-S04-04: only gaps in non-known bypasses and migration preservation."""
import importlib

import pytest
from django.apps import apps
from django.db import IntegrityError, connection, models, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

from apps.catalog.models import MoneyValue, Quantity, ReturnMetric, UnitDefinition
from tests.test_values_fixes import model_for, payload

LATEST = ('catalog', '0004_basis_integrity')
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolated_db():
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_')
    if not UnitDefinition.objects.exists():
        importlib.import_module('apps.catalog.migrations.0003_value_definitions').seed(apps, None)


@pytest.mark.parametrize('status', ['unknown', 'not_applicable'])
@pytest.mark.parametrize('kind', ['duration', 'return'])
@pytest.mark.parametrize('operation', ['insert', 'update'])
def test_missing_status_does_not_allow_partial_basis(kind, status, operation):
    model = model_for(kind)
    row = model.from_payload(payload(kind, status))
    if operation == 'update':
        row.save()
    with pytest.raises(IntegrityError), transaction.atomic():
        if operation == 'insert':
            row.basis = {}
            model.objects.bulk_create([row])
        else:
            model.objects.filter(pk=row.pk).update(basis={})
    if operation == 'update':
        row.refresh_from_db()
        assert row.basis == payload(kind, status)['basis']
    else:
        assert not model.objects.exists()


@pytest.mark.parametrize('kind,status', [('money', 'known'), ('return', 'unknown'), ('return', 'not_applicable')])
def test_json_null_direct_insert_roundtrip(kind, status):
    model = model_for(kind)
    row = model.from_payload(payload(kind, status))
    row.basis = models.Value(None, output_field=models.JSONField())
    model.objects.bulk_create([row])
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT basis IS NULL, jsonb_typeof(basis) FROM {model._meta.db_table} WHERE id=%s', [row.pk])
        assert cursor.fetchone() == (False, 'null')
    row.refresh_from_db()
    row.full_clean()
    assert row.basis is None


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('corrupt_kind', ['money', 'duration', 'return'])
def test_migration_preflight_each_table_is_atomic_and_preserves_all_types(corrupt_kind):
    rows = {kind: model_for(kind).from_payload(payload(kind)) for kind in ['money', 'duration', 'return']}
    for row in rows.values():
        row.save()
    original = {kind: row.as_dict() for kind, row in rows.items()}
    try:
        MigrationExecutor(connection).migrate([('catalog', '0003_value_definitions')])
        row = rows[corrupt_kind]
        invalid = {'money': {}, 'duration': None, 'return': {'metric_type': 'irr'}}[corrupt_kind]
        model_for(corrupt_kind).objects.filter(pk=row.pk).update(basis=invalid)
        with pytest.raises(IntegrityError):
            MigrationExecutor(connection).migrate([LATEST])
        assert LATEST not in MigrationRecorder(connection).applied_migrations()
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regprocedure('catalog_values_basis_valid(text,text,text,text,jsonb)')")
            assert cursor.fetchone()[0] is None
            cursor.execute("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgname IN ('money_basis_guard','quantity_basis_guard','return_basis_guard')")
            assert cursor.fetchone()[0] == 0
        for kind, item in rows.items():
            item.refresh_from_db()
            if kind == corrupt_kind:
                assert item.basis == invalid
            else:
                assert item.as_dict() == original[kind]
        model_for(corrupt_kind).objects.filter(pk=row.pk).update(basis=original[corrupt_kind]['basis'])
        MigrationExecutor(connection).migrate([LATEST])
        for kind, item in rows.items():
            item.refresh_from_db()
            item.full_clean()
            assert item.as_dict() == original[kind]
        with pytest.raises(IntegrityError), transaction.atomic():
            model_for(corrupt_kind).objects.filter(pk=row.pk).update(basis=invalid)
    finally:
        for kind, item in rows.items():
            model_for(kind).objects.filter(pk=item.pk).update(basis=original[kind]['basis'])
        MigrationExecutor(connection).migrate([LATEST])


@pytest.mark.parametrize('status', ['unknown', 'not_applicable'])
@pytest.mark.parametrize('json_null', [False, True])
@pytest.mark.parametrize('operation', ['insert', 'update'])
def test_duration_requires_basis_for_missing_status_with_both_nulls(status, json_null, operation):
    row = Quantity.from_payload(payload('duration', status))
    if operation == 'update':
        row.save()
    invalid = models.Value(None, output_field=models.JSONField()) if json_null else None
    with pytest.raises(IntegrityError), transaction.atomic():
        if operation == 'insert':
            row.basis = invalid
            Quantity.objects.bulk_create([row])
        else:
            Quantity.objects.filter(pk=row.pk).update(basis=invalid)
    if operation == 'update':
        row.refresh_from_db()
        assert row.basis == payload('duration', status)['basis']
    else:
        assert not Quantity.objects.exists()
