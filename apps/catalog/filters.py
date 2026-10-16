import django_filters as filters

from .models import Product


class ProductFilter(filters.FilterSet):
    category = filters.CharFilter(field_name="category__slug")
    min_price = filters.NumberFilter(field_name="sort_price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="sort_price", lookup_expr="lte")
    featured = filters.BooleanFilter(field_name="is_featured")
    new_collection = filters.BooleanFilter(field_name="is_new_collection")
    on_sale = filters.BooleanFilter(method="filter_on_sale")

    class Meta:
        model = Product
        fields = ["category", "min_price", "max_price", "featured", "new_collection", "on_sale"]

    def filter_on_sale(self, queryset, name, value):
        return queryset.filter(sale_price__isnull=not value) if value else queryset
