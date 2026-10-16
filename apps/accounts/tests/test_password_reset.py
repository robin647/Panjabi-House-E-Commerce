import re

import pytest
from django.core import mail
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestPasswordReset:
    forgot_url = reverse("v1:auth-forgot-password")
    reset_url = reverse("v1:auth-reset-password")

    def test_forgot_password_known_and_unknown_identifier_return_identical_response(self, api_client, create_user):
        create_user(email="known@example.com")
        r1 = api_client.post(self.forgot_url, {"identifier": "known@example.com"}, format="json")
        r2 = api_client.post(self.forgot_url, {"identifier": "unknown@example.com"}, format="json")
        assert r1.status_code == r2.status_code == 200
        assert r1.json()["message"] == r2.json()["message"]

    def test_forgot_password_sends_single_use_link(self, api_client, create_user):
        create_user(email="reset@example.com", password="OldPass9!")
        api_client.post(self.forgot_url, {"identifier": "reset@example.com"}, format="json")
        assert len(mail.outbox) == 1
        match = re.search(r"uid=([^&]+)&token=([^\s]+)", mail.outbox[0].body)
        uid, token = match.group(1), match.group(2)

        resp = api_client.post(
            self.reset_url, {"uid": uid, "token": token, "new_password": "BrandNewPass9!"}, format="json"
        )
        assert resp.status_code == 200

        # Token must be single-use.
        resp2 = api_client.post(
            self.reset_url, {"uid": uid, "token": token, "new_password": "AnotherPass9!"}, format="json"
        )
        assert resp2.status_code == 400

        # New password actually works; old one doesn't.
        login_new = api_client.post(
            reverse("v1:auth-login"), {"identifier": "reset@example.com", "password": "BrandNewPass9!"}, format="json"
        )
        assert login_new.status_code == 200
        login_old = api_client.post(
            reverse("v1:auth-login"), {"identifier": "reset@example.com", "password": "OldPass9!"}, format="json"
        )
        assert login_old.status_code == 401

    def test_reset_with_invalid_token_rejected(self, api_client, create_user):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = create_user(email="badtoken@example.com")
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        resp = api_client.post(
            self.reset_url, {"uid": uid, "token": "not-a-real-token", "new_password": "Whatever9!"}, format="json"
        )
        assert resp.status_code == 400
