from django.core.exceptions import ImproperlyConfigured

from .base import *
from .base import (
    ALLOWED_HOSTS,
    CORS_ALLOWED_ORIGINS,
    DEBUG,
    LOG_LEVEL,
    SECRET_KEY,
    build_logging,
    env,
)

# ---- Fail fast on unsafe configuration -------------------------------------
if DEBUG:
    raise ImproperlyConfigured("DEBUG must be False in production.")
if not SECRET_KEY or len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure"):
    raise ImproperlyConfigured("SECRET_KEY must be set to a strong random value (>= 50 chars).")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must list your real domain(s); '*' is not allowed.")
if not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must list the frontend origin(s).")

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
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
