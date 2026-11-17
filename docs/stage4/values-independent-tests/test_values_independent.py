"""TEST-S04-03: boundary and bypass cases missing from the delivered suite.
Every mutation, including migrations, is restricted to pytest's PostgreSQL database.
"""
import copy
import importlib
from decimal import Decimal

import pytest
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from rest_framework.test import APIClient

from apps.catalog.models import (
    City, County, FieldDefinition, Group, MoneyValue, Province, Quantity,
    ReturnMetric, Subtype, UnitDefinition,
)
from apps.catalog.values import MAX_VALUE, ValueErrorDetail, compare, normalize

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def isolated_definitions():
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_'), 'Never mutate application DB'
    if not UnitDefinition.objects.exists():
        importlib.import_module('apps.catalog.migrations.0003_value_definitions').seed(apps, None)


def payload(value='1.5', unit='BILLION_TOMAN', key='min_capital', namespace='project', status='known', basis=None):
    return {'field': {'namespace':'invest.opportunity.'+namespace,'key':key,'version':1},
            'unit':{'code':unit,'version':1},'status':status,'source_value':value,'basis':basis}


def basis():
    return {'version':1,'metric_type':'irr','period':'annual',
            'horizon':{'value':'5','unit':{'code':'YEAR','version':1}},
            'basis_date':'2026-11-17','price_basis':'nominal','scope':'investor',
            'observation':'claimed','source':'synthetic independent source'}


def api():
    client=APIClient(enforce_csrf_checks=True)
    csrf=client.get('/api/v1/auth/csrf').json()['csrfToken']
    return client, {'HTTP_X_CSRFTOKEN':csrf}


def custom(key, units, kind='quantity', version=1, return_type=''):
    unit=UnitDefinition.objects.get(code=units[0],version=1)
    return FieldDefinition.objects.create(namespace='independent.exact',key=key,version=version,label='داده مصنوعی آزمون',
        kind=kind,unit=unit,allowed_units=[{'code':c,'version':1} for c in units],
        minimum=MAX_VALUE.copy_negate() if kind=='return' else Decimal(0),maximum=MAX_VALUE,
        source_path='synthetic',source_locator='independent fixture',meaning='synthetic',return_type=return_type)


@pytest.mark.parametrize('value,unit,expected',[
    ('۱٫۵','BILLION_TOMAN','1500000000'),('١٬٥٠٠','MILLION_TOMAN','1500000000'),
    ('0.000000001','BILLION_TOMAN','1'),
    ('999999999999999.999999999','BILLION_TOMAN','999999999999999999999999'),
    ('999999999999999999999999.999999999','TOMAN','999999999999999999999999.999999999'),
])
def test_transport_and_database_exact_boundaries(value,unit,expected):
    client,headers=api();body=payload(value,unit)
    response=client.post('/api/v1/catalog/values/normalize',body,format='json',**headers)
    assert response.status_code==200,response.data
    dto=response.json();assert dto['value']==expected and isinstance(dto['value'],str)
    assert MoneyValue.objects.count()==0
    row=MoneyValue.from_payload(body);row.save();row.refresh_from_db()
    assert row.value==Decimal(expected) and row.as_dict()==dto


@pytest.mark.parametrize('bad',['1000000000000000000000000','0.0000000001',1,1.5,True,[],{},'1,50','1,234٬567','1.2٫3','1e3','NaN','∞','1 000','۱/۵'])
def test_invalid_inputs_are_http_400_not_rounded(bad):
    client,headers=api()
    response=client.post('/api/v1/catalog/values/normalize',payload(bad,'TOMAN'),format='json',**headers)
    assert response.status_code==400,response.data
    assert response.json()['error']['fields']
    assert not MoneyValue.objects.exists()


