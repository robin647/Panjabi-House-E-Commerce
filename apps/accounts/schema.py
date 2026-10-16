"""
drf-spectacular extensions so the generated OpenAPI schema correctly
describes our custom JWT authenticator (bearer token, same wire format as
SimpleJWT's own class - we only override get_user()).
"""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class VersionedJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.VersionedJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
