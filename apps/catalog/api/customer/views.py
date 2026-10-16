from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from apps.catalog import selectors
from apps.catalog.filters import ProductFilter
from apps.catalog.models import Category

from .serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


@extend_schema(tags=["catalog"])
class CategoryListView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CategorySerializer
    pagination_class = None
    queryset = Category.objects.filter(is_active=True)


@extend_schema(tags=["catalog"])
class ProductListView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ProductListSerializer
    queryset = selectors.published_products()
    filterset_class = ProductFilter
    search_fields = ["name", "sku", "description"]
    ordering_fields = ["sort_price", "created_at", "name"]
    ordering = ["-created_at"]


@extend_schema(tags=["catalog"])
class ProductDetailView(RetrieveAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"
    queryset = selectors.published_products()
