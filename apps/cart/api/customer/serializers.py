from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.cart.models import CartItem


class CartItemVariantSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    size = serializers.CharField()
    color = serializers.CharField()
    product_name = serializers.CharField(source="product.name")
    product_slug = serializers.CharField(source="product.slug")
    image = serializers.ImageField(source="product.image", allow_null=True)
    stock_quantity = serializers.IntegerField()


class CartItemSerializer(serializers.ModelSerializer):
    variant = CartItemVariantSerializer(read_only=True)
    unit_price = serializers.SerializerMethodField()
    line_subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["uuid", "variant", "quantity", "unit_price", "line_subtotal"]

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_unit_price(self, obj):
        return obj.variant.product.effective_price

    @extend_schema_field(serializers.DecimalField(max_digits=12, decimal_places=2))
    def get_line_subtotal(self, obj):
        return obj.variant.product.effective_price * obj.quantity


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)
