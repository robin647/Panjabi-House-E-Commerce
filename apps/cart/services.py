"""
Cart business logic. Prices are NEVER trusted from the client and are never
stored on the cart - every total is computed live from the current product
price, here and again at checkout.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.catalog.models import ProductVariant

from .models import CartItem
from .selectors import get_or_create_cart


def _get_sellable_variant(variant_uuid: str) -> ProductVariant:
    try:
        variant = ProductVariant.objects.select_related("product").get(uuid=variant_uuid)
    except (ProductVariant.DoesNotExist, ValueError, DjangoValidationError) as exc:
        raise ValidationError({"variant_id": "This product variant does not exist."}) from exc
    if not variant.is_active or not variant.product.is_active or not variant.product.is_published:
        raise ValidationError({"variant_id": "This product variant is not currently available."})
    return variant


@transaction.atomic
def add_item(*, user, variant_uuid: str, quantity: int):
    if quantity < 1:
        raise ValidationError({"quantity": "Quantity must be at least 1."})
    variant = _get_sellable_variant(variant_uuid)
    cart = get_or_create_cart(user)
    # NOTE: get_or_create(cart=cart, ...) explicitly, not
    # cart.items.select_for_update().get_or_create(...) - chaining
    # select_for_update() on the related manager returns a plain QuerySet,
    # which loses the related manager's automatic `cart=cart` injection on
    # creation and would insert a NULL cart_id.
    item, created = CartItem.objects.select_for_update().get_or_create(
        cart=cart, variant=variant, defaults={"quantity": 0}
    )
    new_quantity = item.quantity + quantity
    if new_quantity > variant.stock_quantity:
        raise ValidationError({"quantity": f"Only {variant.stock_quantity} in stock for this option."})
    item.quantity = new_quantity
    item.save(update_fields=["quantity"])
    return cart


@transaction.atomic
def update_item_quantity(*, user, item_uuid: str, quantity: int):
    if quantity < 1:
        raise ValidationError({"quantity": "Quantity must be at least 1. Use remove to delete the item."})
    cart = get_or_create_cart(user)
    item = cart.items.select_for_update().select_related("variant").filter(uuid=item_uuid).first()
    if item is None:
        raise ValidationError({"item": "This cart item does not exist."})
    if quantity > item.variant.stock_quantity:
        raise ValidationError({"quantity": f"Only {item.variant.stock_quantity} in stock for this option."})
    item.quantity = quantity
    item.save(update_fields=["quantity"])
    return cart


def remove_item(*, user, item_uuid: str):
    cart = get_or_create_cart(user)
    deleted, _ = cart.items.filter(uuid=item_uuid).delete()
    if not deleted:
        raise ValidationError({"item": "This cart item does not exist."})
    return cart


def clear_cart(*, user):
    cart = get_or_create_cart(user)
    cart.items.all().delete()
    return cart
