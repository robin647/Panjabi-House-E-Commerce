from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.idempotency import idempotent_call
from apps.core.throttles import CheckoutRateThrottle
from apps.core.utils import api_response
from apps.orders import services
from apps.orders.models import Order

from .serializers import CheckoutSerializer, OrderDetailSerializer, OrderListSerializer


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CheckoutRateThrottle]

    @extend_schema(
        request=CheckoutSerializer,
        responses={
            201: OpenApiResponse(OrderDetailSerializer, description="Order placed."),
            400: OpenApiResponse(description="Validation error."),
        },
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=str,
                location=OpenApiParameter.HEADER,
                required=True,
                description=(
                    "Client-generated key. Retrying the same key returns the "
                    "original order instead of creating a duplicate."
                ),
            )
        ],
        tags=["orders"],
        description="Places a Cash-on-Delivery order from the caller's current cart, using the given saved address. "
        "Stock is locked and verified server-side; prices are recomputed from current product prices, never trusted "
        "from the cart. Requires the Idempotency-Key header.",
    )
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            raise ValidationError({"idempotency_key": "The Idempotency-Key header is required for checkout."})

        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        def compute():
            order = services.checkout(
                user=request.user, address_id=str(data["address_id"]), notes=data.get("notes", "")
            )
            return 201, OrderDetailSerializer(order).data

        status_code, response_data = idempotent_call(
            user=request.user,
            key=idempotency_key,
            request_data={"address_id": str(data["address_id"]), "notes": data.get("notes", "")},
            compute=compute,
        )
        return api_response(response_data, message="Order placed successfully.", status=status_code)


@extend_schema(tags=["orders"])
class OrderListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderListSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user)


@extend_schema(tags=["orders"])
class OrderDetailView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        # Scoped to the caller: another user's order 404s, never 403s.
        return Order.objects.filter(user=self.request.user).prefetch_related("items")
