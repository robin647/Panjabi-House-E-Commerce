from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["variant", "product_name", "sku", "variant_label", "unit_price", "quantity", "subtotal"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "note", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "user", "status", "payment_status", "payment_method", "total", "created_at"]
    list_filter = ["status", "payment_status", "payment_method", "created_at"]
    search_fields = ["order_number", "user__email", "user__phone_number", "shipping_phone"]
    autocomplete_fields = ["user"]
    readonly_fields = [
        "uuid",
        "order_number",
        "user",
        "shipping_full_name",
        "shipping_phone",
        "shipping_address_line",
        "shipping_city",
        "shipping_postal_code",
        "subtotal",
        "delivery_charge",
        "total",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"
    list_select_related = ["user"]
    list_per_page = 25
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    fieldsets = (
        (None, {"fields": ("order_number", "user", "status", "payment_status", "payment_method")}),
        (
            "Shipping",
            {
                "fields": (
                    "shipping_full_name",
                    "shipping_phone",
                    "shipping_address_line",
                    "shipping_city",
                    "shipping_postal_code",
                )
            },
        ),
        ("Totals", {"fields": ("subtotal", "delivery_charge", "total")}),
        ("Other", {"fields": ("notes", "uuid", "created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        """Route status changes through the service so the transition is
        validated and a history row is written, instead of writing the
        field directly."""
        if change:
            original = Order.objects.get(pk=obj.pk)
            if original.status != obj.status:
                from .services import transition_order_status

                transition_order_status(
                    order=original, to_status=obj.status, note=f"Changed via admin by {request.user}"
                )
                return
        super().save_model(request, obj, form, change)
