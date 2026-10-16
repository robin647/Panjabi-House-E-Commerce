from rest_framework_simplejwt.authentication import JWTAuthentication


class VersionedJWTAuthentication(JWTAuthentication):
    """
    Project hook point for JWT authentication.

    Looking up the user by ``uuid`` (configured via SIMPLE_JWT.USER_ID_FIELD)
    already keeps the database's integer primary key out of tokens. This
    subclass exists so later phases (e.g. rejecting tokens issued before a
    forced-logout timestamp) have one place to extend without touching
    settings or views.
    """

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not user.is_active:
            from rest_framework_simplejwt.exceptions import AuthenticationFailed

            raise AuthenticationFailed("User account is disabled.", code="user_inactive")
        return user
