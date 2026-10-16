from django.db import models

from apps.core.models import BaseModel


class Cart(BaseModel):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="cart")

    def __str__(self) -> str:
        return f"Cart({self.user})"


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["cart", "variant"], name="unique_variant_per_cart")]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.variant}"
