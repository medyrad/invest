"""TEST-S03-02: independent PostgreSQL and HTTP regressions, synthetic data only."""
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event
from unittest.mock import patch

import pytest
from django.db import close_old_connections, connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.identity import otp, sessions
from apps.identity.locking import identity_transaction
from apps.identity.models import AuthSession, AuditEvent, CheckEvent, IssueEvent, LoginFlow, OTPChallenge, User

pytestmark = pytest.mark.django_db(transaction=True)
BASE = '/api/v1/auth/'


def issue(mobile='09170000001', flow=None, ip='198.51.100.11', key=None):
    token = flow or otp.new_flow()['flow_token']
    return token, otp.issue(token, mobile, key or str(uuid.uuid4()), ip)


def verify(flow, receipt, code=None, current=None):
    return otp.verify(flow, receipt['challenge_id'], code or receipt['notification']['code'], current)


def parallel(*operations):
    barrier = Barrier(len(operations))
    def run(operation):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                pid = cursor.fetchone()[0]
            barrier.wait(10)
            try:
                return pid, operation()
            except otp.Fault as error:
                return pid, error.code
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=len(operations)) as pool:
        return list(pool.map(run, operations))


@pytest.mark.parametrize('mobile', ['09170000001', '+989170000001', '00989170000001', '۰۹۱۷۰۰۰۰۰۰۱', '+٩٨٩١٧٠٠٠٠٠٠١', ' 09-170 000 001 '])
def test_allowed_formats_share_account_and_quota(mobile):
    a, r = issue(mobile)
    assert User.objects.get().mobile == '+989170000001'
    assert verify(a, r)[0]['authenticated']
    assert User.objects.get().mobile_verified_at is None


@pytest.mark.parametrize('mobile', ['09170000001\n', '09170000001X', '091700000010', '\u202e09170000001', '+' + '9'*65, None, 9170000001, '09\t170000001'])
def test_bad_inputs_have_no_number_quota(mobile):
    flow = otp.new_flow()['flow_token']
    with pytest.raises(otp.Fault, match='invalid_mobile'):
        issue(mobile, flow)
    assert not IssueEvent.objects.exists()


def test_two_flows_wrong_binding_and_account_isolation():
    a, ra = issue()
    b, rb = issue('09170000002')
    with pytest.raises(otp.Fault, match='invalid_code'):
        verify(b, ra)
    _, sa = verify(a, ra)
    _, sb = verify(b, rb)
    owner = sessions.me(sb)['user']['id']
    with pytest.raises(otp.Fault, match='forbidden'):
        sessions.operate(sa, 'private', owner)
    assert sessions.operate(sb, 'private', owner)[0]['synthetic']


def test_five_errors_correct_code_refused_and_retry_has_no_secret():
    flow, receipt = issue()
    challenge = OTPChallenge.objects.get(pk=receipt['challenge_id'])
    wrong = '000000' if receipt['notification']['code'] != '000000' else '111111'
    for _ in range(5):
        with pytest.raises(otp.Fault, match='invalid_code'):
            verify(flow, receipt, wrong)
    with pytest.raises(otp.Fault, match='challenge_exhausted'):
        verify(flow, receipt)
    replay = otp.issue(flow, '09170000001', str(challenge.operation_key), '198.51.100.11')
    assert replay['state'] == 'exhausted' and 'notification' not in replay
    assert CheckEvent.objects.count() == 5 and not AuthSession.objects.exists()


@pytest.mark.parametrize('stage', ['expired', 'replaced', 'cancelled', 'consumed', 'logout', 'revoked', 'flow_expired'])
def test_retry_terminal_states_never_revive(stage):
    flow, receipt = issue()
    challenge = OTPChallenge.objects.get(pk=receipt['challenge_id'])
    at = challenge.issued_at
    if stage == 'expired':
        at = challenge.expires_at
    elif stage == 'flow_expired':
        at = LoginFlow.objects.get().expires_at
    elif stage == 'replaced':
        with patch('apps.identity.otp.now', return_value=at + timedelta(seconds=60)):
            issue(flow=flow)
        at += timedelta(seconds=60)
    elif stage == 'cancelled':
        otp.edit(flow)
    elif stage in ('consumed', 'logout', 'revoked'):
        _, token = verify(flow, receipt)
        if stage == 'logout':
            sessions.operate(token, 'logout')
        if stage == 'revoked':
            sessions.operate(token, 'revoke-all')
    count = (IssueEvent.objects.count(), AuthSession.objects.count())
    with patch('apps.identity.otp.now', return_value=at):
        if stage == 'flow_expired':
            with pytest.raises(otp.Fault, match='flow_expired'):
                otp.issue(flow, '09170000001', str(challenge.operation_key), '198.51.100.11')
        else:
            result = otp.issue(flow, '09170000001', str(challenge.operation_key), '198.51.100.11')
            assert result['state'] == ('consumed' if stage == 'logout' else stage)
            assert 'notification' not in result
    assert count == (IssueEvent.objects.count(), AuthSession.objects.count())


