import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import read_environment


def public_env():
    return {
        "INVEST_ENV": "public",
        "DJANGO_SECRET_KEY": "aB3!" * 16,
        "DJANGO_ALLOWED_HOSTS": "invest.example.com",
        "CSRF_TRUSTED_ORIGINS": "https://invest.example.com",
        "DATABASE_URL": "postgresql://example:secret@db:5432/invest",
        "OTP_DELIVERY_MODE": "sms",
        "PUBLIC_LAUNCH_ENABLED": "false",
    }


def test_positive_public():
    config = read_environment(public_env())
    assert config["secure"] and not config["debug"]
    assert not config["launch_enabled"]


def test_actual_public_settings_are_secure():
    import json
    import os
    import subprocess
    import sys

    code = (
        "import json; from config import settings as s; "
        "print(json.dumps([s.DEBUG,s.SESSION_COOKIE_SECURE,s.CSRF_COOKIE_SECURE,"
        "s.SECURE_SSL_REDIRECT,s.SESSION_COOKIE_HTTPONLY,s.CSRF_COOKIE_HTTPONLY,"
        "s.SECURE_PROXY_SSL_HEADER,s.PUBLIC_LAUNCH_ENABLED]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env=os.environ | public_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) == [False, True, True, True, True, True, None, False]


def test_public_deployment_checks_only_defer_real_domain_hsts():
    import os
    import re
    import secrets
    import subprocess
    import sys

    env = os.environ | public_env() | {"DJANGO_SECRET_KEY": secrets.token_urlsafe(64)}
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert set(re.findall(r"security\.W\d+", result.stderr)) == {"security.W004"}


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("DJANGO_SECRET_KEY", ""),
        ("DJANGO_SECRET_KEY", "test-" + "x" * 60),
        ("DJANGO_DEBUG", "true"),
        ("DJANGO_DEBUG", "maybe"),
        ("DJANGO_ALLOWED_HOSTS", "*"),
        ("DJANGO_ALLOWED_HOSTS", ""),
        ("CSRF_TRUSTED_ORIGINS", "http://invest.example.com"),
        ("CSRF_TRUSTED_ORIGINS", ""),
        ("OTP_DELIVERY_MODE", "notification"),
        ("PUBLIC_LAUNCH_ENABLED", "true"),
        ("DATABASE_URL", "sqlite:///db.sqlite"),
        ("DATABASE_URL", "postgresql://user:SENSITIVE@db:bad/db"),
        ("INVEST_ENV", "production-typo"),
    ],
)
def test_invalid_environment_fails_without_secret(key, value):
    env = public_env() | {key: value}
    with pytest.raises(ImproperlyConfigured) as error:
        read_environment(env)
    assert "SENSITIVE" not in str(error.value)
    assert env["DATABASE_URL"] not in str(error.value)
