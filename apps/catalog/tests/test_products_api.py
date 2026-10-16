import pytest
from django.urls import reverse

from .factories import CategoryFactory, ProductFactory, ProductVariantFactory

pytestmark = pytest.mark.django_db


class TestProductListing:
    def test_list_only_shows_published_active_products(self, api_client):
        ProductFactory(is_published=True, is_active=True)
        ProductFactory(is_published=False, is_active=True)
        ProductFactory(is_published=True, is_active=False)
        resp = api_client.get(reverse("v1:product-list"))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_filter_by_category_slug(self, api_client):
        cat_a = CategoryFactory(name="A")
        cat_b = CategoryFactory(name="B")
        ProductFactory(category=cat_a)
        ProductFactory(category=cat_b)
        resp = api_client.get(reverse("v1:product-list") + f"?category={cat_a.slug}")
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["category_slug"] == cat_a.slug

    def test_price_filter(self, api_client):
        ProductFactory(regular_price="500.00")
        ProductFactory(regular_price="5000.00")
        resp = api_client.get(reverse("v1:product-list") + "?min_price=1000")
        data = resp.json()["data"]
        assert len(data) == 1
        assert float(data[0]["price"]) >= 1000

    def test_sale_price_reflected_in_effective_price(self, api_client):
        ProductFactory(regular_price="1000.00", sale_price="800.00")
        resp = api_client.get(reverse("v1:product-list"))
        data = resp.json()["data"][0]
        assert data["price"] == "800.00"
        assert data["discount_percentage"] == 20

    def test_cost_price_never_exposed_to_customer(self, api_client):
        ProductFactory(cost_price="100.00")
        resp = api_client.get(reverse("v1:product-list"))
        assert "cost_price" not in resp.json()["data"][0]

    def test_product_detail_includes_variants(self, api_client):
        product = ProductFactory()
        ProductVariantFactory(product=product, size="M", color="Black")
        ProductVariantFactory(product=product, size="L", color="White")
        resp = api_client.get(reverse("v1:product-detail", kwargs={"slug": product.slug}))
        assert resp.status_code == 200
        assert len(resp.json()["data"]["variants"]) == 2

    def test_unpublished_product_detail_404s(self, api_client):
        product = ProductFactory(is_published=False)
        resp = api_client.get(reverse("v1:product-detail", kwargs={"slug": product.slug}))
        assert resp.status_code == 404
