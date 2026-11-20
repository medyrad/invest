import json
import os
from pathlib import Path

from config.env import read_environment

BASE_DIR = Path(__file__).resolve().parent.parent
ENV = read_environment(os.environ)
INVEST_ENV = ENV["mode"]
SECRET_KEY = ENV["secret"]
DEBUG = ENV["debug"]
ALLOWED_HOSTS = ENV["hosts"]
DATABASES = {"default": ENV["database"]}
CSRF_TRUSTED_ORIGINS = ENV["origins"]
OTP_DELIVERY_MODE = ENV["otp"]
PUBLIC_LAUNCH_ENABLED = ENV["launch_enabled"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "apps.identity",
    "apps.catalog",
    "apps.workspace",
    "apps.core",
    "apps.services",
    "apps.assistant",
]
MIDDLEWARE = [
    "config.middleware.RequestContextMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
AUTH_USER_MODEL = "identity.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_TZ = True
APPEND_SLASH = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = ENV["secure"]
CSRF_COOKIE_SECURE = ENV["secure"]
SECURE_SSL_REDIRECT = ENV["secure"]
SECURE_PROXY_SSL_HEADER = None
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_FAILURE_VIEW = "config.api.csrf_failure"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "config.api.exception_handler",
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"safe": {"format": "{levelname} {message}", "style": "{"}},
    "filters": {"redact_secrets": {"()": "config.secrets.SecretRedactionFilter"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "safe", "filters": ["redact_secrets"]},
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "invest": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["null"], "propagate": False},
        "django.security": {"handlers": ["null"], "propagate": False},
    },
}

# Engineering capacity limits for the synthetic A1 environment (D32).
WORKSPACE_ACCOUNT_BYTES = int(os.environ.get("WORKSPACE_ACCOUNT_BYTES", 500 * 1048576))
WORKSPACE_HOURLY_UPLOADS = int(os.environ.get("WORKSPACE_HOURLY_UPLOADS", 30))
WORKSPACE_MAX_DRAFTS = int(os.environ.get("WORKSPACE_MAX_DRAFTS", 100))
CLAMAV_HOST = os.environ.get("CLAMAV_HOST", "scanner")
CLAMAV_PORT = int(os.environ.get("CLAMAV_PORT", 3310))

WORKSPACE_HOURLY_RECEIVES = int(os.environ.get("WORKSPACE_HOURLY_RECEIVES", 60))

# Delivery fingerprint; generated from source, not from environment or credentials.
CORE_VERSION = json.loads((BASE_DIR / "config/core_version.json").read_text())["version"]

# Private runtime-only AI configuration. Never expose these values through version/schema APIs.
ASSISTANT_OPENAI_API_KEY_FILE = os.environ.get(
    "OPENAI_API_KEY_FILE", "/run/secrets/openai_api_key"
)
ASSISTANT_OPENAI_API_KEY_FALLBACK = (
    os.environ.get("OPENAI_API_KEY", "") if INVEST_ENV in {"development", "test"} else ""
)
ASSISTANT_OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
ASSISTANT_PROVIDER = os.environ.get("ASSISTANT_PROVIDER", "openai")