@pytest.mark.parametrize('ref,key', [('field','namespace'),('field','key'),('unit','code')])
def test_embedded_nul_reference_is_validation_error_not_http_500(ref,key):
    client,headers=api();body=payload();body[ref][key]+='\x00'
    response=client.post('/api/v1/catalog/values/normalize',body,format='json',**headers)
    assert response.status_code==400, f'NUL {ref}.{key} returned {response.status_code}: {response.data}'


@pytest.mark.parametrize('body',[None,[],{},'string',{'field':[]},False])
def test_bad_json_shapes_never_create_http_500(body):
    import json
    client,headers=api()
    response=client.post('/api/v1/catalog/values/normalize',json.dumps(body),content_type='application/json',**headers)
    assert response.status_code==400,response.data


def test_csrf_malformed_json_and_no_public_writes():
    client,headers=api();url='/api/v1/catalog/values/normalize'
    assert client.post(url,payload(),format='json').status_code==403
    assert client.post(url,'{"field":',content_type='application/json',**headers).status_code==400
    before=tuple(m.objects.count() for m in (UnitDefinition,FieldDefinition,MoneyValue,Quantity,ReturnMetric))
    for status,value in [('known','0'),('unknown',None),('not_applicable',None)]:
        response=client.post(url,payload(value,status=status),format='json',**headers)
        assert response.status_code==200,response.data
        assert response.json()['value']==('0' if status=='known' else None)
    assert tuple(m.objects.count() for m in (UnitDefinition,FieldDefinition,MoneyValue,Quantity,ReturnMetric))==before


@pytest.mark.parametrize('change',[
    {'value':Decimal('2')}, {'source_value':Decimal('2')}, {'conversion_factor':Decimal('2')},
    {'base_unit':'USD'}, {'base_version':2}, {'status':'not_applicable'},
])
def test_queryset_update_rejects_numeric_snapshot_tampering(change):
    row=MoneyValue.from_payload(payload('1','TOMAN'));row.save()
    with pytest.raises(IntegrityError),transaction.atomic():
        MoneyValue.objects.filter(pk=row.pk).update(**change)
    row.refresh_from_db();assert row.value==Decimal('1')


@pytest.mark.parametrize('target',['unit','definition'])
def test_direct_fk_update_cannot_change_kind_or_allowed_unit(target):
    row=MoneyValue.from_payload(payload('1','TOMAN'));row.save()
    change={'unit':UnitDefinition.objects.get(code='USD')} if target=='unit' else {'definition':FieldDefinition.objects.get(key='area')}
    with pytest.raises(IntegrityError),transaction.atomic():
        MoneyValue.objects.filter(pk=row.pk).update(**change)


@pytest.mark.parametrize('kind', ['money','duration','return'])
def test_queryset_cannot_persist_basis_rejected_by_application(kind):
    if kind=='money':
        model=MoneyValue;body=payload('1','TOMAN');invalid={'start_basis':'unexpected'}
    elif kind=='duration':
        model=Quantity;body=payload('1','MONTH','execution_months',basis={'start_basis':'contract_signed'});invalid=None
    else:
        model=ReturnMetric;body=payload('10','PERCENT','irr',basis=basis());invalid={'metric_type':'irr'}
    row=model.from_payload(body);row.save();row.basis=invalid
    with pytest.raises(ValidationError):row.full_clean()
    rejected=False
    try:
        with transaction.atomic():model.objects.filter(pk=row.pk).update(basis=invalid)
    except IntegrityError:rejected=True
    row.refresh_from_db()
    if not rejected:
        assert row.basis == invalid
    assert rejected, f'{model.__name__}: SQL UPDATE persisted basis that full_clean rejects: {row.basis!r}'


@pytest.mark.parametrize('model_name,operation',[('unit','update'),('unit','delete'),('field','update'),('field','delete')])
def test_published_definitions_are_immutable_even_when_unused(model_name,operation):
    unit=UnitDefinition.objects.create(code='INDEPENDENT_ITEM',version=1,kind='quantity',base_code='ITEM',factor=Decimal(1))
    field=custom('unused',['ITEM'])
    query=UnitDefinition.objects.filter(pk=unit.pk) if model_name=='unit' else FieldDefinition.objects.filter(pk=field.pk)
    with pytest.raises(IntegrityError),transaction.atomic():
        if operation=='delete':query.delete()
        else:query.update(version=2)


