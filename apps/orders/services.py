"""
Checkout and order-status business logic.

Checkout correctness rules enforced here:
  - Prices are recomputed from the current product price, never trusted
    from the client or from stale cart data.
  - Variant rows are locked with select_for_update(), in a fixed order (by
    primary key) across every item in the cart, before stock is checked -
    this prevents two concurrent checkouts from both succeeding against the
    last unit of stock, and the fixed lock order prevents deadlocks between
    two carts that share more than one product.
  - Stock is decremented and the order is created in the same transaction,
    so a failure partway through never leaves stock decremented without an
    order, or an order created without stock decremented.
"""

import random
import string
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.cart.selectors import get_or_create_cart
from apps.catalog.models import ProductVariant
from apps.customers.models import Address

from .models import (
    ALLOWED_TRANSITIONS,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
)


def _generate_order_number() -> str:
    date_part = timezone.now().strftime("%Y%m%d")
    rand_part = "".join(random.choices(string.digits, k=6))
    return f"ORD-{date_part}-{rand_part}"


def _delivery_charge_for(city: str) -> Decimal:
    dhaka_aliases = {"dhaka"}
    # settings values come from env.float() (a plain Python float); Decimal
    # arithmetic refuses to mix with float, so convert once here via str()
    # (never float -> Decimal directly, which would carry float imprecision).
    if (city or "").strip().lower() in dhaka_aliases:
        return Decimal(str(settings.DELIVERY_CHARGE_INSIDE_DHAKA))
    return Decimal(str(settings.DELIVERY_CHARGE_OUTSIDE_DHAKA))


@transaction.atomic
def checkout(*, user, address_id: str, notes: str = "") -> Order:
    try:
        address = Address.objects.get(uuid=address_id, user=user)
    except (Address.DoesNotExist, ValueError):
        raise ValidationError({"address_id": "This address does not exist."})

    cart = get_or_create_cart(user)
    cart_items = list(cart.items.select_related("variant__product").order_by("id"))
    if not cart_items:
        raise ValidationError({"cart": "Your cart is empty."})

    # Lock every affected variant row, in a stable order (by pk), before
    # reading stock - this is what actually prevents overselling under
    # concurrency; without the lock, two simultaneous checkouts could both
    # read "1 in stock" and both proceed.
    variant_ids = sorted({item.variant_id for item in cart_items})
    locked_variants = {
        v.id: v for v in ProductVariant.objects.select_for_update().filter(id__in=variant_ids).order_by("id")
    }

    subtotal = 0
    order_items_data = []
    for item in cart_items:
        variant = locked_variants[item.variant_id]
        if not variant.is_active or not variant.product.is_active or not variant.product.is_published:
            raise ValidationError({"cart": f"{variant.product.name} ({variant.label}) is no longer available."})
        if item.quantity > variant.stock_quantity:
            raise ValidationError(
                {"cart": f"Only {variant.stock_quantity} left of {variant.product.name} ({variant.label})."}
            )
        unit_price = variant.product.effective_price  # current price, not whatever the cart was computed with earlier
        line_subtotal = unit_price * item.quantity
        subtotal += line_subtotal
        order_items_data.append(
            {
                "variant": variant,
                "product_name": variant.product.name,
                "sku": variant.sku,
                "variant_label": variant.label,
                "unit_price": unit_price,
                "quantity": item.quantity,
                "subtotal": line_subtotal,
            }
        )

    delivery_charge = _delivery_charge_for(address.city)
    total = subtotal + delivery_charge

    order = Order.objects.create(
        order_number=_generate_order_number(),
        user=user,
        status=OrderStatus.PENDING,
        subtotal=subtotal,
        delivery_charge=delivery_charge,
        total=total,
        shipping_full_name=address.full_name,
        shipping_phone=address.phone,
        shipping_address_line=address.address_line,
        shipping_city=address.city,
        shipping_postal_code=address.postal_code,
        notes=notes,
    )
    OrderItem.objects.bulk_create([OrderItem(order=order, **data) for data in order_items_data])
    OrderStatusHistory.objects.create(order=order, from_status="", to_status=OrderStatus.PENDING, note="Order placed.")

    for data in order_items_data:
        variant = data["variant"]
        variant.stock_quantity -= data["quantity"]
        variant.save(update_fields=["stock_quantity"])

    cart.items.all().delete()
    return order


@transaction.atomic
def transition_order_status(*, order: Order, to_status: str, note: str = "") -> Order:
    current = order.status
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if to_status not in allowed:
        raise ValidationError({"status": f"Cannot move an order from '{current}' to '{to_status}'."})
    order.status = to_status
    if to_status == OrderStatus.DELIVERED and order.payment_method == "cod":
        order.payment_status = "paid"  # COD is collected on delivery
    order.save(update_fields=["status", "payment_status", "updated_at"])
    OrderStatusHistory.objects.create(order=order, from_status=current, to_status=to_status, note=note)
    return order
