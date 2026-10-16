"""
Aggregates every app's API routes under /api/v1/ and /api/v1/admin/.
Each app owns its own urls.py; this module just mounts them, so adding a new
app in a later phase means adding one line here.
"""

from django.urls import include, path

from apps.accounts.api.customer.urls import profile_urlpatterns
from apps.orders.api.customer.urls import checkout_urlpatterns

urlpatterns = [
    path("", include("apps.core.urls")),
    path("auth/", include("apps.accounts.api.customer.urls")),
    path("profile/", include(profile_urlpatterns)),
    path("", include("apps.catalog.api.customer.urls")),
    path("addresses/", include("apps.customers.api.customer.urls")),
    path("cart/", include("apps.cart.api.customer.urls")),
    path("checkout/", include(checkout_urlpatterns)),
    path("orders/", include("apps.orders.api.customer.urls")),
    # Phase 6+: payments/, coupons/, wishlist/, reviews/ are added here.
]

admin_api_urlpatterns = [
    # Phase 8: path("products/", include("apps.catalog.api.admin.urls")), etc.
    # Django Admin (/admin/) already covers products/categories/orders/users
    # management for this stage - see README "Demo frontend & Admin UI".
]
