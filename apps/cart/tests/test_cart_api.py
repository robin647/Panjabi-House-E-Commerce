import pytest
from django.urls import reverse

from apps.catalog.tests.factories import ProductVariantFactory

pytestmark = pytest.mark.django_db


def _auth(api_client, create_user):
    user = create_user(email="cartuser@example.com")
    login = api_client.post(
        reverse("v1:auth-login"), {"identifier": "cartuser@example.com", "password": "StrongPass9!"}, format="json"
    ).json()
    return user, {"HTTP_AUTHORIZATION": f"Bearer {login['data']['tokens']['access']}"}


class TestCart:
    def test_add_item_requires_auth(self, api_client):
        resp = api_client.post(reverse("v1:cart-item-create"), {}, format="json")
        assert resp.status_code == 401

    def test_add_item_success(self, api_client, create_user):
        _, headers = _auth(api_client, create_user)
        variant = ProductVariantFactory(stock_quantity=10)
        resp = api_client.post(
            reverse("v1:cart-item-create"), {"variant_id": str(variant.uuid), "quantity": 2}, format="json", **headers
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["item_count"] == 2

    def test_add_item_beyond_stock_rejected(self, api_client, create_user):
        _, headers = _auth(api_client, create_user)
        variant = ProductVariantFactory(stock_quantity=2)
        resp = api_client.post(
            reverse("v1:cart-item-create"), {"variant_id": str(variant.uuid), "quantity": 5}, format="json", **headers
        )
        assert resp.status_code == 400

    def test_adding_same_variant_twice_sums_quantity(self, api_client, create_user):
        _, headers = _auth(api_client, create_user)
        variant = ProductVariantFactory(stock_quantity=10)
        url = reverse("v1:cart-item-create")
        api_client.post(url, {"variant_id": str(variant.uuid), "quantity": 2}, format="json", **headers)
        resp = api_client.post(url, {"variant_id": str(variant.uuid), "quantity": 3}, format="json", **headers)
        assert resp.json()["data"]["items"][0]["quantity"] == 5

    def test_inactive_variant_cannot_be_added(self, api_client, create_user):
        _, headers = _auth(api_client, create_user)
        variant = ProductVariantFactory(stock_quantity=10, is_active=False)
        resp = api_client.post(
            reverse("v1:cart-item-create"), {"variant_id": str(variant.uuid), "quantity": 1}, format="json", **headers
        )
        assert resp.status_code == 400

    def test_remove_item(self, api_client, create_user):
        _, headers = _auth(api_client, create_user)
        variant = ProductVariantFactory(stock_quantity=10)
        add = api_client.post(
            reverse("v1:cart-item-create"), {"variant_id": str(variant.uuid), "quantity": 1}, format="json", **headers
        ).json()
        item_uuid = add["data"]["items"][0]["uuid"]
        resp = api_client.delete(reverse("v1:cart-item-detail", kwargs={"item_uuid": item_uuid}), **headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["item_count"] == 0

    def test_one_users_cart_is_not_visible_to_another(self, api_client, create_user):
        create_user(email="a@example.com")
        create_user(email="b@example.com")
        variant = ProductVariantFactory(stock_quantity=10)

        login_a = api_client.post(
            reverse("v1:auth-login"), {"identifier": "a@example.com", "password": "StrongPass9!"}, format="json"
        ).json()
        headers_a = {"HTTP_AUTHORIZATION": f"Bearer {login_a['data']['tokens']['access']}"}
        api_client.post(
            reverse("v1:cart-item-create"),
            {"variant_id": str(variant.uuid), "quantity": 1},
            format="json",
            **headers_a,
        )

        login_b = api_client.post(
            reverse("v1:auth-login"), {"identifier": "b@example.com", "password": "StrongPass9!"}, format="json"
        ).json()
        headers_b = {"HTTP_AUTHORIZATION": f"Bearer {login_b['data']['tokens']['access']}"}
        resp = api_client.get(reverse("v1:cart-detail"), **headers_b)
        assert resp.json()["data"]["item_count"] == 0
