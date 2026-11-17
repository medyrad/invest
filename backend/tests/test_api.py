from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from django.db import OperationalError


def test_live_does_not_use_database(client):
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200 and response.json() == {"status": "ok"}
    assert response["Cache-Control"] == "no-store"
    UUID(response["X-Request-ID"])


@pytest.mark.django_db
def test_ready_and_database_failure(client):
    assert client.get("/api/v1/health/ready").status_code == 200
    with patch(
        "django.db.backends.base.base.BaseDatabaseWrapper.cursor",
        side_effect=OperationalError("PRIVATE-SENTINEL"),
    ):
        response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


@pytest.mark.django_db(transaction=True)
def test_readiness_uses_actual_application_credentials(client):
    from django.db import connection

    connection.close()
    try:
        with patch.dict(connection.settings_dict, {"PASSWORD": "invalid-test-password"}):
            response = client.get("/api/v1/health/ready")
            assert response.status_code == 503
            assert response.json() == {"status": "unavailable"}
    finally:
        connection.close()
    assert client.get("/api/v1/health/ready").status_code == 200


@pytest.mark.parametrize("incoming", [str(uuid4()), "bad\trequest", "x" * 300])
def test_request_id_and_safe_404(client, incoming):
    response = client.get("/missing", HTTP_X_REQUEST_ID=incoming)
    actual = response["X-Request-ID"]
    UUID(actual)
    if len(incoming) == 36:
        assert actual == incoming
    else:
        assert actual != incoming
    assert response.json()["error"] == {
        "code": "not_found",
        "message": "مسیر موردنظر پیدا نشد.",
        "fields": {},
        "request_id": actual,
    }


def test_unsafe_method_needs_csrf_then_returns_405(client):
    assert client.post("/api/v1/health/live").status_code == 403
    token = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    response = client.post("/api/v1/health/live", HTTP_X_CSRFTOKEN=token)
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


@pytest.mark.urls("tests.urls")
def test_unhandled_error_is_safe(client, caplog):
    client.raise_request_exception = False
    response = client.get("/api/v1/_test/crash")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert response.json()["error"]["request_id"] == response["X-Request-ID"]
    assert "PRIVATE-SENTINEL" not in response.content.decode() + caplog.text


def test_invalid_host_is_safe(client):
    response = client.get("/api/v1/health/live", HTTP_HOST="evil.example")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_host"
