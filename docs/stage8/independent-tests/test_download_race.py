import uuid
from concurrent.futures import ThreadPoolExecutor,TimeoutError
from threading import Event
from types import SimpleNamespace
import pytest
from django.conf import settings
from django.db import connection,close_old_connections
from django.utils import timezone
from rest_framework.test import APIClient
from apps.identity.models import User
from apps.identity.sessions import mint_session
from apps.workspace.models import Draft,Organization,Representation
from apps.services import service
from tests.test_services import complete_raw

@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('output',['download','package'])
def test_authority_change_before_report_bytes_are_generated(output,monkeypatch):
    assert settings.INVEST_ENV=='test' and connection.settings_dict['NAME'].startswith('test_')
    old=User.objects.create_user(mobile='+12025550801');new=User.objects.create_user(mobile='+12025550802')
    org=Organization.objects.create(name='سازمان مصنوعی مستقل',country='ایران',registration='TEST-RACE')
    rep=Representation.objects.create(user=old,organization=org,status='active')
    draft=Draft.objects.create(kind='ideas',creator=old,organization=org,raw=complete_raw('ideas'))
    report=service.create_report(SimpleNamespace(user=old),draft.pk,{'key':str(uuid.uuid4()),'version':1})
    _,token=mint_session(old,timezone.now());authorized=Event();release=Event();original=service.get_report
    def delayed(*args):
        value=original(*args);authorized.set();assert release.wait(5);return value
    monkeypatch.setattr(service,'get_report',delayed)
    def reader():
        close_old_connections()
        try:
            client=APIClient();client.cookies['invest_session']=token
            return client.get(f'/api/v1/services/reports/{report["id"]}/{output}').status_code
        finally:close_old_connections()
    def replace():
        close_old_connections()
        try:
            from django.db import transaction
            with transaction.atomic():
                Organization.objects.select_for_update().get(pk=org.pk)
                Representation.objects.filter(pk=rep.pk).update(status='revoked')
                Representation.objects.create(user_id=new.pk,organization_id=org.pk,status='active')
        finally:close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        download=pool.submit(reader);assert authorized.wait(5);replacement=pool.submit(replace)
        try:
            replacement.result(timeout=1);committed_before_bytes=True
        except TimeoutError:committed_before_bytes=False
        finally:release.set()
        status=download.result(timeout=5);replacement.result(timeout=5)
    assert not committed_before_bytes or status in [403,409],f'{output}: replacement committed before rendering but response was {status}'

@pytest.mark.django_db(transaction=True)
def test_package_does_not_emit_file_quarantined_during_generation(monkeypatch):
    from pathlib import Path
    from apps.workspace.models import PrivateFile
    from apps.workspace.schema import Fault
    assert settings.INVEST_ENV=='test' and connection.settings_dict['NAME'].startswith('test_')
    user=User.objects.create_user(mobile='+12025550803')
    d=Draft.objects.create(kind='ideas',creator=user,raw=complete_raw('ideas'))
    data=Path('/src/tests/fixtures/s08/synthetic.pdf').read_bytes()
    f=PrivateFile.objects.create(draft=d,uploader=user,kind='document',name='synthetic.pdf',size=len(data),sha256='a'*64,status='clean',attached=True,media_type='application/pdf',content=data)
    receipt=service.create_report(SimpleNamespace(user=user),d.pk,{'key':str(uuid.uuid4()),'version':1})
    selected=Event();release=Event();original=service.report_html
    def delayed(report):
        selected.set();assert release.wait(5);return original(report)
    monkeypatch.setattr(service,'report_html',delayed)
    def download():
        close_old_connections()
        try:
            try:return service.report_package(service.get_report(User.objects.get(pk=user.pk),receipt['id']))
            except Fault:return None
        finally:close_old_connections()
    def quarantine():
        close_old_connections()
        try:PrivateFile.objects.filter(pk=f.pk).update(status='quarantined')
        finally:close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        result=pool.submit(download);assert selected.wait(5);change=pool.submit(quarantine)
        try:change.result(timeout=1);committed=True
        except TimeoutError:committed=False
        finally:release.set()
        body=result.result(timeout=5);change.result(timeout=5)
    import io,zipfile
    archived_files=[] if body is None else [n for n in zipfile.ZipFile(io.BytesIO(body)).namelist() if n.startswith('attachments/')]
    assert not committed or not archived_files,f'ZIP emitted quarantined attachment paths: {archived_files}'
