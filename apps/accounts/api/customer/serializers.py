from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.validators import (
    parse_identifier,
    validate_identifier_available,
    validate_strong_password,
)

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["email", "phone_number", "first_name", "last_name", "password", "password_confirm"]
        extra_kwargs = {"email": {"required": False}, "phone_number": {"required": False}}

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        validate_identifier_available(attrs.get("email"), attrs.get("phone_number"))
        validate_strong_password(attrs["password"])
        return attrs


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Email address or phone number.")
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        attrs["identifier_fields"] = parse_identifier(attrs["identifier"])
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    def validate_new_password(self, value):
        return validate_strong_password(value, user=self.context["request"].user)


class ForgotPasswordSerializer(serializers.Serializer):
    identifier = serializers.CharField(help_text="Email address or phone number.")

    def validate(self, attrs):
        attrs["identifier_fields"] = parse_identifier(attrs["identifier"])
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    def validate_new_password(self, value):
        return validate_strong_password(value)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["uuid", "email", "phone_number", "first_name", "last_name", "role", "created_at"]
        read_only_fields = ["uuid", "email", "phone_number", "role", "created_at"]
