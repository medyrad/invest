import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.urls("tests.urls")


@pytest.mark.django_db
@pytest.mark.parametrize("authenticated", [False, True])
def test_csrf_protects_guest_and_authenticated(client, authenticated):
    if authenticated:
        client.force_login(get_user_model().objects.create_user(mobile="+12025550101"))
    url = "/api/v1/_test/probe"
    assert client.post(url, {"message": "آزمون"}, format="json").status_code == 403
    bootstrap = client.get("/api/v1/auth/csrf")
    token = bootstrap.json()["csrfToken"]
    assert bootstrap.cookies["csrftoken"]["httponly"]
    assert "Cookie" in bootstrap["Vary"]
    assert (
        client.post(
            url, {}, format="json", HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN="https://evil.example"
        ).status_code
        == 403
    )
    assert client.post(url, {}, format="json", HTTP_X_CSRFTOKEN="invalid").status_code == 403
    response = client.post(
        url,
        {"message": "آزمون"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_ORIGIN="http://testserver",
    )
    assert response.status_code == 200
    assert response.json()["body"] == {"message": "آزمون"}


def test_production_urlconf_has_no_probe_or_login(client):
    from django.test import override_settings

    with override_settings(ROOT_URLCONF="config.urls"):
        for path in ("_test/probe", "auth/login", "auth/otp"):
            assert client.get("/api/v1/" + path).status_code == 404
