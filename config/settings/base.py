"""
Base settings shared by every environment.

Everything sensitive or environment-specific is read from environment
variables (optionally loaded from a local ``.env`` file). Nothing secret is
hardcoded here.
"""

from datetime import timedelta
from pathlib import Path

import environ
from corsheaders.defaults import default_headers
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(str(_env_file))

# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
ADMIN_URL = env("ADMIN_URL", default="admin/")  # change in production
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")
# Compiled React storefront (`npm run build` in frontend/), served by apps.core.frontend
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # pg_trgm / GIN search in later phases
    # Third party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "axes",
    # Local
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.customers",
    "apps.cart",
    "apps.orders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "apps.core.middleware.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------------------------------
# Database - PostgreSQL only (no SQLite, ever)
# --------------------------------------------------------------------------
if env("DATABASE_URL", default=""):
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", default="own_ecommerce_db"),
            "USER": env("DB_USER", default="shop"),
            "PASSWORD": env("DB_PASSWORD", default="shop-admin"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="5433"),
        }
    }
if "postgresql" not in DATABASES["default"]["ENGINE"]:
    raise ImproperlyConfigured("This project requires PostgreSQL. Check DATABASE_URL / DB_* settings.")
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
# Transactions are explicit (services use transaction.atomic + select_for_update).
DATABASES["default"]["ATOMIC_REQUESTS"] = False

# --------------------------------------------------------------------------
# Cache (Redis when REDIS_URL is set, otherwise per-process memory for dev)
# --------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="")
if REDIS_URL:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}}
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # must be first
    "apps.accounts.backends.IdentifierBackend",  # email OR phone
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",  # fallback / legacy verify
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT_SECONDS", default=3600)

# Brute-force protection (django-axes): lock per (IP + identifier)
AXES_ENABLED = env.bool("AXES_ENABLED", default=True)
AXES_FAILURE_LIMIT = env.int("AXES_FAILURE_LIMIT", default=5)
AXES_COOLOFF_TIME = timedelta(minutes=env.int("AXES_COOLOFF_MINUTES", default=15))
AXES_LOCKOUT_PARAMETERS = [["ip_address", "username"]]
AXES_RESET_ON_SUCCESS = True
AXES_IPWARE_PROXY_COUNT = env.int("AXES_PROXY_COUNT", default=0) or None
AXES_IPWARE_META_PRECEDENCE_ORDER = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"]

# --------------------------------------------------------------------------
# Django REST Framework
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("apps.accounts.authentication.VersionedJWTAuthentication",),
    # Secure by default: every view is private unless it opts out with AllowAny.
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("apps.core.renderers.EnvelopeJSONRenderer",),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ),
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ("v1",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "240/min",
        "login": "10/min",
        "register": "5/min",
        "password_reset": "5/hour",
        "checkout": "10/min",
    },
    "NUM_PROXIES": env.int("NUM_PROXIES", default=0) or None,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,  # we do this ourselves in the login service
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "uuid",  # tokens never expose sequential ids
    "USER_ID_CLAIM": "user_id",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Clothing E-commerce API",
    "DESCRIPTION": "REST API for the customer website and the admin dashboard.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
    "COMPONENT_SPLIT_REQUEST": True,
    # Order.status is serialized by both OrderListSerializer and
    # OrderDetailSerializer; without this, drf-spectacular generates two
    # differently-auto-named enum components for the same underlying
    # OrderStatus choices and warns about the naming collision. This pins
    # both to one clean, stable name instead.
    "ENUM_NAME_OVERRIDES": {
        "OrderStatusEnum": "apps.orders.models.OrderStatus.choices",
    },
    "SERVE_PERMISSIONS": (
        ["rest_framework.permissions.AllowAny"]
        if env.bool("API_DOCS_PUBLIC", default=True)
        else ["rest_framework.permissions.IsAdminUser"]
    ),
}

# --------------------------------------------------------------------------
# CORS / CSRF
# --------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = env.bool("CORS_ALLOW_CREDENTIALS", default=False)
CORS_ALLOW_HEADERS = [*default_headers, "idempotency-key", "x-request-id"]
CORS_EXPOSE_HEADERS = ["x-request-id", "retry-after"]
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# --------------------------------------------------------------------------
# I18N / time
# --------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static / media (storage backend is swappable via STORAGES without code changes)
# --------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Use plain static storage locally to avoid manifest/hash issues during development.
    # Production can use WhiteNoise's compressed manifest storage.
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

# --------------------------------------------------------------------------
# Email
# --------------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Shop <no-reply@example.com>")

# --------------------------------------------------------------------------
# Celery
# --------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL or "redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_TIMEZONE = TIME_ZONE

# --------------------------------------------------------------------------
# Logging (JSON in production, readable text in dev - see dev.py / prod.py)
# --------------------------------------------------------------------------
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
LOG_FORMAT = "text"


def build_logging(fmt: str, level: str) -> dict:
    formatter = (
        "apps.core.logging_utils.JsonFormatter" if fmt == "json" else "apps.core.logging_utils.RedactingFormatter"
    )
    app_logger = {"handlers": ["console"], "level": level, "propagate": False}
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": "apps.core.logging_utils.RequestIDFilter"}},
        "formatters": {
            "default": {
                "()": formatter,
                "fmt": "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s",
            }
        },
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default", "filters": ["request_id"]}},
        "root": {"handlers": ["console"], "level": level},
        "loggers": {
            "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            # Domain loggers, so ops can filter/route them separately
            "shop": app_logger,
            "axes": app_logger,
        },
    }


LOGGING = build_logging(LOG_FORMAT, LOG_LEVEL)

# --------------------------------------------------------------------------
# Baseline security headers (HTTPS-specific ones live in prod.py)
# --------------------------------------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --------------------------------------------------------------------------
# Business defaults used by later phases
# --------------------------------------------------------------------------
DEFAULT_CURRENCY = "BDT"
DELIVERY_CHARGE_INSIDE_DHAKA = env.float("DELIVERY_CHARGE_INSIDE_DHAKA", default=60.0)
DELIVERY_CHARGE_OUTSIDE_DHAKA = env.float("DELIVERY_CHARGE_OUTSIDE_DHAKA", default=120.0)
