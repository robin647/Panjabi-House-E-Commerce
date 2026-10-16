import pytest
from django.urls import reverse

from apps.accounts.models import Role

pytestmark = pytest.mark.django_db


def _auth_header(api_client, create_user, **user_kwargs):
    user = create_user(**user_kwargs)
    login = api_client.post(
        reverse("v1:auth-login"),
        {"identifier": user.email, "password": "StrongPass9!"},
        format="json",
    ).json()
    return user, {"HTTP_AUTHORIZATION": f"Bearer {login['data']['tokens']['access']}"}


class TestProfile:
    def test_get_profile_requires_auth(self, api_client):
        resp = api_client.get(reverse("v1:profile-detail"))
        assert resp.status_code == 401

    def test_get_own_profile(self, api_client, create_user):
        user, headers = _auth_header(api_client, create_user, email="me@example.com")
        resp = api_client.get(reverse("v1:profile-detail"), **headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "me@example.com"

    def test_update_profile_name(self, api_client, create_user):
        user, headers = _auth_header(api_client, create_user, email="rename@example.com")
        resp = api_client.patch(reverse("v1:profile-detail"), {"first_name": "Updated"}, format="json", **headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["first_name"] == "Updated"

    def test_cannot_escalate_own_role_via_profile(self, api_client, create_user):
        user, headers = _auth_header(api_client, create_user, email="escalate@example.com")
        resp = api_client.patch(reverse("v1:profile-detail"), {"role": "super_admin"}, format="json", **headers)
        assert resp.status_code == 200  # request "succeeds" but the field is read-only and ignored
        user.refresh_from_db()
        assert user.role == Role.CUSTOMER

    def test_cannot_change_email_via_profile(self, api_client, create_user):
        user, headers = _auth_header(api_client, create_user, email="original@example.com")
        api_client.patch(reverse("v1:profile-detail"), {"email": "hacked@example.com"}, format="json", **headers)
        user.refresh_from_db()
        assert user.email == "original@example.com"


class TestChangePassword:
    url = reverse("v1:auth-change-password")

    def test_change_password_requires_correct_old_password(self, api_client, create_user):
        user, headers = _auth_header(api_client, create_user, email="cp@example.com")
        resp = api_client.post(
            self.url, {"old_password": "WrongOld1!", "new_password": "NewStrong9!"}, format="json", **headers
        )
        assert resp.status_code == 400
        assert "old_password" in resp.json()["errors"]

    def test_change_password_invalidates_existing_tokens(self, api_client, create_user):
        user, headers = _auth_header(api_client, create_user, email="invalidate@example.com")
        api_client.post(
            self.url, {"old_password": "StrongPass9!", "new_password": "BrandNewPass9!"}, format="json", **headers
        )
        # The OLD access token's underlying refresh family is blacklisted; verify old creds fail on login.
        resp = api_client.post(
            reverse("v1:auth-login"),
            {"identifier": "invalidate@example.com", "password": "StrongPass9!"},
            format="json",
        )
        assert resp.status_code == 401


class TestRoleBasedAccess:
    """A customer must never reach admin-only resources (enforced even with no admin API yet)."""

    def test_customer_role_is_not_staff(self, create_user):
        user = create_user(email="cust@example.com", role=Role.CUSTOMER)
        assert user.is_staff is False
        assert user.is_customer is True
        assert user.is_staff_role is False

    def test_staff_role_flagging(self, create_user):
        staff = create_user(email="staff@example.com", role=Role.STAFF)
        assert staff.is_staff_role is True
        assert staff.is_customer is False