def test_zero_prefix_is_real_generated_challenge_and_arabic_input():
    # Find a synthetic challenge whose real code starts with zero; do not patch code generation.
    flow = otp.new_flow()['flow_token']
    at = timezone.now()
    user = User.objects.create_user('+989170000001')
    for _ in range(500):
        candidate = OTPChallenge(id=uuid.uuid4(), flow=LoginFlow.objects.get(), user=user,
            epoch=user.auth_epoch, operation_key=uuid.uuid4(), nonce=uuid.uuid4().hex*2,
            issued_at=at, expires_at=at+timedelta(seconds=120), delivery='test')
        code = otp.code_for(candidate)
        if code.startswith('0'):
            candidate.code_digest = otp.digest(f'check:{candidate.id}:{code}')
            candidate.save()
            break
    else:
        pytest.fail('No leading-zero synthetic challenge found')
    arabic = code.translate(str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩'))
    assert otp.verify(flow, str(candidate.pk), arabic)[0]['authenticated']


def test_parallel_capacity_and_consumption_real_connections():
    for i in range(9):
        issue(ip=f'198.51.100.{i+1}')
    results = parallel(lambda: issue(), lambda: issue())
    assert len({r[0] for r in results}) == 2
    assert sum(isinstance(r[1], tuple) for r in results) == 1
    assert sum(r[1] == 'rate_limited' for r in results) == 1
    assert IssueEvent.objects.count() == 10
    flow, receipt = next(r[1] for r in results if isinstance(r[1], tuple))
    results = parallel(lambda: verify(flow, receipt), lambda: verify(flow, receipt))
    assert len({r[0] for r in results}) == 2
    assert sum(isinstance(r[1], tuple) for r in results) == 1
    assert AuthSession.objects.count() == 1


def test_quota_boundaries_and_rejections_do_not_extend():
    at = timezone.now()
    with patch('apps.identity.otp.now', return_value=at):
        flow, receipt = issue()
    for delta in (1, 30, 59):
        with patch('apps.identity.otp.now', return_value=at+timedelta(seconds=delta)):
            with pytest.raises(otp.Fault) as error:
                issue(flow=flow)
            assert error.value.retry_after == 60-delta
    with patch('apps.identity.otp.now', return_value=at+timedelta(seconds=60)):
        issue(flow=flow)
    assert IssueEvent.objects.count() == 2


def test_check_throttle_rejected_attempt_not_extending_and_exact_exit():
    flow, receipt = issue()
    user = User.objects.get()
    at = timezone.now()
    CheckEvent.objects.bulk_create([CheckEvent(user=user, failed=True, at=at-timedelta(seconds=899)) for _ in range(10)])
    CheckEvent.objects.create(user=user, failed=False, at=at)
    with patch('apps.identity.otp.now', return_value=at):
        with pytest.raises(otp.Fault) as error:
            verify(flow, receipt)
        assert error.value.retry_after == 1
    assert CheckEvent.objects.count() == 11
    with patch('apps.identity.otp.now', return_value=at+timedelta(seconds=1)):
        assert verify(flow, receipt)[0]['authenticated']


def test_revocation_wins_against_waiting_verify_and_role_wins_sensitive():
    flow, receipt = issue()
    _, token = verify(flow, receipt)
    second, second_receipt = issue()
    entered = Event()
    def waiting_verify():
        close_old_connections()
        entered.set()
        try:
            return verify(second, second_receipt)
        except otp.Fault as error:
            return error.code
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with identity_transaction():
            future = pool.submit(waiting_verify)
            assert entered.wait(5)
            sessions.operate(token, 'revoke-all')
        assert future.result(10) == 'challenge_revoked'
    user = User.objects.get()
    sessions.change_authority(user.pk, role='expert')
    user.refresh_from_db()
    with identity_transaction():
        _, sensitive = sessions.mint_session(user, timezone.now(), sensitive=True, assurance='real')
    entered.clear()
    def waiting_sensitive():
        close_old_connections()
        entered.set()
        try:
            return sessions.operate(sensitive, 'sensitive')
        except otp.Fault as error:
            return error.code
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with identity_transaction():
            future = pool.submit(waiting_sensitive)
            assert entered.wait(5)
            sessions.change_authority(user.pk, role='user')
        assert future.result(10) == 'forbidden'
    assert not AuditEvent.objects.filter(kind='synthetic_sensitive_action').exists()


def test_http_csrf_forgery_and_no_secret_in_errors_audit(settings, caplog):
    api = APIClient(enforce_csrf_checks=True)
    assert api.post(BASE+'flows', {}, format='json').status_code == 403
    csrf = api.get(BASE+'csrf').json()['csrfToken']
    headers = {'HTTP_X_CSRFTOKEN': csrf}
    flow = api.post(BASE+'flows', {}, format='json', **headers).json()['flow_token']
    headers['HTTP_X_LOGIN_FLOW'] = flow
    r = api.post(BASE+'issue', {'mobile':'09170000001','key':str(uuid.uuid4())}, format='json', **headers)
    receipt = r.json()
    assert 'no-store' in r['Cache-Control']
    assert api.post(BASE+'verify', {'challenge_id':receipt['challenge_id'], 'code':receipt['notification']['code']}, format='json', **headers).status_code == 200
    old = api.cookies['invest_session'].value
    csrf = api.get(BASE+'csrf').json()['csrfToken']
    headers['HTTP_X_CSRFTOKEN'] = csrf
    assert api.post(BASE+'activity', {}, format='json').status_code == 403
    for field in ('role','assurance','sensitive','owner'):
        r = api.post(BASE+'activity', {field:'admin'}, format='json', **headers)
        assert r.status_code == 400
    assert api.post(BASE+'sensitive', {}, format='json', **headers).status_code == 403
    assert api.post(BASE+'logout', {}, format='json', **headers).status_code == 200
    api.cookies['invest_session'] = old
    assert api.get(BASE+'me').json()['authenticated'] is False
    combined = str(list(AuditEvent.objects.values())) + caplog.text + str(r.json())
    for secret in (flow, receipt['notification']['code'], old, '09170000001'):
        assert secret not in combined
    settings.INVEST_ENV='public'
    settings.OTP_DELIVERY_MODE='sms'
    r = api.post(BASE+'issue', {'mobile':'09170000001','key':str(uuid.uuid4())}, format='json', **headers)
    assert 'notification' not in str(r.json())


def test_idle_natural_read_does_not_refresh_but_explicit_activity_does():
    flow, receipt = issue()
    _, token = verify(flow, receipt)
    record = AuthSession.objects.get()
    initial = record.last_activity
    owner = str(record.user_id)
    with patch('apps.identity.otp.now', return_value=initial+timedelta(hours=23)):
        assert sessions.me(token)['authenticated']
        assert sessions.operate(token, 'private', owner)[0]['synthetic']
        record.refresh_from_db()
        assert record.last_activity == initial
        sessions.operate(token, 'activity')
        record.refresh_from_db()
        assert record.last_activity == initial+timedelta(hours=23)
    with patch('apps.identity.otp.now', return_value=record.created_at+timedelta(days=7)):
        assert not sessions.me(token)['authenticated']


def test_http_polling_prefetch_health_and_client_activity_claim_do_not_refresh_idle():
    flow, receipt = issue()
    _, token = verify(flow, receipt)
    record = AuthSession.objects.get()
    initial = record.last_activity
    client = APIClient(enforce_csrf_checks=True)
    client.cookies['invest_session'] = token
    for second in (60, 3600, 43200, 86399):
        with patch('apps.identity.otp.now', return_value=initial+timedelta(seconds=second)):
            assert client.get(BASE+'me').json()['authenticated']
            assert client.get(BASE+'me?user_active=true', HTTP_SEC_PURPOSE='prefetch', HTTP_PURPOSE='prefetch').json()['authenticated']
            assert client.get('/api/v1/health/live').status_code == 200
        record.refresh_from_db()
        assert record.last_activity == initial
    with patch('apps.identity.otp.now', return_value=initial+timedelta(seconds=86400)):
        assert client.get(BASE+'me').json()['authenticated'] is False
