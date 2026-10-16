import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_health_check_returns_ok(api_client):
    resp = api_client.get(reverse("v1:health-check"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["database"] is True


def test_shop_config_is_public_and_exposes_delivery_charges(api_client):
    resp = api_client.get(reverse("v1:shop-config"))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["currency"] == "BDT"
    assert data["delivery_charge_inside_dhaka"] == "60.00"
    assert data["delivery_charge_outside_dhaka"] == "120.00"
    assert data["payment_methods"] == ["cod"]
