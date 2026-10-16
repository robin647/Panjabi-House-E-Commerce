from .models import Cart


def get_or_create_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def cart_with_items(user) -> Cart:
    cart = get_or_create_cart(user)
    cart._prefetched_items = list(
        cart.items.select_related("variant__product", "variant__product__category").order_by("id")
    )
    return cart


def compute_totals(cart: Cart) -> dict:
    items = getattr(cart, "_prefetched_items", None)
    if items is None:
        items = list(cart.items.select_related("variant__product"))
    subtotal = sum((item.variant.product.effective_price * item.quantity for item in items), start=0)
    return {"items": items, "subtotal": subtotal, "item_count": sum(i.quantity for i in items)}
