import logging

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("shop.errors")


class BusinessRuleError(APIException):
    """A valid request that violates a business rule (e.g. out of stock)."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state."
    default_code = "business_rule_violation"


class AccountLockedError(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Too many failed attempts. Please try again later."
    default_code = "account_locked"


def _plain(detail):
    """Convert DRF ErrorDetail structures into plain str / list / dict."""
    if isinstance(detail, dict):
        return {key: _plain(value) for key, value in detail.items()}
    if isinstance(detail, (list, tuple)):
        return [_plain(item) for item in detail]
    return str(detail)


def error_payload(message: str, errors: dict | None = None, code: str = "error") -> dict:
    return {"success": False, "message": message, "errors": errors or {}, "code": code}


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled exception: log everything server-side, reveal nothing to the client.
        view = context.get("view")
        logger.exception("Unhandled exception in %s", view.__class__.__name__ if view else "unknown view")
        return Response(
            error_payload("An unexpected error occurred. Please try again later.", code="server_error"),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data
    if isinstance(exc, ValidationError):
        errors = _plain(data)
        if not isinstance(errors, dict):
            errors = {"non_field_errors": errors if isinstance(errors, list) else [errors]}
        message = "Validation failed."
        code = "validation_error"
    else:
        detail = data.get("detail") if isinstance(data, dict) else None
        message = str(detail) if detail else "Request failed."
        code = getattr(detail, "code", None) or getattr(exc, "default_code", "error")
        errors = {}

    response.data = error_payload(message, errors, str(code))
    # DRF only sends a 401 (vs 403) when the view's authenticators issue a
    # WWW-Authenticate challenge. Login/token endpoints have no authenticators
    # by design, so force the semantically correct 401 here instead.
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
    return response
