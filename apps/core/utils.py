import re

from rest_framework.response import Response

_BD_MOBILE_RE = re.compile(r"^01[3-9]\d{8}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def looks_like_email(value: str) -> bool:
    return bool(_EMAIL_RE.match((value or "").strip()))


def normalize_email(value: str | None) -> str | None:
    value = (value or "").strip().lower()
    return value or None


def normalize_phone(value: str | None) -> str | None:
    """
    Normalise Bangladeshi mobile numbers to E.164 (``+8801XXXXXXXXX``).

    Accepts 01XXXXXXXXX, 8801XXXXXXXXX, +8801XXXXXXXXX (spaces/dashes ignored).
    Returns None for empty input and raises ValueError for anything else.
    """
    raw = (value or "").strip()
    if not raw:
        return None
    digits = re.sub(r"[\s\-().]", "", raw)
    if digits.startswith("+880"):
        digits = "0" + digits[4:]
    elif digits.startswith("880"):
        digits = "0" + digits[3:]
    if not _BD_MOBILE_RE.match(digits):
        raise ValueError("Enter a valid Bangladeshi mobile number.")
    return "+880" + digits[1:]


def mask_identifier(value: str | None) -> str:
    """Mask an email/phone for logs so we never log full personal data."""
    value = value or ""
    if "@" in value:
        local, _, domain = value.partition("@")
        return f"{local[:1]}***@{domain}"
    return f"{value[:4]}***{value[-2:]}" if len(value) > 6 else "***"


def api_response(data=None, message: str = "Success.", status: int = 200, headers: dict | None = None) -> Response:
    """Success response; the renderer wraps it into the standard envelope."""
    response = Response(data, status=status, headers=headers)
    response.message = message
    return response
