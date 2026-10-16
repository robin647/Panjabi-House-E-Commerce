from django.contrib import admin

from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["full_name", "user", "city", "phone", "is_default", "created_at"]
    list_filter = ["is_default", "city"]
    search_fields = ["full_name", "phone", "user__email", "user__phone_number"]
    autocomplete_fields = ["user"]
