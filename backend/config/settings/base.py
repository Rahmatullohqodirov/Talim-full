from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-secret-key-change-me")
AUTH_USER_MODEL = "accounts.User"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",
    "channels",
    "apps.accounts",
    "apps.subjects",
    "apps.session",
    "apps.statistics",
    "apps.math_practice",
    "apps.avatars",
    "apps.gamification",
    "apps.learning_path",
    "apps.practice_tools",
    "apps.youtube_recommendations",
    "apps.payments",
    "apps.ai_teacher",
    "apps.integrations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://localhost:6379/1"),
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [config("REDIS_URL", default="redis://localhost:6379/2")]},
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Login/register kabi ochiq endpointlarni brute-force'dan himoya qilish
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",       # login/register urinishlari
        "payment": "20/min",    # to'lov yaratish so'rovlari
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SuperTutor AI API",
    "DESCRIPTION": "AI asosidagi til va matematika o'qitish platformasi backend API'si",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
}

CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/3")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tashkent"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ACKS_LATE = True

YOUTUBE_API_KEY = config("YOUTUBE_API_KEY", default="")
GROQ_API_KEY = config("GROQ_API_KEY", default="")
XAI_API_KEY = config("XAI_API_KEY", default="")  # https://x.ai — Grok (AI Chat/Lesson Generator uchun asosiy provayder)
USD_TO_UZS_RATE = config("USD_TO_UZS_RATE", default=12700, cast=int)
PAYME_MERCHANT_ID = config("PAYME_MERCHANT_ID", default="")
PAYME_KEY = config("PAYME_KEY", default="")  # Payme kassa kaliti — webhook Basic Auth uchun
CLICK_SERVICE_ID = config("CLICK_SERVICE_ID", default="")
CLICK_MERCHANT_ID = config("CLICK_MERCHANT_ID", default="")
CLICK_SECRET_KEY = config("CLICK_SECRET_KEY", default="")  # Click imzo (sign_string) tekshiruvi uchun

# CORS_ALLOWED_ORIGINS = config(
#     "CORS_ALLOWED_ORIGINS",
#     default="http://localhost:5173,http://127.0.0.1:5173",
#     cast=lambda v: [s.strip() for s in v.split(",")],
# )
CORS_ALLOW_CREDENTIALS = True

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

XAI_MODEL = config("XAI_MODEL", default="grok-4.1-fast")