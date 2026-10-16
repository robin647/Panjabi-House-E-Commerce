from django.urls import path

from .views import HealthCheckView, ShopConfigView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("config/", ShopConfigView.as_view(), name="shop-config"),
]
