"""PROGRAMMER-S03-01: executable contract and time-boundary specifications."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.identity import otp
from apps.identity.models import AuthSession, OTPChallenge, User

pytestmark = pytest.mark.django_db(transaction=True)


def test_canonical_contract():
    for value in (
        "09123456789",
        "+989123456789",
        "00989123456789",
        "۰۹۱۲۳۴۵۶۷۸۹",
        "٠٩١٢٣٤٥٦٧٨٩",
        " 0912-345 6789 ",
    ):
        assert otp.canonical_mobile(value) == "+989123456789"
    for value in (
        "09123456789\n",
        "a09123456789",
        "09123456789\u202e",
        "0" * 100,
        "+12025550101",
        "091234567890",
    ):
        with pytest.raises(otp.Fault):
            otp.canonical_mobile(value)


def issue(mobile="09123456789", flow=None, key=None, ip="127.0.0.1"):
    import uuid

    token = flow or otp.new_flow()["flow_token"]
    result = otp.issue(token, mobile, key or str(uuid.uuid4()), ip)
    return token, result


def verify(token, result, code=None, current=None):
    return otp.verify(
        token, result["challenge_id"], code or result["notification"]["code"], current
    )


def test_consumption_and_replay():
    token, result = issue()
    data, secret = verify(token, result)
    assert data["authenticated"] and secret
    assert AuthSession.objects.count() == 1
    with pytest.raises(otp.Fault, match="recovery_required"):
        verify(token, result)
    assert verify(token, result, current=secret)[0]["recovered"]
    assert AuthSession.objects.count() == 1
    assert User.objects.get().mobile_verified_at is None


def test_expiry_and_five_errors():
    token, result = issue()
    challenge = OTPChallenge.objects.get(pk=result["challenge_id"])
    with patch("apps.identity.otp.now", return_value=challenge.expires_at):
        with pytest.raises(otp.Fault, match="challenge_expired"):
            verify(token, result)
    for _ in range(5):
        with pytest.raises(otp.Fault):
            verify(token, result, "xxxxxx")
    with pytest.raises(otp.Fault, match="challenge_exhausted"):
        verify(token, result)


def test_retry_current_state_and_payload():
    import uuid

    key = str(uuid.uuid4())
    token, result = issue(key=key)
    again = otp.issue(token, "+989123456789", key, "127.0.0.1")
    assert again == result
    with pytest.raises(otp.Fault, match="payload_conflict"):
        otp.issue(token, "09123456788", key, "127.0.0.1")
    verify(token, result)
    again = otp.issue(token, "09123456789", key, "127.0.0.1")
    assert again["state"] == "consumed" and "notification" not in again
    with patch("apps.identity.otp.now", return_value=timezone.now() + timedelta(minutes=31)):
        with pytest.raises(otp.Fault, match="flow_expired"):
            otp.issue(token, "09123456789", key, "127.0.0.1")


def test_binding_edit_and_independent_devices():
    a, ra = issue()
    b, rb = issue()
    with pytest.raises(otp.Fault, match="invalid_code"):
        otp.verify(b, ra["challenge_id"], ra["notification"]["code"])
    otp.edit(a)
    with pytest.raises(otp.Fault, match="challenge_cancelled"):
        verify(a, ra)
    assert verify(b, rb)[0]["authenticated"]
    assert User.objects.count() == 1


def test_flow_spacing_and_sliding_boundaries():
    import uuid

    token, result = issue()
    at = OTPChallenge.objects.get(pk=result["challenge_id"]).issued_at
    for second in (1, 59):
        with patch("apps.identity.otp.now", return_value=at + timedelta(seconds=second)):
            with pytest.raises(otp.Fault) as exc:
                issue(flow=token)
            assert exc.value.retry_after == 60 - second
    for second in (60, 120):
        with patch("apps.identity.otp.now", return_value=at + timedelta(seconds=second)):
            issue(flow=token)
    with patch("apps.identity.otp.now", return_value=at + timedelta(seconds=180)):
        with pytest.raises(otp.Fault) as exc:
            issue(flow=token)
        assert exc.value.retry_after == 720
    with patch("apps.identity.otp.now", return_value=at + timedelta(seconds=900)):
        assert otp.issue(token, "09123456789", str(uuid.uuid4()), "127.0.0.1")["state"] == "active"


def test_phone_daily_cap_and_rejected_does_not_extend():
    start = timezone.now()
    for index in range(10):
        with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=index)):
            issue()
    for seconds in (10, 901, 86399):
        with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=seconds)):
            with pytest.raises(otp.Fault) as exc:
                issue()
            assert exc.value.retry_after == 86400 - seconds
    with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=86400)):
        issue()


def test_ip_only_limits_new_issuance():
    for i in range(30):
        token, result = issue(mobile=f"0912{i:07d}")
    with pytest.raises(otp.Fault, match="rate_limited"):
        issue(mobile="09129999999")
    assert verify(token, result)[0]["authenticated"]


def test_error_throttle_shared_and_sliding_exit():
    from apps.identity.models import CheckEvent

    a, ra = issue()
    b, rb = issue()
    c, rc = issue()
    start = timezone.now()
    with patch("apps.identity.otp.now", return_value=start):
        for token, result in ((a, ra), (b, rb)):
            for _ in range(5):
                with pytest.raises(otp.Fault):
                    verify(token, result, "bad")
        assert CheckEvent.objects.filter(failed=True).count() == 10
    for second in (1, 29):
        with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=second)):
            with pytest.raises(otp.Fault) as exc:
                verify(c, rc)
            assert exc.value.retry_after == 30 - second
            assert CheckEvent.objects.count() == 10
    with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=30)):
        assert verify(c, rc)[0]["authenticated"]


def test_throttle_ends_when_errors_leave_window():
    from apps.identity.models import CheckEvent

    token, result = issue()
    user = User.objects.get()
    at = timezone.now()
    CheckEvent.objects.bulk_create(
        [CheckEvent(user=user, failed=True, at=at - timedelta(seconds=899)) for _ in range(10)]
    )
    CheckEvent.objects.create(user=user, failed=False, at=at)
    with patch("apps.identity.otp.now", return_value=at):
        with pytest.raises(otp.Fault) as exc:
            verify(token, result)
        assert exc.value.retry_after == 1
    with patch("apps.identity.otp.now", return_value=at + timedelta(seconds=1)):
        assert verify(token, result)[0]["authenticated"]


def test_provider_failure_unknown_and_public_no_disclosure(settings):
    from apps.identity.models import IssueEvent

    with patch("apps.identity.otp.delivery_adapter", side_effect=TimeoutError):
        token, result = issue()
    assert result["delivery"] == "unknown" and "notification" not in result
    challenge = OTPChallenge.objects.get(pk=result["challenge_id"])
    with patch("apps.identity.otp.delivery_adapter") as adapter:
        again = otp.issue(token, "09123456789", str(challenge.operation_key), "127.0.0.1")
        adapter.assert_not_called()
    assert again == result and IssueEvent.objects.count() == 1
    settings.OTP_DELIVERY_MODE = "sms"
    _, failed = issue(mobile="09123456788")
    assert failed["delivery"] == "failed"
    settings.INVEST_ENV = "public"
    settings.OTP_DELIVERY_MODE = "notification"
    _, public = issue(mobile="09123456787")
    assert public["delivery"] == "failed" and "notification" not in public


def test_zero_prefix_and_strict_otp():
    with patch("apps.identity.otp.code_for", return_value="000123"):
        token, result = issue()
        assert verify(token, result, "۰۰۰۱۲۳")[0]["authenticated"]
    for value in ("000123\n", "0001234", 123, "00012\u202e", "000 123"):
        with pytest.raises(otp.Fault):
            otp.normalized_code(value)


def test_sessions_logout_revoke_deactivate_and_role_changes():
    from apps.identity import sessions

    a, ra = issue()
    b, rb = issue()
    _, sa = verify(a, ra)
    _, sb = verify(b, rb)
    sessions.operate(sa, "logout")
    assert not sessions.me(sa)["authenticated"] and sessions.me(sb)["authenticated"]
    with pytest.raises(otp.Fault, match="recovery_required"):
        verify(a, ra, current=sa)
    c, rc = issue()
    sessions.operate(sb, "revoke-all")
    assert not sessions.me(sb)["authenticated"]
    with pytest.raises(otp.Fault, match="challenge_revoked"):
        verify(c, rc)
    d, rd = issue()
    user = User.objects.get()
    sessions.change_authority(user.pk, active=False)
    sessions.change_authority(user.pk, active=True)
    with pytest.raises(otp.Fault, match="challenge_revoked"):
        verify(d, rd)
    e, re = issue()
    _, se = verify(e, re)
    sessions.change_authority(user.pk, role="expert")
    assert not sessions.me(se)["authenticated"]


@pytest.mark.parametrize("sensitive,idle,absolute", [(False, 86400, 604800), (True, 1800, 43200)])
def test_idle_absolute_rotation_and_activity(sensitive, idle, absolute):
    from apps.identity import sessions

    user = User.objects.create_user("+989123456789")
    start = timezone.now()
    with sessions.identity_transaction():
        record, token = sessions.mint_session(user, start, sensitive=sensitive)
    with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=idle - 1)):
        assert sessions.me(token)["authenticated"]
        record.refresh_from_db()
        assert record.last_activity == start
        _, rotated = sessions.operate(token, "rotate")
        assert not sessions.me(token)["authenticated"]
        sessions.operate(rotated, "activity")
    with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=absolute)):
        assert not sessions.me(rotated)["authenticated"]
    record.last_activity = start
    record.save()
    with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=idle)):
        assert not sessions.me(rotated)["authenticated"]


def test_two_accounts_and_sensitive_gate():
    from apps.identity import sessions

    a, ra = issue()
    b, rb = issue("09123456788")
    _, sa = verify(a, ra)
    _, sb = verify(b, rb)
    owner = sessions.me(sb)["user"]["id"]
    with pytest.raises(otp.Fault, match="forbidden"):
        sessions.operate(sa, "private", owner)
    assert sessions.operate(sb, "private", owner)[0]["synthetic"]
    with pytest.raises(otp.Fault, match="forbidden"):
        sessions.operate(sa, "sensitive")


def test_reauth_is_session_bound_and_cannot_refresh_real_assurance():
    from apps.identity import sessions

    user = User.objects.create_user("+989123456789", role="expert")
    start = timezone.now()
    with sessions.identity_transaction():
        record, token = sessions.mint_session(user, start, sensitive=True, assurance="real")
    with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=299)):
        assert sessions.operate(token, "sensitive")[0]["ok"]
    with patch("apps.identity.otp.now", return_value=start + timedelta(seconds=300)):
        with pytest.raises(otp.Fault):
            sessions.operate(token, "sensitive")
    flow, challenge = issue()
    otp.verify(
        flow, challenge["challenge_id"], challenge["notification"]["code"], token, reauth=True
    )
    record.refresh_from_db()
    assert record.created_at == start and record.assurance == "test"
    with pytest.raises(otp.Fault):
        sessions.operate(token, "sensitive")
    another, result = issue("09123456788")
    with pytest.raises(otp.Fault, match="forbidden"):
        otp.verify(
            another, result["challenge_id"], result["notification"]["code"], token, reauth=True
        )


def test_intent_snapshot_replacement_expiry_cancel_and_owner():
    from apps.identity import sessions

    flow = otp.new_flow()["flow_token"]
    payload = {"destination": "/saved", "snapshot": {"listing": "synthetic-1"}}
    otp.intent(flow, "set", payload)
    token, result = issue(flow=flow)
    _, session = verify(token, result)
    payload["snapshot"]["listing"] = "changed"
    handoff = otp.intent(flow, "consume", session_token=session)
    assert handoff["handoff"]["snapshot"]["listing"] == "synthetic-1"
    assert handoff["persisted"] is False
    replay = otp.intent(flow, "consume", session_token=session)
    assert replay == handoff  # network recovery reuses the same immutable operation key
    otp.intent(flow, "set", payload, session)
    otp.intent(flow, "cancel")
    with pytest.raises(otp.Fault):
        otp.intent(flow, "consume", session_token=session)
    otp.intent(flow, "set", payload, session)
    with patch("apps.identity.otp.now", return_value=timezone.now() + timedelta(minutes=10)):
        with pytest.raises(otp.Fault):
            otp.intent(flow, "consume", session_token=session)
    b, rb = issue("09123456788")
    _, sb = verify(b, rb)
    with pytest.raises(otp.Fault):
        otp.intent(flow, "consume", session_token=sb)
    with pytest.raises(otp.Fault):
        otp.intent(flow, "set", {"destination": "https://evil.example", "snapshot": {}})
    assert sessions.me(session)["authenticated"]


def test_api_csrf_payload_cookie_ip_and_logs(client, caplog):
    import uuid

    from apps.identity.models import AuditEvent, IssueEvent

    base = "/api/v1/auth/"
    assert client.post(base + "flows", {}, format="json").status_code == 403
    csrf = client.get(base + "csrf").json()["csrfToken"]
    headers = {"HTTP_X_CSRFTOKEN": csrf}
    flow = client.post(base + "flows", {}, format="json", **headers).json()["flow_token"]
    headers["HTTP_X_LOGIN_FLOW"] = flow
    bad = client.post(
        base + "issue", {"mobile": "bad", "key": str(uuid.uuid4())}, format="json", **headers
    )
    assert bad.status_code == 400 and IssueEvent.objects.count() == 0
    invalid_csrf = client.post(
        base + "issue", {"mobile": "09123456789", "key": str(uuid.uuid4())}, format="json"
    )
    assert invalid_csrf.status_code == 403 and IssueEvent.objects.count() == 0
    issued = client.post(
        base + "issue",
        {"mobile": "09123456789", "key": str(uuid.uuid4())},
        format="json",
        HTTP_X_FORWARDED_FOR="1.2.3.4",
        **headers,
    )
    assert issued.status_code == 200
    result = issued.json()
    assert IssueEvent.objects.get().ip_digest == otp.digest("ip:127.0.0.1")
    assert "no-store" in issued["Cache-Control"]
    verified = client.post(
        base + "verify",
        {"challenge_id": result["challenge_id"], "code": result["notification"]["code"]},
        format="json",
        **headers,
    )
    assert verified.status_code == 200
    cookie = verified.cookies["invest_session"]
    assert cookie["httponly"] and cookie["samesite"] == "Lax"
    assert "invest_session" not in verified.json()
    assert client.get(base + "me").json()["authenticated"]
    for forbidden in ("role", "assurance", "owner"):
        headers["HTTP_X_CSRFTOKEN"] = client.get(base + "csrf").json()["csrfToken"]
        assert (
            client.post(
                base + "activity", {forbidden: "admin"}, format="json", **headers
            ).status_code
            == 400
        )
    data = str(list(AuditEvent.objects.values())) + caplog.text
    for secret in (result["notification"]["code"], flow, cookie.value, "09123456789"):
        assert secret not in data
    assert client.post(base + "logout", {}, format="json", **headers).status_code == 200
    client.cookies["invest_session"] = cookie.value
    assert not client.get(base + "me").json()["authenticated"]


def test_audit_failure_rolls_back_issuance_and_consumption():
    from apps.identity.models import IssueEvent

    flow = otp.new_flow()["flow_token"]
    with patch("apps.identity.otp.audit", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            issue(flow=flow)
    assert IssueEvent.objects.count() == 0
    token, result = issue(flow=flow)
    with patch("apps.identity.otp.audit", side_effect=RuntimeError):
        with pytest.raises(RuntimeError):
            verify(token, result)
    assert AuthSession.objects.count() == 0
    assert OTPChallenge.objects.get().state == "active"


def test_retry_expired_replaced_and_mode_change_never_exposes_code(settings):
    token, result = issue()
    challenge = OTPChallenge.objects.get(pk=result["challenge_id"])
    key = str(challenge.operation_key)
    with patch("apps.identity.otp.now", return_value=challenge.expires_at):
        replay = otp.issue(token, "09123456789", key, "127.0.0.1")
        assert replay["state"] == "expired" and "notification" not in replay
    settings.INVEST_ENV = "public"
    assert "notification" not in otp.issue(token, "09123456789", key, "127.0.0.1")
    settings.INVEST_ENV = "test"
    with patch("apps.identity.otp.now", return_value=challenge.issued_at + timedelta(seconds=60)):
        issue(flow=token)
        replay = otp.issue(token, "09123456789", key, "127.0.0.1")
        assert replay["state"] == "replaced" and "notification" not in replay


def test_number_fifteen_minute_window_boundary_independent_from_daily_cap():
    from apps.identity.models import IssueEvent

    flow, _ = issue()
    user = User.objects.get()
    at = timezone.now()
    IssueEvent.objects.all().delete()
    # One daily event has already left the short window; nine remain in it.
    IssueEvent.objects.create(
        flow_id=otp.get_flow(flow, at).pk,
        user=user,
        ip_digest="synthetic",
        at=at - timedelta(seconds=901),
    )
    for offset in range(9):
        IssueEvent.objects.create(
            flow_id=otp.get_flow(flow, at).pk,
            user=user,
            ip_digest="synthetic",
            at=at - timedelta(seconds=offset),
        )
    with patch("apps.identity.otp.now", return_value=at):
        with pytest.raises(otp.Fault) as exc:
            issue()
        assert exc.value.retry_after == 86400 - 901
    # Exact initial boundary is excluded for every generic sliding quota query.
    assert (
        otp.window_wait(
            IssueEvent.objects.filter(at__lte=at - timedelta(seconds=901)),
            at - timedelta(seconds=1),
            900,
            1,
        )
        == 0
    )


def test_failed_delivery_consumes_quota_and_retry_does_not_refund_or_redeliver(settings):
    from apps.identity.models import IssueEvent

    settings.OTP_DELIVERY_MODE = "sms"
    flow, result = issue()
    challenge = OTPChallenge.objects.get(pk=result["challenge_id"])
    assert result["delivery"] == "failed" and IssueEvent.objects.count() == 1
    assert otp.issue(flow, "09123456789", str(challenge.operation_key), "127.0.0.1") == result
    assert IssueEvent.objects.count() == 1


def test_intent_replacement_and_account_switch_are_final():
    from apps.identity import sessions

    flow = otp.new_flow()["flow_token"]
    otp.intent(flow, "set", {"destination": "/saved", "snapshot": {"listing": "old"}})
    otp.intent(flow, "set", {"destination": "/saved", "snapshot": {"listing": "new"}})
    _, result = issue(flow=flow)
    _, token = verify(flow, result)
    assert (
        otp.intent(flow, "consume", session_token=token)["handoff"]["snapshot"]["listing"] == "new"
    )
    a, ra = issue("09123456788")
    otp.intent(a, "set", {"destination": "/saved", "snapshot": {}}, token)
    _, other = verify(a, ra, current=token)
    assert not sessions.me(token)["authenticated"]
    with pytest.raises(otp.Fault, match="intent_unavailable"):
        otp.intent(a, "consume", session_token=other)


def test_intent_cannot_revive_after_switching_away_and_back():
    flow = otp.new_flow()["flow_token"]
    otp.intent(flow, "set", {"destination": "/saved", "snapshot": {"id": "synthetic"}})
    _, ra = issue(flow=flow)
    _, sa = verify(flow, ra)
    b, rb = issue("09123456788")
    _, sb = verify(b, rb, current=sa)
    c, rc = issue()
    _, sc = verify(c, rc, current=sb)
    with pytest.raises(otp.Fault, match="intent_unavailable"):
        otp.intent(flow, "consume", session_token=sc)


def test_trial_evidence_and_previous_code_are_unusable_in_public(settings):
    from apps.identity import sessions

    flow, result = issue()
    _, session = verify(flow, result)
    another, challenge = issue()
    settings.INVEST_ENV = "public"
    settings.OTP_DELIVERY_MODE = "sms"
    assert sessions.me(session) == {"authenticated": False}
    with pytest.raises(otp.Fault, match="delivery_unavailable"):
        verify(another, challenge)


def test_preexisting_django_cookie_cannot_fixate_trial_session(client):
    user = User.objects.create_user("+989123456789")
    client.force_login(user)
    assert client.get("/api/v1/auth/me").json() == {"authenticated": False}


def test_machine_contract_matches_implemented_trial_responses(client):
    import uuid

    from jsonschema import Draft202012Validator
    from openapi_spec_validator import validate as validate_openapi

    contract = client.get("/api/v1/schema").json()
    validate_openapi(contract)

    def validate(name, body):
        schema = {"$ref": "#/components/schemas/" + name, "components": contract["components"]}
        Draft202012Validator(schema).validate(body)

    validate("TrialMe", client.get("/api/v1/auth/me").json())
    csrf = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    headers = {"HTTP_X_CSRFTOKEN": csrf}
    flow = client.post("/api/v1/auth/flows", {}, format="json", **headers).json()
    validate("TrialFlow", flow)
    headers["HTTP_X_LOGIN_FLOW"] = flow["flow_token"]
    receipt = client.post(
        "/api/v1/auth/issue",
        {"mobile": "09123456789", "key": str(uuid.uuid4())},
        format="json",
        **headers,
    ).json()
    validate("TrialReceipt", receipt)
    verified = client.post(
        "/api/v1/auth/verify",
        {"challenge_id": receipt["challenge_id"], "code": receipt["notification"]["code"]},
        format="json",
        **headers,
    ).json()
    validate("TrialVerify", verified)
    validate("TrialMe", client.get("/api/v1/auth/me").json())
    assert "/auth/reauth" in contract["paths"] and "/auth/intent/consume" in contract["paths"]
