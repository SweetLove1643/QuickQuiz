from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    """Custom User model with additional fields"""

    ROLE_CHOICES = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("admin", "Admin"),
    ]

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def update_last_login(self):
        self.last_login_at = timezone.now()
        self.save(update_fields=["last_login_at"])


class UserProfile(models.Model):
    """Extended user profile information"""

    profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    organization = models.CharField(max_length=255, blank=True, null=True)
    department = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    preferred_language = models.CharField(
        max_length=10, default="en", choices=[("en", "English"), ("vi", "Vietnamese")]
    )
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile of {self.user.username}"


class Role(models.Model):
    """User roles and permissions management"""

    role_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField("Permission", related_name="roles")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Fine-grained permissions"""

    permission_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    resource = models.CharField(max_length=100)  # e.g., 'quiz', 'document', 'user'
    action = models.CharField(
        max_length=50
    )  # e.g., 'create', 'read', 'update', 'delete'
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["resource", "action"]
        unique_together = ["resource", "action"]

    def __str__(self):
        return f"{self.resource}:{self.action}"


class AuditLog(models.Model):
    """Log all user activities for security and auditing"""

    ACTION_CHOICES = [
        ("login", "Login"),
        ("logout", "Logout"),
        ("create_user", "Create User"),
        ("update_user", "Update User"),
        ("delete_user", "Delete User"),
        ("change_password", "Change Password"),
        ("reset_password", "Reset Password"),
        ("enable_user", "Enable User"),
        ("disable_user", "Disable User"),
        ("assign_role", "Assign Role"),
        ("other", "Other"),
    ]

    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=[("success", "Success"), ("failure", "Failure")]
    )
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"


class RefreshTokenBlacklist(models.Model):
    """Blacklist for refresh tokens (logout)"""

    token_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blacklisted_tokens"
    )
    token = models.TextField()
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-blacklisted_at"]
        indexes = [
            models.Index(fields=["user", "-blacklisted_at"]),
        ]

    def __str__(self):
        return f"Blacklist token for {self.user.username}"
