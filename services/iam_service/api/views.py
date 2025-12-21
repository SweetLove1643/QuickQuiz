import logging
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import (
    User,
    UserProfile,
    Role,
    Permission,
    AuditLog,
    RefreshTokenBlacklist,
)
from api.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    RoleSerializer,
    PermissionSerializer,
    UserProfileSerializer,
    AuditLogSerializer,
)
from django.utils import timezone
from django.db.models import Q
import json

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["created_at", "username"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        if self.request.user.role == "student":
            return User.objects.filter(user_id=self.request.user.user_id)
        elif self.request.user.role == "teacher":
            return User.objects.filter(
                Q(role="student") | Q(user_id=self.request.user.user_id)
            )
        return User.objects.all()

    def get_permissions(self):
        if self.action in ["create", "login"]:
            permission_classes = [AllowAny]
        elif self.action in ["destroy", "disable_user"]:
            permission_classes = [IsAuthenticated, IsAdminUser]
        elif self.action in ["update", "partial_update", "change_password"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        self._log_action(
            user=user,
            action="create_user",
            resource="user",
            resource_id=str(user.user_id),
            status="success",
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        if request.user.user_id != user.user_id and not request.user.is_staff:
            return Response(
                {"detail": "You can only update your own profile."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        self._log_action(
            user=request.user,
            action="update_user",
            resource="user",
            resource_id=str(user.user_id),
            status="success",
        )

        return Response(UserSerializer(user).data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user_id = user.user_id
        user.delete()

        self._log_action(
            user=request.user,
            action="delete_user",
            resource="user",
            resource_id=str(user_id),
            status="success",
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def change_password(self, request, pk=None):
        user = self.get_object()

        if request.user.user_id != user.user_id and not request.user.is_staff:
            return Response(
                {"detail": "You can only change your own password."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        self._log_action(
            user=request.user,
            action="change_password",
            resource="user",
            resource_id=str(user.user_id),
            status="success",
        )

        return Response(
            {"detail": "Password changed successfully."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def disable_user(self, request, pk=None):
        user = self.get_object()
        user.is_active = False
        user.save()

        self._log_action(
            user=request.user,
            action="disable_user",
            resource="user",
            resource_id=str(user.user_id),
            status="success",
        )

        return Response(
            {"detail": "User disabled successfully."}, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def enable_user(self, request, pk=None):
        user = self.get_object()
        user.is_active = True
        user.save()

        self._log_action(
            user=request.user,
            action="enable_user",
            resource="user",
            resource_id=str(user.user_id),
            status="success",
        )

        return Response(
            {"detail": "User enabled successfully."}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        logger.info(
            f"[IAM Login] Received login request from {request.data.get('username')}"
        )

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        logger.info(f"[IAM Login] Serializer validation passed")

        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        user.update_last_login()
        refresh = RefreshToken.for_user(user)

        self._log_action(
            user=user,
            action="login",
            resource="auth",
            status="success",
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                RefreshTokenBlacklist.objects.create(
                    user=request.user, token=refresh_token, expires_at=token["exp"]
                )

            self._log_action(
                user=request.user, action="logout", resource="auth", status="success"
            )

            return Response(
                {"detail": "Logged out successfully."}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response(
                {"detail": "Logout failed."}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def _log_action(
        self,
        user,
        action,
        resource,
        resource_id="",
        status="success",
        ip_address=None,
        user_agent="",
        details=None,
    ):
        try:
            AuditLog.objects.create(
                user=user,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                details=details,
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class UserProfileViewSet(viewsets.ModelViewSet):

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        if request.user.user_id != profile.user.user_id and not request.user.is_staff:
            return Response(
                {"detail": "You can only update your own profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)


class RoleViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "description"]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code", "resource"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__username", "action", "resource"]
    ordering_fields = ["created_at", "action"]
    ordering = ["-created_at"]
