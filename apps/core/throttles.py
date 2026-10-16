"""
Scoped throttles for sensitive endpoints. Rates themselves live in
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] so ops can tune them via settings
without touching code.
"""

from rest_framework.throttling import ScopedRateThrottle


class LoginRateThrottle(ScopedRateThrottle):
    scope = "login"


class RegisterRateThrottle(ScopedRateThrottle):
    scope = "register"


class PasswordResetRateThrottle(ScopedRateThrottle):
    scope = "password_reset"


class CheckoutRateThrottle(ScopedRateThrottle):
    scope = "checkout"
