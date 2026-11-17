from contextlib import contextmanager

from django.db import connection, transaction


@contextmanager
def identity_transaction():
    """Shared serialization point for issuance, consumption and authority changes."""
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(73003001)")
        yield
