"""TEST-EXPERIENCE-COMPLETE-01: expectations from AC-PC and D29, not product output."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from django.core.management import call_command
from django.db import close_old_connections
from rest_framework.test import APIClient

from tests.test_core import team, current_core_definitions, publish, key
from apps.core import personal
from apps.core.models import Report, Search, Case
from apps.catalog.models import Subtype
from apps.identity.sessions import mint_session
from apps.services import advisories
from apps.workspace.schema import Fault
from django.utils import timezone

pytestmark = pytest.mark.django_db

def make_report(team, subtype, answers):
    call_command('import_reference', verbosity=0)
    st = Subtype.objects.get(raw_id=subtype)
    _, op = publish(team, values={'group':st.group_id, 'subtype':st.pk})
    data={'key':key(),'action':'report','id':str(op.pk),'value':{'criteria':{'route':'investor'},'guide_context':{'answers':answers,'kind':'visit','checked':['pre-0'],'advisory_version':1}}}
    receipt=personal.mutate(team[2].user,data)
    return Report.objects.get(pk=receipt['report_id']),op

@pytest.mark.parametrize('subtype,answers,inactive,active',[
    ('roads',{'revenue':'public','toll':'notallowed','buyer':'documented'},'toll','buyer'),
    ('roads',{'revenue':'user','toll':'allowed','buyer':'unknown'},'buyer','toll'),
    ('residential',{'revenue':'rent','presale':'yes'},'presale','revenue'),
])
def test_inactive_answer_never_rendered(team,subtype,answers,inactive,active):
    report,_=make_report(team,subtype,answers)
    effective=report.snapshot['effective_advisory']['effective_answers']
    assert inactive not in effective and active in effective
    Path('/evidence/'+subtype+'-'+answers['revenue']+'.html').write_text(report.snapshot['rendered_html'])
    assert f'<dt>{inactive}</dt>' not in report.snapshot['rendered_html'], 'Inactive raw answer is rendered as effective'

@pytest.mark.parametrize('value',['yes','no'])
def test_residential_presale_active(team,value):
    report,_=make_report(team,'residential',{'revenue':'sale','presale':value})
    assert report.snapshot['effective_advisory']['effective_answers']['presale']==value

def test_report_labels_and_followup_are_human_readable(team):
    report,_=make_report(team,'roads',{'revenue':'public','buyer':'documented'})
    body=report.snapshot['rendered_html']
    assert '<dt>buyer</dt>' not in body, 'Raw English question ID, not Persian label'
    assert 'pre-0' not in body, 'Raw checkbox ID, not checklist wording'

def client_for(user):
    _,token=mint_session(user,timezone.now())
    client=APIClient()
    client.cookies['invest_session']=token
    return client

def test_history_other_session_injection_isolation_no_case(team):
    report,op=make_report(team,'roads',{'revenue':'public','buyer':'documented'})
    client=client_for(team[2].user)
    url=f'/api/v1/core/reports/{report.pk}'
    first=client.get(url)
    assert first.status_code==200
    assert first['Content-Type'].startswith('text/html')
    assert 'sandbox' in first['Content-Security-Policy']
    op.availability='owner_paused';op.save()
    assert client_for(team[2].user).get(url).content==first.content
    assert client_for(team[3].user).get(url).status_code==404
    assert APIClient().get(url).status_code in (401,403)  # AC requires denial, not a particular code.
    assert Case.objects.count()==0
    data={'key':key(),'action':'report','id':str(op.pk),'value':{'criteria':{},'guide_context':{'mine':[['نام','<script>alert(1)</script>']]}}}
    receipt=personal.mutate(team[2].user,data)
    body=client.get('/api/v1/core/reports/'+receipt['report_id']).content.decode()
    assert '<script>alert' not in body and '&lt;script&gt;' in body

def test_legacy_report_is_readable_html(team):
    report,_=make_report(team,'roads',{'revenue':'public'})
    snapshot={k:v for k,v in report.snapshot.items() if k!='rendered_html'}
    legacy=Report.objects.create(user=team[2].user,snapshot=snapshot)
    response=client_for(team[2].user).get('/api/v1/core/reports/'+str(legacy.pk))
    assert response.status_code==200
    assert response['Content-Type'].startswith('text/html'), 'AC-PC05 disallows raw JSON; legacy is not approved exclusion'

@pytest.mark.parametrize('invalid',[{'route':'bad'},{'important':[{}]}])
def test_search_validation_atomic_owner(team,invalid):
    u=team[2].user
    personal.mutate(u,{'key':key(),'action':'search','id':None,'value':{'name':'قبلی','criteria':{}}})
    search=Search.objects.get(user=u)
    data={'key':key(),'action':'search_update','id':str(search.pk),'value':{'name':'جدید','criteria':invalid}}
    with pytest.raises(Fault):personal.mutate(u,data)
    search.refresh_from_db();assert search.name=='قبلی'
    data['value']['criteria']={}
    with pytest.raises(Fault):personal.mutate(team[3].user,data)
    search.refresh_from_db();assert search.name=='قبلی'

@pytest.mark.django_db(transaction=True)
def test_concurrent_search_same_key_once(team):
    user=team[2].user
    data={'key':key(),'action':'search','id':None,'value':{'name':'هم‌زمان','criteria':{'route':'investor'}}}
    barrier=Barrier(2)
    def run():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return personal.mutate(user,data)
        finally:close_old_connections()
    with ThreadPoolExecutor(2) as pool:
        futures=[pool.submit(run) for _ in range(2)]
        results=[x.result(timeout=30) for x in futures]
    assert results[0]==results[1]
    assert Search.objects.filter(user=user).count()==1

def test_profile_two_sessions_roles_not_authority(team):
    u=team[2].user
    value={'professional':json.dumps({'roles':['investor','contractor'],'name':'آزمون','capital':'0','entity':'individual','validity':'unknown'})}
    data={'key':key(),'action':'profile','id':None,'value':value}
    personal.mutate(u,data)
    personal.mutate(u,data)
    for _ in range(2):
        result=client_for(u).get('/api/v1/core/personal')
        assert result.status_code==200 and result.json()['profile']==value
    u.refresh_from_db();assert u.role=='user'
    assert client_for(team[3].user).get('/api/v1/core/personal').json()['profile']=={}
