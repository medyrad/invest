import pytest
from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from apps.catalog.models import FieldDefinition,UnitDefinition,MoneyValue,Quantity,ReturnMetric
from tests.test_values import payload,basis

@pytest.mark.django_db(transaction=True)
def test_new_operator_migration_preserves_old_records_without_consumers():
    assert settings.INVEST_ENV=='test' and connection.vendor=='postgresql' and connection.settings_dict['NAME'].startswith('test_')
    latest=[('catalog','0010_operator_work_period')]
    old_fields=list(FieldDefinition.objects.exclude(key='operator_work_period').order_by('pk').values())
    units=list(UnitDefinition.objects.order_by('pk').values())
    bodies=[(MoneyValue,payload('budget','TOMAN','2')),(Quantity,payload('area','SQUARE_METRE','3.25',namespace='sale')),(ReturnMetric,payload('irr','PERCENT','10',basis=basis()))]
    records=[]
    for model,body in bodies:
        row=model.from_payload(body);row.save();records.append((row,row.as_dict()))
    try:
        MigrationExecutor(connection).migrate([('catalog','0009_signed_fund_returns')])
        assert not FieldDefinition.objects.filter(key='operator_work_period').exists()
        MigrationExecutor(connection).migrate(latest)
        assert list(FieldDefinition.objects.exclude(key='operator_work_period').order_by('pk').values())==old_fields
        assert list(UnitDefinition.objects.order_by('pk').values())==units
        for row,snapshot in records:row.refresh_from_db();assert row.as_dict()==snapshot
    finally:MigrationExecutor(connection).migrate(latest)
