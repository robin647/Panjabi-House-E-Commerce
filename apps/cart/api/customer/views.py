from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.utils import api_response

from ... import services
from ...selectors import cart_with_items, compute_totals
from .serializers import AddCartItemSerializer, CartItemSerializer, UpdateCartItemSerializer


class _CartResponseSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    item_count = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)


_CART_OK = OpenApiResponse(_CartResponseSerializer, description="The caller's current cart.")
_CART_ERR = OpenApiResponse(description="Validation error (e.g. insufficient stock, unavailable variant).")


def _cart_payload(user):
    cart = cart_with_items(user)
    totals = compute_totals(cart)
    return {
        "items": CartItemSerializer(totals["items"], many=True).data,
        "item_count": totals["item_count"],
        "subtotal": totals["subtotal"],
    }


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: _CART_OK}, tags=["cart"], description="Get the caller's current cart.")
    def get(self, request):
        return api_response(_cart_payload(request.user))

    @extend_schema(responses={200: _CART_OK}, tags=["cart"], description="Remove every item from the cart.")
    def delete(self, request):
        services.clear_cart(user=request.user)
        return api_response(_cart_payload(request.user), message="Cart cleared.")


class CartItemListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=AddCartItemSerializer,
        responses={201: _CART_OK, 400: _CART_ERR},
        tags=["cart"],
        description="Add a product variant to the cart. Adding a variant already in the cart increases its quantity.",
    )
    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.add_item(
            user=request.user,
            variant_uuid=str(serializer.validated_data["variant_id"]),
            quantity=serializer.validated_data["quantity"],
        )
        return api_response(_cart_payload(request.user), message="Item added to cart.", status=201)


class CartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=UpdateCartItemSerializer, responses={200: _CART_OK, 400: _CART_ERR}, tags=["cart"],
        description="Set a cart item's quantity.",
    )
    def patch(self, request, item_uuid):
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.update_item_quantity(
            user=request.user, item_uuid=str(item_uuid), quantity=serializer.validated_data["quantity"]
        )
        return api_response(_cart_payload(request.user), message="Cart updated.")

    @extend_schema(responses={200: _CART_OK}, tags=["cart"], description="Remove one item from the cart.")
    def delete(self, request, item_uuid):
        services.remove_item(user=request.user, item_uuid=str(item_uuid))
        return api_response(_cart_payload(request.user), message="Item removed from cart.")
