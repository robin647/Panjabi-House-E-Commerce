from rest_framework import serializers

from apps.customers.models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "uuid",
            "full_name",
            "phone",
            "address_line",
            "city",
            "postal_code",
            "delivery_instructions",
            "is_default",
        ]
        read_only_fields = ["uuid"]
