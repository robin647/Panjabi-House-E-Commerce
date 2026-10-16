from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.catalog.models import Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["uuid", "name", "slug", "description", "display_order"]


class ProductVariantSerializer(serializers.ModelSerializer):
    label = serializers.ReadOnlyField()
    available = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["uuid", "size", "color", "label", "available"]

    @extend_schema_field(serializers.BooleanField())
    def get_available(self, obj):
        return obj.is_active and obj.stock_quantity > 0


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    price = serializers.DecimalField(source="effective_price", max_digits=12, decimal_places=2, read_only=True)
    # IntegerField/BooleanField (not ReadOnlyField/SerializerMethodField) so
    # drf-spectacular can infer the OpenAPI type without a type hint on the
    # underlying @property / method - avoids a schema-generation warning.
    discount_percentage = serializers.IntegerField(read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "uuid",
            "name",
            "slug",
            "short_description",
            "category",
            "category_slug",
            "regular_price",
            "sale_price",
            "price",
            "discount_percentage",
            "image",
            "is_featured",
            "is_new_collection",
            "in_stock",
        ]

    @extend_schema_field(serializers.BooleanField())
    def get_in_stock(self, obj):
        return obj.total_stock > 0


class ProductDetailSerializer(ProductListSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["description", "variants"]
