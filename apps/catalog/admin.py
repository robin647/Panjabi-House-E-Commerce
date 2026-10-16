from django.contrib import admin
from django.db.models import Count, PositiveIntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils.html import format_html

from .models import Category, Product, ProductVariant


class StockStatusFilter(admin.SimpleListFilter):
    title = "stock status"
    parameter_name = "stock_status"

    def lookups(self, request, model_admin):
        return [("in_stock", "In stock"), ("out_of_stock", "Out of stock")]

    def queryset(self, request, queryset):
        if self.value() == "in_stock":
            return queryset.filter(_admin_total_stock__gt=0)
        if self.value() == "out_of_stock":
            return queryset.filter(_admin_total_stock=0)
        return queryset


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ["size", "color", "sku", "stock_quantity", "is_active"]
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "display_order", "product_count"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["display_order", "name"]
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_product_count=Count("products"))

    @admin.display(description="Products", ordering="_product_count")
    def product_count(self, obj):
        return obj._product_count


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "image_thumbnail",
        "name",
        "sku",
        "category",
        "regular_price",
        "sale_price",
        "total_stock_display",
        "is_active",
        "is_published",
        "is_featured",
    ]
    list_filter = ["category", "is_active", "is_published", "is_featured", "is_new_collection", StockStatusFilter]
    search_fields = ["name", "sku", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["category"]
    readonly_fields = ["image_preview", "uuid", "created_at", "updated_at"]
    inlines = [ProductVariantInline]
    date_hierarchy = "created_at"
    fieldsets = (
        ("Basic information", {"fields": ("name", "slug", "sku", "category")}),
        ("Product image", {"fields": ("image", "image_preview")}),
        ("Description", {"fields": ("short_description", "description")}),
        ("Pricing", {"fields": ("regular_price", "sale_price", "cost_price")}),
        ("Store visibility", {"fields": ("is_active", "is_published", "is_featured", "is_new_collection")}),
        ("Identity", {"fields": ("uuid", "created_at", "updated_at")}),
    )
    list_select_related = ["category"]
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _admin_total_stock=Coalesce(
                Sum("variants__stock_quantity", filter=Q(variants__is_active=True)),
                Value(0),
                output_field=PositiveIntegerField(),
            )
        )

    @admin.display(description="Image", empty_value="No image")
    def image_thumbnail(self, obj):
        if not obj.image:
            return "No image"
        return format_html('<img class="store-product-thumbnail" src="{}" alt="{}">', obj.image.url, obj.name)

    @admin.display(description="Image preview")
    def image_preview(self, obj):
        if not obj or not obj.image:
            return "Upload an image to show its preview here."
        return format_html('<img class="store-product-preview" src="{}" alt="{}">', obj.image.url, obj.name)

    @admin.display(description="Stock")
    def total_stock_display(self, obj):
        return obj._admin_total_stock


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """
    Registered mainly so other admins (e.g. CartItemInline) can use
    autocomplete_fields=["variant"] - Django requires the target model to
    have its own registered ModelAdmin with search_fields for that to work.
    """

    list_display = ["sku", "product", "size", "color", "stock_quantity", "is_active"]
    list_filter = ["is_active", "size"]
    search_fields = ["sku", "product__name", "product__sku"]
    autocomplete_fields = ["product"]


admin.site.site_header = "Clothing Shop Admin"
admin.site.site_title = "Clothing Shop Admin"
admin.site.index_title = "Store management"
admin.site.index_template = "admin/store_index.html"
