import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    from apps.accounts.models import Role, User

    def _create(email="user@example.com", phone_number=None, password="StrongPass9!", role=Role.CUSTOMER, **kwargs):
        return User.objects.create_user(
            email=email, phone_number=phone_number, password=password, role=role, **kwargs
        )

    return _create
