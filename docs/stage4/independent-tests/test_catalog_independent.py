"""Independent destructive tests: isolated pytest PostgreSQL database only."""
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError,transaction
from rest_framework.test import APIClient
from apps.catalog.models import Group,Subtype,Province,County,City

pytestmark=pytest.mark.django_db(transaction=True)
MODELS=(Group,Subtype,Province,County,City)
EXPECTED=json.loads(Path('/evidence/source-expected.json').read_text())

def snapshot():return [list(m.objects.order_by('pk').values()) for m in MODELS]

def test_every_api_identity_name_and_parent_matches_zip():
 call_command('import_reference')
 api=APIClient()
 assert api.get('/api/v1/catalog/taxonomy').json()['groups']==EXPECTED['groups']
 geo=api.get('/api/v1/catalog/geography').json()
 assert geo['provinces']==EXPECTED['provinces']
 assert geo['city_coverage']=='source-linked-only'
 for g in EXPECTED['groups']:
  for s in g['subtypes']:
   row=Subtype.objects.get(pk=g['id']+'.'+s['id']);assert row.name==s['name'] and row.group_id==g['id'] and row.raw_id==s['id']
 for p in EXPECTED['provinces']:
  for c in p['counties']:
   assert County.objects.get(pk=c['id']).province_id==p['id']
   for city in c['cities']:assert City.objects.get(pk=city['id']).county_id==c['id']
 assert [m.objects.count() for m in MODELS]==[11,78,31,478,22]

def test_repeat_preserves_all_independent_rows_and_metadata():
 Group.objects.create(id='independent',name='مصنوعی مستقل',source_version='custom',metadata={'unchanged':True},position=99)
 Province.objects.create(id='custom-province',name='استان مصنوعی',source_version='custom')
 County.objects.create(id='custom-county',name='شهرستان مصنوعی',source_version='custom',province_id='custom-province')
 City.objects.create(id='custom-city',name='شهر مصنوعی',source_version='custom',county_id='custom-county')
 call_command('import_reference');before=snapshot();call_command('import_reference');assert snapshot()==before

def test_late_id_conflict_rolls_back_entire_import():
 Province.objects.create(id='province-30',name='تعارض مصنوعی',source_version='custom')
 before=snapshot()
 with pytest.raises(CommandError):call_command('import_reference')
 assert snapshot()==before

def test_error_after_writes_rolls_back_all_models():
 Group.objects.create(id='keep',name='مستقل',source_version='custom')
 before=snapshot();original=County.save;count=0
 def fail_midway(self,*args,**kwargs):
  nonlocal count
  count+=1
  if count==200:raise RuntimeError('Synthetic mid-import failure')
  return original(self,*args,**kwargs)
 with patch.object(County,'save',fail_midway),pytest.raises(RuntimeError):call_command('import_reference')
 assert count==200 and snapshot()==before

@pytest.mark.parametrize('kind',['county-parent','city-parent','duplicate-county','duplicate-city','duplicate-subtype'])
def test_real_fk_and_uniqueness(kind):
 call_command('import_reference')
 with pytest.raises(IntegrityError),transaction.atomic():
  if kind=='county-parent':County.objects.create(id='bad',name='bad',source_version='custom',province_id='missing')
  elif kind=='city-parent':City.objects.create(id='bad',name='bad',source_version='custom',county_id='missing')
  elif kind=='duplicate-county':
   c=County.objects.first();County.objects.create(id='duplicate',name=c.name,source_version='custom',province_id=c.province_id)
  elif kind=='duplicate-city':
   c=City.objects.first();City.objects.create(id='duplicate',name=c.name,source_version='custom',county_id=c.county_id)
  else:
   s=Subtype.objects.first();Subtype.objects.create(id='duplicate',name='duplicate',source_version='custom',group_id=s.group_id,raw_id=s.raw_id)

def test_public_api_and_every_preview_value_has_no_phone(settings):
 api=APIClient();data=api.get('/api/v1/catalog/preview').json();assert data['enabled'] and len(data['listings'])==273
 def scan(value):
  if isinstance(value,dict):
   for key,v in value.items():assert key.lower() not in ('phone','mobile','telephone','contactphone');scan(v)
  elif isinstance(value,list):
   for v in value:scan(v)
 scan(data)
 settings.INVEST_ENV='public'
 public=api.get('/api/v1/catalog/preview');assert public.status_code==200 and public.json()['enabled'] is False and public.json()['listings']==[]
