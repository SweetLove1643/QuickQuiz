from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

router = DefaultRouter()
router.register(r"users", views.UserViewSet, basename="user")
router.register(r"profiles", views.UserProfileViewSet, basename="profile")
router.register(r"roles", views.RoleViewSet, basename="role")
router.register(r"permissions", views.PermissionViewSet, basename="permission")
router.register(r"audit-logs", views.AuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("", include(router.urls)),
]
