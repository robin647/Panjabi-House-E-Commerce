from .models import Product


def published_products():
    return Product.objects.published().with_main_price().select_related("category").prefetch_related("variants")


def product_by_slug_or_404(slug: str):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(
        Product.objects.published().select_related("category").prefetch_related("variants"), slug=slug
    )
