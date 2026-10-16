from django.core.management.utils import get_random_secret_key

from .base import *
from .base import REST_FRAMEWORK, SIMPLE_JWT, env

# Random per-run key: no secret is committed, and tests need no .env file.
SECRET_KEY = env("SECRET_KEY", default=get_random_secret_key())
SIMPLE_JWT = {**SIMPLE_JWT, "SIGNING_KEY": SECRET_KEY}
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # fast; tests only
CELERY_TASK_ALWAYS_EAGER = True
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
AXES_ENABLED = False  # enabled explicitly in the lockout test
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {k: "10000/min" for k in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]},
}
LOGGING_CONFIG = None  # keep pytest's log capture
