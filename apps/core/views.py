from decimal import Decimal

from django.conf import settings
from django.db import connection
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .utils import api_response


class HealthCheckSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    database = serializers.BooleanField()


class HealthCheckView(APIView):
    """GET /api/v1/health/ - liveness + DB connectivity, for load balancers / uptime checks."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses={
            200: OpenApiResponse(HealthCheckSerializer, description="Service is healthy."),
            503: OpenApiResponse(HealthCheckSerializer, description="Database is unreachable."),
        },
        tags=["health"],
    )
    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:  # noqa: BLE001 - deliberately broad: any DB error means "not healthy"
            db_ok = False
        status_code = 200 if db_ok else 503
        return api_response({"status": "ok" if db_ok else "degraded", "database": db_ok}, status=status_code)


class ShopConfigSerializer(serializers.Serializer):
    currency = serializers.CharField()
    delivery_charge_inside_dhaka = serializers.DecimalField(max_digits=12, decimal_places=2)
    delivery_charge_outside_dhaka = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_methods = serializers.ListField(child=serializers.CharField())


class ShopConfigView(APIView):
    """GET /api/v1/config/ - public storefront settings (currency, delivery charges, payment methods)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses={200: OpenApiResponse(ShopConfigSerializer, description="Public shop settings.")},
        tags=["config"],
        description="Lets the storefront show delivery charges before checkout. The server still recomputes "
        "every total at checkout; these values are for display only.",
    )
    def get(self, request):
        cents = Decimal("0.01")
        payload = {
            "currency": settings.DEFAULT_CURRENCY,
            "delivery_charge_inside_dhaka": Decimal(str(settings.DELIVERY_CHARGE_INSIDE_DHAKA)).quantize(cents),
            "delivery_charge_outside_dhaka": Decimal(str(settings.DELIVERY_CHARGE_OUTSIDE_DHAKA)).quantize(cents),
            "payment_methods": ["cod"],
        }
        # Via the serializer so money is emitted as strings like every other endpoint
        # (DRF's raw JSON encoder would turn a bare Decimal into a float).
        return api_response(ShopConfigSerializer(payload).data)


def not_found(request, exception=None):
    """404 handler: JSON (same envelope as every API error) for /api/ paths, Django's page otherwise."""
    if request.path.startswith("/api/"):
        from django.http import JsonResponse

        return JsonResponse({"success": False, "message": "Not found.", "errors": {}, "code": "not_found"}, status=404)
    from django.views.defaults import page_not_found

    return page_not_found(request, exception)
