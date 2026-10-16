import threading

import pytest
from django.db import connection
from django.urls import reverse

from apps.catalog.tests.factories import ProductVariantFactory

pytestmark = pytest.mark.django_db


def _checkout_ready_user(api_client, create_user, email="checkout@example.com", stock=10):
    user = create_user(email=email)
    login = api_client.post(
        reverse("v1:auth-login"), {"identifier": email, "password": "StrongPass9!"}, format="json"
    ).json()
    headers = {"HTTP_AUTHORIZATION": f"Bearer {login['data']['tokens']['access']}"}
    variant = ProductVariantFactory(stock_quantity=stock)
    api_client.post(
        reverse("v1:cart-item-create"), {"variant_id": str(variant.uuid), "quantity": 1}, format="json", **headers
    )
    address = api_client.post(
        reverse("v1:address-list"),
        {"full_name": "Test", "phone": "01812345678", "address_line": "123 St", "city": "Dhaka"},
        format="json",
        **headers,
    ).json()
    return user, headers, variant, address["data"]["uuid"]


class TestCheckout:
    def test_checkout_requires_idempotency_key(self, api_client, create_user):
        _, headers, _, address_uuid = _checkout_ready_user(api_client, create_user)
        resp = api_client.post(reverse("v1:checkout"), {"address_id": address_uuid}, format="json", **headers)
        assert resp.status_code == 400
        assert "idempotency_key" in resp.json()["errors"]

    def test_checkout_creates_order_and_decrements_stock(self, api_client, create_user):
        _, headers, variant, address_uuid = _checkout_ready_user(api_client, create_user, stock=5)
        resp = api_client.post(
            reverse("v1:checkout"),
            {"address_id": address_uuid},
            format="json",
            HTTP_IDEMPOTENCY_KEY="k1",
            **headers,
        )
        assert resp.status_code == 201
        variant.refresh_from_db()
        assert variant.stock_quantity == 4

    def test_checkout_empty_cart_rejected(self, api_client, create_user):
        create_user(email="emptycart@example.com")
        login = api_client.post(
            reverse("v1:auth-login"),
            {"identifier": "emptycart@example.com", "password": "StrongPass9!"},
            format="json",
        ).json()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {login['data']['tokens']['access']}"}
        address = api_client.post(
            reverse("v1:address-list"),
            {"full_name": "T", "phone": "01812345678", "address_line": "x", "city": "Dhaka"},
            format="json",
            **headers,
        ).json()
        resp = api_client.post(
            reverse("v1:checkout"),
            {"address_id": address["data"]["uuid"]},
            format="json",
            HTTP_IDEMPOTENCY_KEY="k2",
            **headers,
        )
        assert resp.status_code == 400
        assert "cart" in resp.json()["errors"]

    def test_checkout_same_idempotency_key_returns_same_order_not_a_duplicate(self, api_client, create_user):
        _, headers, variant, address_uuid = _checkout_ready_user(api_client, create_user, stock=5)
        r1 = api_client.post(
            reverse("v1:checkout"),
            {"address_id": address_uuid},
            format="json",
            HTTP_IDEMPOTENCY_KEY="dup-key",
            **headers,
        )
        order_number = r1.json()["data"]["order_number"]
        r2 = api_client.post(
            reverse("v1:checkout"),
            {"address_id": address_uuid},
            format="json",
            HTTP_IDEMPOTENCY_KEY="dup-key",
            **headers,
        )
        assert r2.json()["data"]["order_number"] == order_number

        orders = api_client.get(reverse("v1:order-list"), **headers).json()["data"]
        assert len(orders) == 1

    def test_checkout_wrong_users_address_rejected(self, api_client, create_user):
        create_user(email="addr-a@example.com")
        create_user(email="addr-b@example.com")

        login_a = api_client.post(
            reverse("v1:auth-login"), {"identifier": "addr-a@example.com", "password": "StrongPass9!"}, format="json"
        ).json()
        headers_a = {"HTTP_AUTHORIZATION": f"Bearer {login_a['data']['tokens']['access']}"}
        address_a = api_client.post(
            reverse("v1:address-list"),
            {"full_name": "A", "phone": "01812345678", "address_line": "x", "city": "Dhaka"},
            format="json",
            **headers_a,
        ).json()["data"]["uuid"]

        login_b = api_client.post(
            reverse("v1:auth-login"), {"identifier": "addr-b@example.com", "password": "StrongPass9!"}, format="json"
        ).json()
        headers_b = {"HTTP_AUTHORIZATION": f"Bearer {login_b['data']['tokens']['access']}"}
        variant = ProductVariantFactory(stock_quantity=5)
        api_client.post(
            reverse("v1:cart-item-create"),
            {"variant_id": str(variant.uuid), "quantity": 1},
            format="json",
            **headers_b,
        )

        resp = api_client.post(
            reverse("v1:checkout"), {"address_id": address_a}, format="json", HTTP_IDEMPOTENCY_KEY="k3", **headers_b
        )
        assert resp.status_code == 400
        assert "address_id" in resp.json()["errors"]

    def test_one_users_orders_not_visible_to_another(self, api_client, create_user):
        _, headers_a, _, address_a = _checkout_ready_user(api_client, create_user, email="ord-a@example.com", stock=5)
        api_client.post(
            reverse("v1:checkout"), {"address_id": address_a}, format="json", HTTP_IDEMPOTENCY_KEY="k4", **headers_a
        )

        _, headers_b, _, _ = _checkout_ready_user(api_client, create_user, email="ord-b@example.com", stock=5)
        resp = api_client.get(reverse("v1:order-list"), **headers_b)
        assert len(resp.json()["data"]) == 0


