import uuid

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """Public, non-guessable identifier exposed by APIs (the integer pk stays internal)."""

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    class Meta:
        abstract = True


class IdempotencyRecord(TimeStampedModel):
    """
    Backs idempotent writes (currently: checkout). A client sends an
    ``Idempotency-Key`` header; repeating the same key for the same user
    returns the original stored response instead of re-running the
    operation, which prevents duplicate orders from retried requests.
    """

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="idempotency_records")
    key = models.CharField(max_length=255)
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField()
    response_body = models.JSONField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "key"], name="unique_idempotency_key_per_user")]
