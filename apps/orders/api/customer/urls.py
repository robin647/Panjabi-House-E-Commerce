from django.urls import path

from . import views

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path("<uuid:uuid>/", views.OrderDetailView.as_view(), name="order-detail"),
]

checkout_urlpatterns = [
    path("", views.CheckoutView.as_view(), name="checkout"),
]
