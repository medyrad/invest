"""Actual overlapping PostgreSQL connections; no SQLite or lock mocks."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event
from unittest.mock import patch

import pytest
from django.db import close_old_connections
from django.utils import timezone

from apps.identity import otp, sessions
from apps.identity.locking import identity_transaction
from apps.identity.models import AuditEvent, AuthSession, IssueEvent, OTPChallenge, User
from tests.test_identity import issue, verify

pytestmark = pytest.mark.django_db(transaction=True)


def parallel(*operations):
    gate = Barrier(len(operations))

    def run(operation):
        close_old_connections()
        gate.wait(timeout=5)
        try:
            return operation()
        except otp.Fault as exc:
            return exc.code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=len(operations)) as pool:
        return list(pool.map(run, operations))


def test_parallel_consumption_creates_exactly_one_session():
    token, result = issue()
    results = parallel(lambda: verify(token, result), lambda: verify(token, result))
    assert sum(isinstance(r, tuple) for r in results) == 1
    assert "recovery_required" in results
    assert AuthSession.objects.count() == 1


def test_parallel_first_login_has_one_account_two_sessions():
    a, b = otp.new_flow()["flow_token"], otp.new_flow()["flow_token"]
    results = parallel(lambda: issue(flow=a), lambda: issue(flow=b))
    assert User.objects.count() == 1
    verified = parallel(*(lambda pair=pair: verify(*pair) for pair in results))
    assert all(isinstance(r, tuple) for r in verified)
    assert AuthSession.objects.count() == 2


def test_parallel_last_phone_quota_and_same_idempotency_key():
    import uuid

    for _ in range(9):
        issue()
    result = parallel(lambda: issue(), lambda: issue())
    assert sum(isinstance(r, tuple) for r in result) == 1
    assert "rate_limited" in result and IssueEvent.objects.count() == 10
    flow = otp.new_flow()["flow_token"]
    key = str(uuid.uuid4())
    result = parallel(
        lambda: issue("09123456788", flow, key), lambda: issue("09123456788", flow, key)
    )
    assert result[0] == result[1]
    assert OTPChallenge.objects.filter(flow__digest=otp.digest(flow)).count() == 1


def test_revocation_committed_first_blocks_waiting_verify():
    a, ra = issue()
    _, session = verify(a, ra)
    b, rb = issue()
    entered = Event()

    def waiter():
        close_old_connections()
        entered.set()
        try:
            return verify(b, rb)
        except otp.Fault as exc:
            return exc.code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with identity_transaction():
            pending = pool.submit(waiter)
            assert entered.wait(5)
            sessions.operate(session, "revoke-all")
        assert pending.result(timeout=10) == "challenge_revoked"
    assert AuthSession.objects.count() == 1


def test_clock_sampled_after_lock_wait():
    a, ra = issue()
    challenge = OTPChallenge.objects.get(pk=ra["challenge_id"])
    locked = Event()

    def waiter():
        close_old_connections()
        locked.set()
        try:
            return verify(a, ra)
        except otp.Fault as exc:
            return exc.code
        finally:
            close_old_connections()

    with patch(
        "apps.identity.otp.now", return_value=challenge.expires_at - timedelta(seconds=1)
    ) as clock:
        with ThreadPoolExecutor(max_workers=1) as pool:
            with identity_transaction():
                pending = pool.submit(waiter)
                assert locked.wait(5)
                clock.return_value = challenge.expires_at
            assert pending.result(timeout=10) == "challenge_expired"


def test_role_revoked_first_blocks_sensitive_action():
    user = User.objects.create_user("+989123456789", role="expert")
    with identity_transaction():
        _, token = sessions.mint_session(user, timezone.now(), sensitive=True, assurance="real")
    entered = Event()

    def waiter():
        close_old_connections()
        entered.set()
        try:
            return sessions.operate(token, "sensitive")
        except otp.Fault as exc:
            return exc.code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with identity_transaction():
            pending = pool.submit(waiter)
            assert entered.wait(5)
            sessions.change_authority(user.pk, role="user")
        assert pending.result(timeout=10) == "forbidden"
    assert not AuditEvent.objects.filter(kind="synthetic_sensitive_action").exists()


def test_resend_consumption_both_serial_orders():
    a, ra = issue()
    at = OTPChallenge.objects.get(pk=ra["challenge_id"]).issued_at
    with patch("apps.identity.otp.now", return_value=at + timedelta(seconds=60)):
        result = parallel(lambda: issue(flow=a), lambda: verify(a, ra))
    if isinstance(result[0], tuple):
        assert result[1] == "challenge_replaced"
    else:
        assert result[0] == "flow_completed" and isinstance(result[1], tuple)
    # Explicit reverse order evidence, independent of scheduler order.
    b, rb = issue("09123456788")
    at = OTPChallenge.objects.get(pk=rb["challenge_id"]).issued_at
    with patch("apps.identity.otp.now", return_value=at + timedelta(seconds=60)):
        issue("09123456788", flow=b)
        with pytest.raises(otp.Fault, match="challenge_replaced"):
            verify(b, rb)


def test_parallel_intent_recovery_returns_same_idempotent_handoff():
    flow = otp.new_flow()["flow_token"]
    otp.intent(flow, "set", {"destination": "/saved", "snapshot": {"id": "synthetic"}})
    _, result = issue(flow=flow)
    _, token = verify(flow, result)
    results = parallel(
        lambda: otp.intent(flow, "consume", session_token=token),
        lambda: otp.intent(flow, "consume", session_token=token),
    )
    assert all(isinstance(r, dict) for r in results)
    assert results[0]["handoff"] == results[1]["handoff"]
