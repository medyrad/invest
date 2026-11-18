import importlib
import uuid
from datetime import timedelta
import pytest
from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from apps.catalog.models import UnitDefinition, FieldDefinition
from apps.workspace import service
from apps.workspace.models import Organization, RepresentationRequest, Representation
from tests.test_workspace import create
from tests.conftest import accounts  # existing fixture, outside /independent discovery

pytestmark = pytest.mark.django_db

@pytest.fixture(autouse=True)
def isolated():
    assert connection.vendor == 'postgresql' and connection.settings_dict['NAME'].startswith('test_')


def test_lost_save_replay_preserves_exact_receipt_and_one_revision(accounts):
    a=accounts[0];d=create(a)
    body=dict(key=str(uuid.uuid4()),version=d['version'],routes=['lessee'],heritage_enabled=False,values={'title':'ذخیره مستقل'})
    first=service.save_draft(a,d['id'],body)
    second=service.save_draft(a,d['id'],body)
    assert first==second
    assert service.get_draft(a,d['id'])['raw']['title']=='ذخیره مستقل'
    assert service.get_draft(a,d['id'])['version']==2
    with pytest.raises(service.Fault):service.save_draft(a,d['id'],{**body,'values':{'title':'بدنه متفاوت'}})


@pytest.mark.parametrize('state',['hold','revoked','expired'])
def test_restore_and_receipt_replay_require_current_authority(accounts,state):
    a=accounts[0]
    org=Organization.objects.create(name='مصنوعی',country='ایران',registration='independent')
    request=RepresentationRequest.objects.create(organization=org,applicant=a,details={},status='approved')
    grant=Representation.objects.create(organization=org,user=a,status='active')
    d=create(a,{'kind':'organization','request_id':str(request.pk)})
    body={'key':str(uuid.uuid4()),'version':d['version']}
    deleted=service.draft_action(a,d['id'],'delete',body)
    if state=='expired':grant.ends_at=timezone.now()-timedelta(seconds=1)
    else:grant.status=state
    grant.save()
    for action,data in [('delete',body),('restore',{'key':str(uuid.uuid4()),'version':deleted['version']})]:
        with pytest.raises(service.Fault) as err:service.draft_action(a,d['id'],action,data)
        assert err.value.status==403
    assert not service.list_drafts(a,trash=True)


@pytest.mark.django_db(transaction=True)
def test_incremental_catalog_migrations_preserve_v1_definitions():
    target=[('catalog','0006_project_capacity_units')]
    executor=MigrationExecutor(connection)
    try:
        executor.migrate([('catalog','0004_basis_integrity')])
        before_units=list(UnitDefinition.objects.order_by('pk').values())
        before_fields=list(FieldDefinition.objects.order_by('pk').values())
        MigrationExecutor(connection).migrate(target)
        assert list(UnitDefinition.objects.filter(pk__in=[r['id'] for r in before_units]).order_by('pk').values())==before_units
        assert list(FieldDefinition.objects.filter(pk__in=[r['id'] for r in before_fields]).order_by('pk').values())==before_fields
    finally:MigrationExecutor(connection).migrate(target)
