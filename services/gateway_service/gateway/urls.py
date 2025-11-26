"""
URL configuration for QuickQuiz Gateway Service.

Clean URL routing for the API Gateway.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


def gateway_info(request):
    """Gateway information endpoint."""
    return JsonResponse(
        {
            "service": "QuickQuiz API Gateway",
            "version": "2.0.0",
            "status": "operational",
            "description": "Centralized API gateway for QuickQuiz microservices",
            "documentation": {
                "api_endpoints": "/api/",
                "health_check": "/api/health/",
                "admin_panel": "/admin/",
            },
            "microservices": {
                "quiz_generator": f"http://{settings.MICROSERVICES['quiz_generator']['host']}:{settings.MICROSERVICES['quiz_generator']['port']}",
                "quiz_evaluator": f"http://{settings.MICROSERVICES['quiz_evaluator']['host']}:{settings.MICROSERVICES['quiz_evaluator']['port']}",
            },
        }
    )


urlpatterns = [
    # Gateway info
    path("", gateway_info, name="gateway_info"),
    # Django admin
    path("admin/", admin.site.urls),
    # API routes
    path("api/", include("api.urls")),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