def test_append_version_does_not_reinterpret_old_record_or_snapshot():
    old=MoneyValue.from_payload(payload());old.save();snapshot=old.as_dict()
    field=custom('money',['TOMAN'],kind='money');new=custom('money',['TOMAN'],kind='money',version=2)
    a=normalize({**payload('1','TOMAN'),'field':field.reference()})
    b=normalize({**payload('1','TOMAN'),'field':new.reference()})
    assert compare(a,b)['comparable'] is False
    old.refresh_from_db();assert old.as_dict()==snapshot
    forged=copy.deepcopy(snapshot);forged['contract_version']=2
    with pytest.raises(ValueErrorDetail):compare(snapshot,forged)


def test_currency_calendar_dimensions_count_and_meaning_stay_separate():
    field=custom('money',['TOMAN','USD'],kind='money')
    a=normalize({**payload('1','TOMAN'),'field':field.reference()});b=normalize({**payload('1','USD'),'field':field.reference()})
    assert b['value']=='1' and b['base_unit']=='USD' and not compare(a,b)['comparable']
    duration=custom('duration',['DAY','MONTH','YEAR'])
    facts=[normalize({**payload('1',unit,basis={'start_basis':'contract_signed'}),'field':duration.reference()}) for unit in ('DAY','MONTH','YEAR')]
    assert all(x['value']=='1' for x in facts)
    for x,y in ((facts[0],facts[1]),(facts[1],facts[2])):assert not compare(x,y)['comparable']
    unspecified=normalize({**payload('1','MONTH',basis={'start_basis':'unspecified'}),'field':duration.reference()})
    assert not compare(unspecified,unspecified)['comparable']
    count=custom('count',['ITEM'])
    with pytest.raises(ValueErrorDetail):normalize({**payload('1.5','ITEM'),'field':count.reference()})
    assert not compare(normalize(payload('1')),normalize(payload('1',key='budget')))['comparable']


@pytest.mark.parametrize('change',[{'period':'monthly'},{'scope':'project'},{'price_basis':'real'},{'basis_date':'2025-11-17'},{'observation':'observed'}])
def test_return_comparison_requires_identical_full_basis(change):
    a=normalize(payload('10','PERCENT','irr',basis=basis()));other=basis();other.update(change)
    b=normalize(payload('10','PERCENT','irr',basis=other));assert not compare(a,b)['comparable']
    wrong=basis();wrong['metric_type']='simple_rate'
    with pytest.raises(ValueErrorDetail):normalize(payload('10','PERCENT','irr',basis=wrong))


def test_migration_roundtrip_preserves_every_old_catalog_row():
    call_command('import_reference')
    models=(Group,Subtype,Province,County,City)
    before=[list(m.objects.order_by('pk').values()) for m in models]
    assert [len(rows) for rows in before]==[11,78,31,478,22]
    executor=MigrationExecutor(connection)
    try:
        executor.migrate([('catalog','0001_initial')])
        assert 'catalog_moneyvalue' not in connection.introspection.table_names()
        assert [list(m.objects.order_by('pk').values()) for m in models]==before
        MigrationExecutor(connection).migrate([('catalog','0003_value_definitions')])
        assert [list(m.objects.order_by('pk').values()) for m in models]==before
        assert UnitDefinition.objects.count()==11 and FieldDefinition.objects.count()==8
        row=MoneyValue.from_payload(payload('999999999999999999999999.999999999','TOMAN'));row.save();row.refresh_from_db()
        assert row.value==MAX_VALUE
    finally:
        MigrationExecutor(connection).migrate([('catalog','0003_value_definitions')])
