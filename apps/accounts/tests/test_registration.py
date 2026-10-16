import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestRegistration:
    url = reverse("v1:auth-register")

    def test_register_with_email_succeeds(self, api_client):
        resp = api_client.post(
            self.url,
            {
                "email": "new@example.com",
                "password": "CorrectHorse9!",
                "password_confirm": "CorrectHorse9!",
                "first_name": "New",
            },
            format="json",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["user"]["email"] == "new@example.com"
        assert body["data"]["user"]["role"] == "customer"
        assert "access" in body["data"]["tokens"]
        assert "refresh" in body["data"]["tokens"]
        # cost/role/is_staff must never be settable or exposed to the registrant
        assert "cost_price" not in body["data"]["user"]
        assert "is_staff" not in body["data"]["user"]

    def test_register_with_phone_only_succeeds(self, api_client):
        resp = api_client.post(
            self.url,
            {"phone_number": "01712345678", "password": "CorrectHorse9!", "password_confirm": "CorrectHorse9!"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["user"]["phone_number"] == "+8801712345678"

    def test_register_without_identifier_fails(self, api_client):
        resp = api_client.post(
            self.url, {"password": "CorrectHorse9!", "password_confirm": "CorrectHorse9!"}, format="json"
        )
        assert resp.status_code == 400

    def test_register_duplicate_email_fails(self, api_client, create_user):
        create_user(email="dup@example.com")
        resp = api_client.post(
            self.url,
            {"email": "dup@example.com", "password": "CorrectHorse9!", "password_confirm": "CorrectHorse9!"},
            format="json",
        )
        assert resp.status_code == 400
        assert "email" in resp.json()["errors"]

    def test_register_weak_password_rejected(self, api_client):
        resp = api_client.post(
            self.url,
            {"email": "weak@example.com", "password": "12345678", "password_confirm": "12345678"},
            format="json",
        )
        assert resp.status_code == 400

    def test_register_password_mismatch_rejected(self, api_client):
        resp = api_client.post(
            self.url,
            {"email": "mismatch@example.com", "password": "CorrectHorse9!", "password_confirm": "Different9!"},
            format="json",
        )
        assert resp.status_code == 400
        assert "password_confirm" in resp.json()["errors"]

    def test_password_is_hashed_not_plaintext(self, api_client):
        api_client.post(
            self.url,
            {"email": "hash@example.com", "password": "CorrectHorse9!", "password_confirm": "CorrectHorse9!"},
            format="json",
        )
        from apps.accounts.models import User

        user = User.objects.get(email="hash@example.com")
        assert user.password != "CorrectHorse9!"
        # Hasher is swapped to MD5 in test settings for speed; assert the real
        # invariant (never plaintext, always a recognised Django hash format)
        # rather than a specific algorithm name.
        assert "$" in user.password
        assert user.check_password("CorrectHorse9!")


def test_argon2_is_the_configured_production_hasher():
    """Production/dev settings must hash with Argon2 (verified at the settings level,
    independent of the fast MD5 hasher test settings swap in for speed)."""
    from config.settings.base import PASSWORD_HASHERS

    assert PASSWORD_HASHERS[0] == "django.contrib.auth.hashers.Argon2PasswordHasher"
