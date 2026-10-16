from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .base import *
from .base import (
    ALLOWED_HOSTS,
    CORS_ALLOWED_ORIGINS,
    CSRF_TRUSTED_ORIGINS,
    DEBUG,
    DATABASES,
    FRONTEND_URL,
    LOG_LEVEL,
    SECRET_KEY,
    build_logging,
    env,
)

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")

# ---- Fail fast on unsafe configuration -------------------------------------
if DEBUG:
    raise ImproperlyConfigured("DEBUG must be False in production.")
if not SECRET_KEY or len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure"):
    raise ImproperlyConfigured("SECRET_KEY must be set to a strong random value (>= 50 chars).")
if not env("DATABASE_URL", default=""):
    raise ImproperlyConfigured("DATABASE_URL must be set to the production PostgreSQL connection string.")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must list your real domain(s); '*' is not allowed.")
if not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must list the frontend origin(s).")
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS must list the trusted HTTPS origin(s).")

for setting_name, origins in (
    ("FRONTEND_URL", [FRONTEND_URL]),
    ("CORS_ALLOWED_ORIGINS", CORS_ALLOWED_ORIGINS),
    ("CSRF_TRUSTED_ORIGINS", CSRF_TRUSTED_ORIGINS),
):
    for origin in origins:
        parsed = urlsplit(origin)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ImproperlyConfigured(f"{setting_name} must contain full HTTPS origins in production.")

# Render PostgreSQL and other hosted PostgreSQL services require TLS in production.
DATABASES["default"].setdefault("OPTIONS", {})["sslmode"] = "require"
if "-pooler" in DATABASES["default"].get("HOST", ""):
    DATABASES["default"].setdefault("OPTIONS", {})["DISABLE_SERVER_SIDE_CURSORS"] = True

if EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
    raise ImproperlyConfigured("Configure a production SMTP or transactional email backend.")
if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend" and not EMAIL_HOST:
    raise ImproperlyConfigured("EMAIL_HOST is required for the production SMTP backend.")

# ---- HTTPS / cookies ---------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # behind Render/Railway/nginx/ALB
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ---- Ops -----------------------------------------------------------------------
LOGGING = build_logging("json", LOG_LEVEL)
SERVE_MEDIA = env.bool("SERVE_MEDIA", default=True)
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))
