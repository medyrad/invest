import hashlib,io,uuid
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
import pytest
from django.conf import settings
from django.db import connection
from django.utils import timezone
from apps.identity.models import User
from apps.workspace.models import Draft,PrivateFile
from apps.workspace import files
from apps.workspace.schema import Fault
from apps.services import service
from tests.test_services import complete_raw

@pytest.mark.django_db(transaction=True)
def test_scanner_unavailable_keeps_service_text_and_retries_to_quarantine(monkeypatch):
    assert settings.INVEST_ENV=='test' and connection.settings_dict['NAME'].startswith('test_')
    user=User.objects.create_user(mobile='+12025550807')
    d=Draft.objects.create(creator=user,kind='ideas',raw=complete_raw('ideas'))
    content=Path('/src/tests/fixtures/s08/synthetic.pdf').read_bytes()
    reservation={'key':str(uuid.uuid4()),'target_type':'draft','target_id':str(d.pk),'kind':'document','name':'synthetic.pdf','size':len(content),'sha256':hashlib.sha256(content).hexdigest(),'replaces':None}
    with pytest.raises(Fault):files.reserve(user,{**reservation,'key':str(uuid.uuid4()),'name':'forbidden.exe'})
    f=files.reserve(user,reservation);files.receive(user,f['id'],io.BytesIO(content))
    def offline(_):raise OSError('synthetic isolated scanner failure')
    monkeypatch.setattr(files,'scan',offline);assert files.check_one()
    row=PrivateFile.objects.get(pk=f['id']);assert row.status=='pending_check' and row.attempts==1 and row.next_check>timezone.now()
    assert 'دسترس نیست' in row.reason
    from apps.workspace import service as workspace
    saved=workspace.save_draft(user,d.pk,{'key':str(uuid.uuid4()),'version':1,'routes':[],'heritage_enabled':False,'values':{'title':'متن خصوصی هنگام قطع اسکن محفوظ است'}})
    d.refresh_from_db();assert d.raw['title']=='متن خصوصی هنگام قطع اسکن محفوظ است'
    with pytest.raises(Fault):files.download(user,row.pk)
    receipt=service.submit(SimpleNamespace(user=user),d.pk,{'key':str(uuid.uuid4()),'version':saved['version'],'text':'مصنوعی','previous':None})
    assert receipt['case']['service_files']==[]  # دریافتِ در انتظار، هنوز پیوست فعال نیست و ارسال نمی‌شود.
    monkeypatch.setattr(files,'scan',lambda _: 'quarantined');assert files.check_one(at=row.next_check+timedelta(seconds=1));row.refresh_from_db();assert row.status=='quarantined'
    with pytest.raises(Fault):files.download(user,row.pk)
