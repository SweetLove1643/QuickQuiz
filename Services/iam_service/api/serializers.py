from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from api.models import User, UserProfile, Role, Permission, AuditLog
import re


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["permission_id", "name", "code", "description", "resource", "action"]
        read_only_fields = ["permission_id"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = [
            "role_id",
            "name",
            "description",
            "permissions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["role_id", "created_at", "updated_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "profile_id",
            "organization",
            "department",
            "location",
            "date_of_birth",
            "preferred_language",
            "notifications_enabled",
            "email_notifications",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["profile_id", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "user_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_display",
            "phone_number",
            "avatar_url",
            "bio",
            "is_verified",
            "is_active",
            "is_staff",
            "profile",
            "created_at",
            "updated_at",
            "last_login_at",
        ]
        read_only_fields = ["user_id", "created_at", "updated_at", "last_login_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "avatar_url",
        ]

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise ValidationError({"password": "Passwords do not match."})

        # Validate password strength
        password = data["password"]
        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                {"password": "Password must contain at least one uppercase letter."}
            )
        if not re.search(r"[a-z]", password):
            raise ValidationError(
                {"password": "Password must contain at least one lowercase letter."}
            )
        if not re.search(r"[0-9]", password):
            raise ValidationError(
                {"password": "Password must contain at least one digit."}
            )

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "avatar_url",
            "bio",
            "role",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, min_length=8
    )

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise ValidationError({"new_password": "Passwords do not match."})

        user = self.context["request"].user
        if not user.check_password(data["old_password"]):
            raise ValidationError({"old_password": "Old password is incorrect."})

        # Validate password strength
        password = data["new_password"]
        if not re.search(r"[A-Z]", password):
            raise ValidationError(
                {"new_password": "Password must contain at least one uppercase letter."}
            )
        if not re.search(r"[a-z]", password):
            raise ValidationError(
                {"new_password": "Password must contain at least one lowercase letter."}
            )
        if not re.search(r"[0-9]", password):
            raise ValidationError(
                {"new_password": "Password must contain at least one digit."}
            )

        return data


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        import logging

        logger = logging.getLogger(__name__)

        username = data["username"]
        password = data["password"]

        logger.info(f"[LoginSerializer] Validating login for username: {username}")

        user = authenticate(username=username, password=password)

        if not user:
            logger.error(
                f"[LoginSerializer] Authentication failed for username: {username}"
            )
            raise ValidationError("Invalid username or password.")
        if not user.is_active:
            logger.warning(f"[LoginSerializer] User {username} is inactive")
            raise ValidationError("User account is disabled.")

        logger.info(f"[LoginSerializer] Validation successful for user: {username}")
        return data


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "log_id",
            "user",
            "username",
            "action",
            "resource",
            "resource_id",
            "ip_address",
            "status",
            "details",
            "created_at",
        ]
        read_only_fields = ["log_id", "created_at"]
