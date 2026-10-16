from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from apps.core.utils import looks_like_email, normalize_email, normalize_phone

User = get_user_model()


class IdentifierBackend(ModelBackend):
    """
    Authenticate with either an email address or a Bangladeshi phone number.

    Accepts the identifier three ways, so it works both with Django's own
    ``username`` convention and with the already-normalised, already-typed
    fields the accounts services pass in:
      - ``identifier="jamal@example.com"`` (raw, detected as email or phone)
      - ``email="jamal@example.com"``
      - ``phone_number="+8801..."``
    """

    def authenticate(
        self, request, username=None, password=None, identifier=None, email=None, phone_number=None, **kwargs
    ):
        if not password:
            return None

        if email:
            lookup = {"email": normalize_email(email)}
        elif phone_number:
            lookup = {"phone_number": phone_number}
        else:
            raw = identifier or username
            if not raw:
                return None
            if looks_like_email(raw):
                lookup = {"email": normalize_email(raw)}
            else:
                try:
                    lookup = {"phone_number": normalize_phone(raw)}
                except ValueError:
                    return None

        try:
            user = User.objects.get(**lookup)
        except User.DoesNotExist:
            User().set_password(password)  # constant-time-ish: avoid a fast "no such user" path
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
