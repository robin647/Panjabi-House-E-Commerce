from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ["variant"]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "item_count", "created_at"]
    search_fields = ["user__email", "user__phone_number"]
    inlines = [CartItemInline]

    def item_count(self, obj):
        return obj.items.count()
