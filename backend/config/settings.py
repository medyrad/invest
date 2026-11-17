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
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "safe"},
        "null": {"class": "logging.NullHandler"},
    },
    "loggers": {
        "invest": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["null"], "propagate": False},
        "django.security": {"handlers": ["null"], "propagate": False},
    },
}
