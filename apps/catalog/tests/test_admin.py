import pytest
from django.urls import reverse

from apps.accounts.models import User

from .factories import CategoryFactory, ProductFactory, ProductVariantFactory

pytestmark = pytest.mark.django_db


def test_admin_dashboard_and_product_image_preview(client):
    user = User.objects.create_superuser(email="admin@example.com", password="StrongPass9!")
    client.force_login(user)
    category = CategoryFactory(name="Everyday wear")
    product = ProductFactory(category=category, name="Cotton shirt")
    ProductVariantFactory(product=product, stock_quantity=7)
    out_of_stock_product = ProductFactory(category=category, name="Out of stock shirt")
    ProductVariantFactory(product=out_of_stock_product, stock_quantity=0)

    dashboard_response = client.get(reverse("admin:index"))
    assert dashboard_response.status_code == 200
    assert b"Store overview" in dashboard_response.content
    assert b"Available units" in dashboard_response.content
    assert b"Categories" in dashboard_response.content

    list_response = client.get(reverse("admin:catalog_product_changelist"))
    assert list_response.status_code == 200
    assert b"Cotton shirt" in list_response.content
    assert b">7<" in list_response.content

    out_of_stock_response = client.get(
        reverse("admin:catalog_product_changelist"), {"stock_status": "out_of_stock"}
    )
    assert b"Out of stock shirt" in out_of_stock_response.content
    assert b"Cotton shirt" not in out_of_stock_response.content

    change_response = client.get(reverse("admin:catalog_product_change", args=[product.pk]))
    assert change_response.status_code == 200
    assert b"Upload an image to show its preview here." in change_response.content
