"""
Django settings for QuickQuiz Gateway Service.

Clean, production-ready API Gateway configuration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from parent directory
# Look for .env in QuickQuiz root directory
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
env_path = project_root / ".env"

if env_path.exists():
    load_dotenv(env_path)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# CORE DJANGO SETTINGS
# ==============================================================================

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "django-insecure-gateway-dev-key-change-in-production"
)

DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party apps
    "rest_framework",
    "corsheaders",
    # Local apps
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gateway.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gateway.wsgi.application"

# ==============================================================================
# DATABASE CONFIGURATION
# ==============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "data" / "gateway.db",
    }
}

# ==============================================================================
# SECURITY & AUTHENTICATION
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = "vi-vn"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# ==============================================================================
# STATIC FILES & MEDIA
# ==============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==============================================================================
# API GATEWAY CONFIGURATION
# ==============================================================================

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour", "user": "1000/hour"},
}

# CORS Configuration for Frontend Integration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8080",  # Vue dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only for development

# ==============================================================================
# MICROSERVICES CONFIGURATION
# ==============================================================================

MICROSERVICES = {
    "quiz_generator": {
        "host": os.getenv("QUIZ_GENERATOR_HOST", "localhost"),
        "port": os.getenv("QUIZ_GENERATOR_PORT", "8003"),
        "health_endpoint": "/health",
        "timeout": 30,
        "retry_count": 3,
    },
    "quiz_evaluator": {
        "host": os.getenv("QUIZ_EVALUATOR_HOST", "localhost"),
        "port": os.getenv("QUIZ_EVALUATOR_PORT", "8004"),
        "health_endpoint": "/health",
        "timeout": 60,
        "retry_count": 3,
    },
    "ocr_service": {
        "host": os.getenv("OCR_SERVICE_HOST", "localhost"),
        "port": os.getenv("OCR_SERVICE_PORT", "8007"),
        "health_endpoint": "/health",
        "timeout": 60,  # OCR might take longer
        "retry_count": 3,
    },
    "summary_service": {
        "host": os.getenv("SUMMARY_SERVICE_HOST", "localhost"),
        "port": os.getenv("SUMMARY_SERVICE_PORT", "8008"),
        "health_endpoint": "/health",
        "timeout": 60,  # Summarization might take longer
        "retry_count": 3,
    },
    "rag_chatbot_service": {
        "host": os.getenv("RAG_CHATBOT_HOST", "localhost"),
        "port": os.getenv("RAG_CHATBOT_PORT", "8011"),
        "health_endpoint": "/health",
        "timeout": 45,  # RAG processing might take time
        "retry_count": 3,
    },
    "iam_service": {
        "host": os.getenv("IAM_SERVICE_HOST", "localhost"),
        "port": os.getenv("IAM_SERVICE_PORT", "8005"),
        "health_endpoint": "/health",
        "timeout": 30,
        "retry_count": 3,
    },
    # Legacy service for backward compatibility
    "extract_information": {
        "host": os.getenv("EXTRACT_INFORMATION_HOST", "localhost"),
        "port": os.getenv("EXTRACT_INFORMATION_PORT", "8007"),
        "health_endpoint": "/health",
        "timeout": 30,
        "retry_count": 3,
    },
}

# Dynamically construct base URLs
for service_name, config in MICROSERVICES.items():
    config["base_url"] = f"http://{config['host']}:{config['port']}"

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname}] {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "gateway.log",
            "formatter": "verbose",
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "api": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "gateway": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# ==============================================================================
# PERFORMANCE & CACHING
# ==============================================================================

# Cache configuration (for future use)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
        "TIMEOUT": 300,
        "OPTIONS": {"MAX_ENTRIES": 1000},
    }
}

# ==============================================================================
# MONITORING & HEALTH CHECK
# ==============================================================================

# Health check settings
HEALTH_CHECK = {
    "CACHE_TIMEOUT": 60,  # Cache health check results for 60 seconds
    "DISK_USAGE_MAX": 90,  # Maximum disk usage percentage
    "MEMORY_MIN": 100,  # Minimum available memory in MB
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
