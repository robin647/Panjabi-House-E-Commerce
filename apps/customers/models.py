from django.db import models, transaction

from apps.core.models import BaseModel


class Address(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address_line = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    delivery_instructions = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        indexes = [models.Index(fields=["user", "is_default"])]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.city}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_default:
                Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
            elif not Address.objects.filter(user=self.user).exclude(pk=self.pk).exists():
                # The user's first address is always the default, so checkout
                # always has one to fall back to.
                self.is_default = True
            super().save(*args, **kwargs)
