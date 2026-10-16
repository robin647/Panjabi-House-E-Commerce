"""
Business logic for registration, login, password change/reset and profile
updates. Views stay thin and only translate HTTP <-> these functions.
"""

import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.utils import mask_identifier

User = get_user_model()
logger = logging.getLogger("shop.accounts")


def issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


@transaction.atomic
def register_customer(*, email, phone_number, password, first_name="", last_name=""):
    user = User.objects.create_user(
        email=email,
        phone_number=phone_number,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )
    logger.info("New customer registered: %s", mask_identifier(user.email or user.phone_number))
    return user


def login_user(*, identifier_fields: dict, password: str, request=None):
    user = authenticate(request=request, password=password, **identifier_fields)
    if user is None:
        logger.warning("Failed login attempt for %s", mask_identifier(next(iter(identifier_fields.values()), "")))
        raise AuthenticationFailed("Invalid credentials.")
    if not user.is_active:
        raise AuthenticationFailed("This account has been deactivated.")

    from django.utils import timezone

    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    logger.info("User logged in: %s", mask_identifier(user.email or user.phone_number))
    return user


def logout_user(refresh_token: str) -> None:
    from rest_framework_simplejwt.tokens import TokenError

    try:
        RefreshToken(refresh_token).blacklist()
    except TokenError:
        # Already invalid/expired/blacklisted - logout is idempotent from the client's point of view.
        pass


@transaction.atomic
def change_password(*, user, old_password: str, new_password: str) -> None:
    if not user.check_password(old_password):
        from rest_framework.exceptions import ValidationError

        raise ValidationError({"old_password": "Current password is incorrect."})
    user.set_password(new_password)
    user.save(update_fields=["password"])
    _blacklist_all_outstanding_tokens(user)
    logger.info("Password changed for user %s", user.uuid)


def _blacklist_all_outstanding_tokens(user) -> None:
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )

    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def request_password_reset(*, email: str | None, phone_number: str | None) -> None:
    """
    Always returns None without revealing whether the account exists.
    Email delivery is the implemented channel; SMS is wired through the
    notifications service in a later phase.
    """
    user = None
    if email:
        user = User.objects.filter(email=email).first()
    elif phone_number:
        user = User.objects.filter(phone_number=phone_number).first()

    if user is None or not user.is_active:
        logger.info("Password reset requested for unknown/inactive identifier")
        return

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"

    send_mail(
        subject="Reset your password",
        message=f"Use this link to reset your password: {reset_link}\nThis link expires soon and can be used once.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email] if user.email else [],
        fail_silently=True,
    )
    logger.info("Password reset email dispatched for user %s", user.uuid)


@transaction.atomic
def confirm_password_reset(*, uidb64: str, token: str, new_password: str) -> None:
    from rest_framework.exceptions import ValidationError

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
        raise ValidationError({"token": "This reset link is invalid."}) from exc

    if not default_token_generator.check_token(user, token):
        raise ValidationError({"token": "This reset link is invalid or has expired."})

    user.set_password(new_password)
    user.save(update_fields=["password"])
    _blacklist_all_outstanding_tokens(user)
    logger.info("Password reset completed for user %s", user.uuid)
