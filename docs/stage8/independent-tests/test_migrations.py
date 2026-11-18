import pytest
from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from apps.identity.models import User
from apps.workspace.models import Draft,PrivateFile
from apps.catalog.models import FieldDefinition,UnitDefinition

@pytest.mark.django_db(transaction=True)
def test_five_migrations_keep_old_draft_blob_and_definitions():
    assert settings.INVEST_ENV=='test' and connection.settings_dict['NAME'].startswith('test_')
    latest=MigrationExecutor(connection).loader.graph.leaf_nodes()
    old=[('services',None),('core','0004_reviewevidence'),('workspace','0003_draft_kind'),('catalog','0010_operator_work_period')]
    try:
        MigrationExecutor(connection).migrate(old)
        u=User.objects.create_user(mobile='+12025550809');d=Draft.objects.create(creator=u,kind='project',raw={'title':'پیش‌نویس مصنوعی قدیمی'})
        f=PrivateFile.objects.create(draft=d,uploader=u,kind='document',name='old.txt',size=3,sha256='a'*64,status='pending_check',content=b'old')
        fields=list(FieldDefinition.objects.order_by('pk').values());units=list(UnitDefinition.objects.order_by('pk').values())
        for target in [latest,old,latest]:
            MigrationExecutor(connection).migrate(target);d.refresh_from_db();f.refresh_from_db()
            assert d.raw=={'title':'پیش‌نویس مصنوعی قدیمی'} and bytes(f.content)==b'old'
            assert list(FieldDefinition.objects.filter(pk__in=[x['id'] for x in fields]).order_by('pk').values())==fields
            assert list(UnitDefinition.objects.filter(pk__in=[x['id'] for x in units]).order_by('pk').values())==units
    finally:MigrationExecutor(connection).migrate(latest)
