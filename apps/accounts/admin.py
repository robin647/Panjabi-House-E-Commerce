from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = ["email", "phone_number", "first_name", "last_name", "role", "is_active", "is_staff", "created_at"]
    list_filter = ["role", "is_active", "is_staff", "created_at"]
    search_fields = ["email", "phone_number", "first_name", "last_name", "uuid"]
    readonly_fields = ["uuid", "created_at", "last_login"]
    date_hierarchy = "created_at"
    fieldsets = (
        (None, {"fields": ("email", "phone_number", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        (
            "Role & permissions",
            {
                "fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at")}),
        ("Identity", {"fields": ("uuid",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "phone_number", "role", "password1", "password2"),
            },
        ),
    )
    filter_horizontal = ["groups", "user_permissions"]
