import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.core.frontend import serve_frontend

from .api_v1 import admin_api_urlpatterns
from .api_v1 import urlpatterns as api_v1_urlpatterns

handler404 = "apps.core.views.not_found"

_admin_prefix = re.escape(settings.ADMIN_URL.strip("/"))

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/", include((api_v1_urlpatterns, "v1"), namespace="v1")),
    path("api/v1/admin/", include((admin_api_urlpatterns, "v1-admin"), namespace="v1-admin")),
    # API documentation
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif getattr(settings, "SERVE_MEDIA", False):
    from django.views.static import serve

    urlpatterns += [
        re_path(
            rf"^{re.escape(settings.MEDIA_URL.lstrip('/'))}(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]

# React storefront + client-side-routing fallback. MUST stay last. The negative
# lookahead keeps API/admin/media/static typos as real 404s instead of HTML, and
# lets "/admin" (no slash) still get Django's APPEND_SLASH redirect.
urlpatterns += [
    re_path(rf"^(?!api/|media/|static/|{_admin_prefix}(?:/|$))(?P<path>.*)$", serve_frontend, name="frontend"),
]