@pytest.mark.concurrency
@pytest.mark.django_db(transaction=True)
class TestConcurrentCheckout:
    def test_two_simultaneous_checkouts_for_last_unit_never_oversell(self, create_user):
        """
        Real threads, real PostgreSQL row locking - not simulated. Two
        customers race to buy the single remaining unit of one variant;
        exactly one checkout must succeed and stock must land at exactly 0,
        never negative. Requires transaction=True (TransactionTestCase style)
        so the two threads actually see each other's committed rows, like
        two real concurrent requests would - the default django_db wraps
        each test in one uncommitted outer transaction, which would hide
        the very race condition this test exists to catch.
        """
        from rest_framework.test import APIClient

        variant = ProductVariantFactory(stock_quantity=1)
        variant_uuid = str(variant.uuid)

        for email in ("race-a@example.com", "race-b@example.com"):
            create_user(email=email)

        results = {}

        def attempt(email, key):
            connection.close()
            client = APIClient()
            login = client.post(
                reverse("v1:auth-login"), {"identifier": email, "password": "StrongPass9!"}, format="json"
            ).json()
            headers = {"HTTP_AUTHORIZATION": f"Bearer {login['data']['tokens']['access']}"}
            client.post(
                reverse("v1:cart-item-create"), {"variant_id": variant_uuid, "quantity": 1}, format="json", **headers
            )
            address = client.post(
                reverse("v1:address-list"),
                {"full_name": email, "phone": "01812345678", "address_line": "Race St", "city": "Dhaka"},
                format="json",
                **headers,
            ).json()["data"]["uuid"]
            resp = client.post(
                reverse("v1:checkout"),
                {"address_id": address},
                format="json",
                HTTP_IDEMPOTENCY_KEY=key,
                **headers,
            )
            results[email] = resp.status_code
            connection.close()

        t1 = threading.Thread(target=attempt, args=("race-a@example.com", "race-key-a"))
        t2 = threading.Thread(target=attempt, args=("race-b@example.com", "race-key-b"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        successes = [s for s in results.values() if s == 201]
        variant.refresh_from_db()

        assert len(successes) == 1, f"Overselling occurred: {results}"
        assert variant.stock_quantity == 0
