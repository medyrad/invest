from uuid import UUID

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError, connection, transaction

pytestmark = pytest.mark.django_db


def test_independent_unverified_accounts(accounts):
    assert connection.vendor == "postgresql"
    users = accounts
    assert users[0].pk != users[1].pk
    for user in users:
        user.refresh_from_db()
        assert isinstance(user.pk, UUID)
        assert user.is_active and not user.is_staff and not user.is_superuser
        assert user.mobile_verified_at is None
        assert not user.has_usable_password()
        assert user.created_at and user.updated_at


def test_duplicate_rejected_by_database():
    get_user_model().objects.create_user(mobile="+12025550101")
    with pytest.raises(IntegrityError), transaction.atomic():
        get_user_model().objects.create(mobile="+12025550101")


@pytest.mark.parametrize(
    "mobile",
    [
        "",
        "09121234567",
        "+0123456789",
        "+۱۲۳۴۵۶۷۸۹",
        "+1234567",
        "+1234567890123456",
        "+12025550101\n",
    ],
)
def test_invalid_mobile_rejected_by_manager_and_database(mobile):
    with pytest.raises(ValidationError):
        get_user_model().objects.create_user(mobile=mobile)
    with pytest.raises((IntegrityError, DataError)), transaction.atomic():
        get_user_model().objects.create(mobile=mobile)
