"""
Idempotency helper for POST endpoints that must never double-execute on
retry (checkout being the motivating case - see apps.core.models.IdempotencyRecord).
"""

import hashlib
import json

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from .models import IdempotencyRecord


def _hash_body(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def idempotent_call(*, user, key: str, request_data: dict, compute):
    """
    Runs ``compute()`` (which must return (status_code, response_data)) at
    most once per (user, key). A retried request with the SAME key and the
    SAME body transparently replays the stored response. The same key with a
    DIFFERENT body is rejected (409) rather than silently ignored, since that
    almost certainly indicates a client bug.
    """
    request_hash = _hash_body(request_data)
    existing = IdempotencyRecord.objects.filter(user=user, key=key).first()
    if existing:
        if existing.request_hash != request_hash:
            raise ValidationError({"idempotency_key": "This key was already used with a different request body."})
        return existing.response_status, existing.response_body

    try:
        with transaction.atomic():
            status_code, response_data = compute()
            IdempotencyRecord.objects.create(
                user=user,
                key=key,
                request_hash=request_hash,
                response_status=status_code,
                response_body=response_data,
            )
            return status_code, response_data
    except IntegrityError:
        # Lost a race against a concurrent identical request; the other one
        # already wrote the record, so replay what IT produced.
        existing = IdempotencyRecord.objects.get(user=user, key=key)
        return existing.response_status, existing.response_body
