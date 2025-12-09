from django.contrib import admin
from api.models import (
    User,
    UserProfile,
    Role,
    Permission,
    AuditLog,
    RefreshTokenBlacklist,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "username",
        "email",
        "role",
        "is_verified",
        "is_active",
        "created_at",
    ]
    list_filter = ["role", "is_verified", "is_active", "created_at"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Account Information",
            {"fields": ("user_id", "username", "email", "password")},
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                    "avatar_url",
                    "bio",
                )
            },
        ),
        (
            "Role & Permissions",
            {
                "fields": (
                    "role",
                    "is_verified",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Dates", {"fields": ("created_at", "updated_at", "last_login_at")}),
    )

    readonly_fields = ["user_id", "created_at", "updated_at", "last_login_at"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "organization",
        "department",
        "preferred_language",
        "created_at",
    ]
    list_filter = ["preferred_language", "notifications_enabled", "email_notifications"]
    search_fields = ["user__username", "organization", "department"]
    readonly_fields = ["profile_id", "created_at", "updated_at"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name", "description"]
    filter_horizontal = ["permissions"]
    readonly_fields = ["role_id", "created_at", "updated_at"]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "resource", "action"]
    list_filter = ["resource", "action"]
    search_fields = ["name", "code", "resource"]
    readonly_fields = ["permission_id"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["user", "action", "resource", "status", "created_at"]
    list_filter = ["action", "status", "resource", "created_at"]
    search_fields = ["user__username", "action", "resource"]
    readonly_fields = ["log_id", "created_at"]
    ordering = ["-created_at"]


@admin.register(RefreshTokenBlacklist)
class RefreshTokenBlacklistAdmin(admin.ModelAdmin):
    list_display = ["user", "blacklisted_at", "expires_at"]
    list_filter = ["blacklisted_at", "expires_at"]
    search_fields = ["user__username"]
    readonly_fields = ["token_id", "blacklisted_at"]
    ordering = ["-blacklisted_at"]
