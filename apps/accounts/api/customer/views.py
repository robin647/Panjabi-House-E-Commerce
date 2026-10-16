from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.core.throttles import (
    LoginRateThrottle,
    PasswordResetRateThrottle,
    RegisterRateThrottle,
)
from apps.core.utils import api_response

from ... import services
from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
)

_OK = OpenApiResponse(description="Success.")
_ERR = OpenApiResponse(description="Validation or business-rule error.")


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RegisterRateThrottle]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: OpenApiResponse(description="Account created; tokens issued."), 400: _ERR},
        tags=["auth"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        user = services.register_customer(
            email=data.get("email"),
            phone_number=data.get("phone_number"),
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
        )
        tokens = services.issue_tokens(user)
        return api_response(
            {"user": ProfileSerializer(user).data, "tokens": tokens},
            message="Account created successfully.",
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
        request=LoginSerializer,
        responses={200: OpenApiResponse(description="Login successful; tokens issued."), 401: _ERR},
        tags=["auth"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.login_user(
            identifier_fields=serializer.validated_data["identifier_fields"],
            password=serializer.validated_data["password"],
            request=request,
        )
        tokens = services.issue_tokens(user)
        return api_response({"user": ProfileSerializer(user).data, "tokens": tokens}, message="Login successful.")


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={200: _OK, 401: _ERR},
        tags=["auth"],
        description="Blacklists the given refresh token. Requires a valid access token.",
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.logout_user(serializer.validated_data["refresh"])
        return api_response(None, message="Logged out successfully.")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={200: _OK, 400: _ERR},
        tags=["auth"],
        description="Changes the authenticated user's password and blacklists their other outstanding refresh tokens.",
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        services.change_password(
            user=request.user,
            old_password=serializer.validated_data["old_password"],
            new_password=serializer.validated_data["new_password"],
        )
        return api_response(None, message="Password changed successfully. Please log in again on other devices.")


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={200: _OK},
        tags=["auth"],
        description="Always returns 200 with a generic message, whether or not the identifier is registered, "
        "to avoid leaking account existence. Sends a one-time reset link by email when the account exists.",
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.validated_data["identifier_fields"]
        services.request_password_reset(email=fields.get("email"), phone_number=fields.get("phone_number"))
        return api_response(None, message="If an account exists for that identifier, a reset link has been sent.")


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [PasswordResetRateThrottle]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={200: _OK, 400: _ERR},
        tags=["auth"],
        description="Completes a password reset using the uid/token pair emailed by /auth/forgot-password/. "
        "The token is single-use and expires after PASSWORD_RESET_TIMEOUT_SECONDS.",
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.confirm_password_reset(
            uidb64=serializer.validated_data["uid"],
            token=serializer.validated_data["token"],
            new_password=serializer.validated_data["new_password"],
        )
        return api_response(None, message="Password has been reset successfully.")


class ProfileView(RetrieveUpdateAPIView):
    """GET/PATCH the authenticated user's own profile. uuid/email/phone/role/created_at are read-only here."""

    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user
