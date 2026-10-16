import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestLogin:
    url = reverse("v1:auth-login")

    def test_login_with_email(self, api_client, create_user):
        create_user(email="login@example.com", password="CorrectHorse9!")
        resp = api_client.post(
            self.url, {"identifier": "login@example.com", "password": "CorrectHorse9!"}, format="json"
        )
        assert resp.status_code == 200
        assert "access" in resp.json()["data"]["tokens"]

    def test_login_with_phone(self, api_client, create_user):
        create_user(email=None, phone_number="+8801812345678", password="CorrectHorse9!")
        resp = api_client.post(self.url, {"identifier": "01812345678", "password": "CorrectHorse9!"}, format="json")
        assert resp.status_code == 200

    def test_login_wrong_password_returns_401(self, api_client, create_user):
        create_user(email="wp@example.com", password="CorrectHorse9!")
        resp = api_client.post(
            self.url, {"identifier": "wp@example.com", "password": "WrongPassword1!"}, format="json"
        )
        assert resp.status_code == 401
        assert resp.json()["success"] is False

    def test_login_unknown_identifier_returns_401_not_500(self, api_client):
        resp = api_client.post(
            self.url, {"identifier": "ghost@example.com", "password": "Whatever123!"}, format="json"
        )
        assert resp.status_code == 401

    def test_login_inactive_user_rejected(self, api_client, create_user):
        user = create_user(email="inactive@example.com", password="CorrectHorse9!")
        user.is_active = False
        user.save(update_fields=["is_active"])
        resp = api_client.post(
            self.url, {"identifier": "inactive@example.com", "password": "CorrectHorse9!"}, format="json"
        )
        assert resp.status_code == 401

    def test_login_updates_last_login(self, api_client, create_user):
        user = create_user(email="lastlogin@example.com", password="CorrectHorse9!")
        assert user.last_login is None
        api_client.post(self.url, {"identifier": "lastlogin@example.com", "password": "CorrectHorse9!"}, format="json")
        user.refresh_from_db()
        assert user.last_login is not None


class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client, create_user):
        create_user(email="lo@example.com", password="CorrectHorse9!")
        login = api_client.post(
            reverse("v1:auth-login"), {"identifier": "lo@example.com", "password": "CorrectHorse9!"}, format="json"
        ).json()
        access, refresh = login["data"]["tokens"]["access"], login["data"]["tokens"]["refresh"]

        resp = api_client.post(
            reverse("v1:auth-logout"), {"refresh": refresh}, format="json", HTTP_AUTHORIZATION=f"Bearer {access}"
        )
        assert resp.status_code == 200

        refresh_resp = api_client.post(reverse("v1:auth-token-refresh"), {"refresh": refresh}, format="json")
        assert refresh_resp.status_code == 401

    def test_logout_requires_authentication(self, api_client):
        resp = api_client.post(reverse("v1:auth-logout"), {"refresh": "whatever"}, format="json")
        assert resp.status_code == 401
