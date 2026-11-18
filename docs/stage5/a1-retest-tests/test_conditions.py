import pytest
from django.db import connection
from tests.conftest import accounts
from tests.test_workspace import create,save,number
from apps.workspace import service

pytestmark=pytest.mark.django_db
@pytest.fixture(autouse=True)
def isolated():
    assert connection.vendor=='postgresql' and connection.settings_dict['NAME'].startswith('test_')

@pytest.mark.parametrize('route,key,unit',[
 ('investor','min_capital','BILLION_TOMAN'),('contractor','working_capital_min','BILLION_TOMAN'),
 ('buyer','purchase_price','BILLION_TOMAN'),('lessee','deposit','BILLION_TOMAN'),
 ('heritage','min_capital','BILLION_TOMAN')])
def test_route_restore_and_inactive_injection(accounts,route,key,unit):
    a=accounts[0];d=create(a);value=number(key,'0',unit)
    d=save(a,d,{key:value},[route]);assert d['effective'][key]['value']=='0'
    d=save(a,d,{key:number(key,'999',unit)},[])
    assert key not in d['effective'] and d['raw'][key]==value and key not in d['missing']
    d=save(a,d,{},[route]);assert d['effective'][key]['value']=='0'


def test_model_id_readiness_matches_product_table(accounts):
    d=create(accounts[0]);assert 'model_id' in d['missing']
