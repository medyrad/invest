import json
import pytest
from django.db import connection
from rest_framework.test import APIClient

pytestmark=pytest.mark.django_db
@pytest.mark.parametrize('important',[[{}],[[]],[1],[True]])
def test_malformed_important_never_returns_internal_error(important):
    assert connection.vendor=='postgresql' and connection.settings_dict['NAME'].startswith('test_')
    response=APIClient().get('/api/v1/core/opportunities',{'criteria':json.dumps({'important':important})})
    assert response.status_code==400,response.data

@pytest.mark.parametrize('kind,key,route',[('project','min_capital','investor'),('fund','minimum_investment','fund'),('sale','price','buyer')])
def test_independent_sixty_weight_fraction_for_each_kind(kind,key,route):
    from decimal import Decimal
    from types import SimpleNamespace
    from apps.core.discovery import score
    snapshot={key:{'status':'known','value':'10'},'budget':{'status':'known','value':'999999'},'risk':'high','price_mode':'total'}
    result=score(SimpleNamespace(kind=kind,snapshot=snapshot),{'route':route,'budget_max':'20','province':['test-place'],'risk':['low'],'important':['location','risk']})
    # amount met=30; location unknown=15; risk unmet=15. W=60, E=30, K=45.
    assert Decimal(result['score'])==50 and Decimal(result['coverage'])==75
    assert len(result['warnings'])==2

def test_operator_has_active_work_period_contract():
    from apps.workspace.schema import FIELDS,active_keys
    active=active_keys(['operator'],False,{})
    periods=[k for k in active if FIELDS[k].get('unit') in ['DAY','MONTH','YEAR']]
    assert periods, 'F09 requires a work period; operator has no active time quantity'
