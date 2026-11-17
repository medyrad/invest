import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def accounts(db):
    return [
        get_user_model().objects.create_user(mobile=mobile)
        for mobile in ("+12025550101", "+12025550102")
    ]
