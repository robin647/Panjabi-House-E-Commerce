from django.core.exceptions import ImproperlyConfigured

from .base import *
from .base import LOG_LEVEL, SECRET_KEY, build_logging, env

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY is not set. Copy .env.example to .env and generate one with: "
        'python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"'
    )

DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]", "testserver"])
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)  # no Redis needed in dev
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://localhost:5173",
        # Common ports for serving the simple static frontend (e.g. `python -m
        # http.server` or VS Code's Live Server) during local development.
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
WHITENOISE_USE_FINDERS = True
SERVE_MEDIA = True
LOGGING = build_logging("text", LOG_LEVEL)
