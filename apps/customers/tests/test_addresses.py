import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _auth(api_client, create_user, email="addruser@example.com"):
    create_user(email=email)
    login = api_client.post(
        reverse("v1:auth-login"), {"identifier": email, "password": "StrongPass9!"}, format="json"
    ).json()
    return {"HTTP_AUTHORIZATION": f"Bearer {login['data']['tokens']['access']}"}


class TestAddresses:
    def test_create_first_address_becomes_default(self, api_client, create_user):
        headers = _auth(api_client, create_user)
        resp = api_client.post(
            reverse("v1:address-list"),
            {"full_name": "A", "phone": "01812345678", "address_line": "x", "city": "Dhaka"},
            format="json",
            **headers,
        )
        assert resp.json()["data"]["is_default"] is True

    def test_setting_new_default_unsets_old_one(self, api_client, create_user):
        headers = _auth(api_client, create_user)
        url = reverse("v1:address-list")
        a1 = api_client.post(
            url,
            {"full_name": "A1", "phone": "01812345678", "address_line": "x", "city": "Dhaka"},
            format="json",
            **headers,
        ).json()["data"]
        a2 = api_client.post(
            url,
            {"full_name": "A2", "phone": "01812345678", "address_line": "y", "city": "Dhaka", "is_default": True},
            format="json",
            **headers,
        ).json()["data"]
        assert a2["is_default"] is True

        detail = api_client.get(reverse("v1:address-detail", kwargs={"uuid": a1["uuid"]}), **headers).json()["data"]
        assert detail["is_default"] is False

    def test_cannot_see_another_users_addresses(self, api_client, create_user):
        headers_a = _auth(api_client, create_user, "addr-user-a@example.com")
        api_client.post(
            reverse("v1:address-list"),
            {"full_name": "A", "phone": "01812345678", "address_line": "x", "city": "Dhaka"},
            format="json",
            **headers_a,
        )

        headers_b = _auth(api_client, create_user, "addr-user-b@example.com")
        resp = api_client.get(reverse("v1:address-list"), **headers_b)
        assert len(resp.json()["data"]) == 0
