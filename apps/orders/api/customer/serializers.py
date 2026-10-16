from rest_framework import serializers

from apps.orders.models import Order, OrderItem


class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.UUIDField()
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500, default="")


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product_name", "sku", "variant_label", "unit_price", "quantity", "subtotal"]


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["uuid", "order_number", "status", "payment_status", "payment_method", "total", "created_at"]


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "uuid",
            "order_number",
            "status",
            "payment_status",
            "payment_method",
            "subtotal",
            "delivery_charge",
            "total",
            "shipping_full_name",
            "shipping_phone",
            "shipping_address_line",
            "shipping_city",
            "shipping_postal_code",
            "notes",
            "items",
            "created_at",
        ]
