from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.utils import looks_like_email, normalize_email, normalize_phone

User = get_user_model()


def validate_identifier_available(email: str | None, phone_number: str | None) -> None:
    email = normalize_email(email)
    phone_number = normalize_phone(phone_number) if phone_number else None
    if not email and not phone_number:
        raise serializers.ValidationError("Provide an email or a phone number.")
    if email and User.objects.filter(email=email).exists():
        raise serializers.ValidationError({"email": "An account with this email already exists."})
    if phone_number and User.objects.filter(phone_number=phone_number).exists():
        raise serializers.ValidationError({"phone_number": "An account with this phone number already exists."})


def validate_strong_password(password: str, user=None) -> str:
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return password


def parse_identifier(identifier: str) -> dict:
    """Return {'email': ...} or {'phone_number': ...} for the login/reset flows."""
    identifier = (identifier or "").strip()
    if looks_like_email(identifier):
        return {"email": normalize_email(identifier)}
    try:
        return {"phone_number": normalize_phone(identifier)}
    except ValueError as exc:
        raise serializers.ValidationError({"identifier": "Enter a valid email or phone number."}) from exc
