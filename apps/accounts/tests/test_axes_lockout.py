import pytest
from django.test import override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


@override_settings(AXES_ENABLED=True, AXES_FAILURE_LIMIT=3)
def test_repeated_failed_logins_are_locked_out(api_client, create_user):
    create_user(email="lockout@example.com", password="CorrectHorse9!")
    url = reverse("v1:auth-login")
    for _ in range(3):
        resp = api_client.post(
            url, {"identifier": "lockout@example.com", "password": "WrongPassword1!"}, format="json"
        )
        assert resp.status_code == 401

    # 4th attempt (even with the CORRECT password) should now be locked by Axes.
    resp = api_client.post(url, {"identifier": "lockout@example.com", "password": "CorrectHorse9!"}, format="json")
    assert resp.status_code in (401, 403)
