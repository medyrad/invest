"""Bounded database protection for non-streaming private response construction."""

from functools import wraps

from django.db import OperationalError, connection, transaction

from .schema import Fault


def download_transaction(fn):
    @wraps(fn)
    def guarded(*args, **kwargs):
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL lock_timeout = '5s'")
                return fn(*args, **kwargs)
        except OperationalError as exc:
            # Only PostgreSQL lock timeout, after the failed transaction is rolled back.
            if getattr(exc.__cause__, "sqlstate", None) == "55P03":
                raise Fault(
                    "وضعیت دسترسی یا فایل در حال تغییر است؛ دریافت را دوباره امتحان کنید.",
                    409,
                    "files",
                ) from exc
            raise

    return guarded
