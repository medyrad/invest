from config.settings import *  # noqa: F403

if INVEST_ENV != "test":  # noqa: F405
    raise RuntimeError("Test URLConf requires INVEST_ENV=test")
ROOT_URLCONF = "tests.urls"
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:3109"]
