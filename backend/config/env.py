"""Validate configuration before serving requests; never include values in failures."""

from urllib.parse import unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured


def read_environment(env):
    def fail(key):
        raise ImproperlyConfigured(f"Invalid or missing configuration: {key}")

    def boolean(key, default="false"):
        value = env.get(key, default)
        if value not in ("true", "false"):
            fail(key)
        return value == "true"

    mode = env.get("INVEST_ENV", "")
    if mode not in ("development", "test", "public"):
        fail("INVEST_ENV")
    secure = mode == "public"
    secret = env.get("DJANGO_SECRET_KEY", "")
    if len(secret) < 50 or any(
        word in secret.lower() for word in ("replace-with", "placeholder", "test-", "development")
    ):
        fail("DJANGO_SECRET_KEY")
    debug = boolean("DJANGO_DEBUG")
    hosts = [
        host.strip() for host in env.get("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()
    ]
    origins = [
        origin.strip()
        for origin in env.get("CSRF_TRUSTED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if not hosts or any("*" in host or "/" in host or ":" in host for host in hosts):
        fail("DJANGO_ALLOWED_HOSTS")
    if not origins:
        fail("CSRF_TRUSTED_ORIGINS")
    for origin in origins:
        try:
            parsed = urlsplit(origin)
            valid = (
                parsed.scheme in (("https",) if secure else ("http", "https"))
                and parsed.hostname
                and "*" not in origin
                and not parsed.username
                and not parsed.password
                and not parsed.path
                and not parsed.query
                and not parsed.fragment
            )
            _ = parsed.port
        except ValueError:
            valid = False
        if not valid:
            fail("CSRF_TRUSTED_ORIGINS")
    otp = env.get("OTP_DELIVERY_MODE", "")
    launch = boolean("PUBLIC_LAUNCH_ENABLED")
    if otp not in ("notification", "sms"):
        fail("OTP_DELIVERY_MODE")
    if launch:
        fail("PUBLIC_LAUNCH_ENABLED")  # S02 cannot enable public intake.
    if secure and debug:
        fail("DJANGO_DEBUG")
    if secure and otp != "sms":
        fail("OTP_DELIVERY_MODE")
    try:
        db = urlsplit(env.get("DATABASE_URL", ""))
        valid = (
            db.scheme == "postgresql"
            and db.hostname
            and db.username
            and db.password
            and db.path.startswith("/")
            and len(db.path) > 1
            and not db.query
            and not db.fragment
        )
        port = db.port or 5432
        if not valid:
            fail("DATABASE_URL")
    except ValueError:
        fail("DATABASE_URL")
    return {
        "mode": mode,
        "secure": secure,
        "secret": secret,
        "debug": debug,
        "hosts": hosts,
        "origins": origins,
        "otp": otp,
        "launch_enabled": launch,
        "database": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": unquote(db.path[1:]),
            "USER": unquote(db.username),
            "PASSWORD": unquote(db.password),
            "HOST": db.hostname,
            "PORT": port,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"connect_timeout": 3, "options": "-c statement_timeout=3000"},
        },
    }
