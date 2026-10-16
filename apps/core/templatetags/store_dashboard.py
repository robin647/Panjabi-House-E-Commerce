from django import template
from django.db.models import PositiveIntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce

from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.models import Order

register = template.Library()


@register.simple_tag(takes_context=True)
def store_dashboard(context):
    request = context.get("request")
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}

    dashboard = {}
    if user.has_perm("catalog.view_product"):
        dashboard["products"] = Product.objects.count()
        dashboard["inventory"] = ProductVariant.objects.filter(is_active=True).aggregate(
            total=Coalesce(Sum("stock_quantity"), Value(0), output_field=PositiveIntegerField())
        )["total"]
        dashboard["out_of_stock"] = (
            Product.objects.annotate(
                _active_stock=Coalesce(
                    Sum("variants__stock_quantity", filter=Q(variants__is_active=True)),
                    Value(0),
                    output_field=PositiveIntegerField(),
                )
            )
            .filter(_active_stock=0)
            .count()
        )
    if user.has_perm("catalog.view_category"):
        dashboard["categories"] = Category.objects.count()
    if user.has_perm("orders.view_order"):
        orders = Order.objects.select_related("user")
        dashboard["orders"] = orders.count()
        dashboard["recent_orders"] = orders.only(
            "id",
            "order_number",
            "user__email",
            "user__first_name",
            "user__last_name",
            "status",
            "payment_status",
            "total",
            "created_at",
        )[:5]
    return dashboard
