from django.urls import path

from . import views

urlpatterns = [
    path("", views.CartView.as_view(), name="cart-detail"),
    path("items/", views.CartItemListCreateView.as_view(), name="cart-item-create"),
    path("items/<uuid:item_uuid>/", views.CartItemDetailView.as_view(), name="cart-item-detail"),
]
