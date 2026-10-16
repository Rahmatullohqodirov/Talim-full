from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-secret-key-change-me")
AUTH_USER_MODEL = "accounts.User"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# --- Email (ro'yxatdan o'tishni tasdiqlash uchun) ---
# Standart: konsolga chiqaradi (dev uchun qulay). Haqiqiy email yuborish uchun .env fayliga
# EMAIL_HOST/EMAIL_HOST_USER/EMAIL_HOST_PASSWORD to'ldiring (masalan Gmail App Password,
# yoki SendGrid/Mailgun/Amazon SES SMTP ma'lumotlari) — shunda avtomatik SMTP orqali yuboradi.
EMAIL_HOST = config("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@talim.uz")

# --- Google / Facebook orqali kirish (ixtiyoriy — .env'da bo'sh qoldirilsa, shu provayder
#     orqali kirish frontendda "hali sozlanmagan" deb ko'rsatiladi, ilova buzilmaydi) ---
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
FACEBOOK_APP_ID = config("FACEBOOK_APP_ID", default="")
FACEBOOK_APP_SECRET = config("FACEBOOK_APP_SECRET", default="")

# Frontend manzili — tasdiqlash havolasi shu domenga yo'naltiriladi
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")

# (Eski GOOGLE_OAUTH_* / FACEBOOK_OAUTH_* sozlamalari ishlatilmas edi — olib tashlandi; yuqoridagi
#  GOOGLE_CLIENT_ID / FACEBOOK_APP_ID / FACEBOOK_APP_SECRET dan foydalaning.)

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
    "apps.ai_teacher",
    "apps.english_library",
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
    "apps.integrations",
    "apps.lessons",
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

DATABASE_URL="postgresql://neondb_owner:PAROLNI_YANGILA@ep-falling-sound-b5rr4l98-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

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
        "activity": "30/min",   # faollik vaqtini qayd etish (har daqiqada yuboriladi)
        "youtube_search": "20/min",  # YouTube API kvotasini tejash
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


CORS_ALLOW_CREDENTIALS = True

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


XAI_MODEL = config("XAI_MODEL", default="grok-4.1-fast")

# === AI Ustoz (Claude) ===
# ANTHROPIC_API_KEY bo'lsa AI Ustoz Claude orqali ishlaydi (tool'lar bilan).
# Bo'lmasa yoki Claude javob bermasa — eski xAI -> Groq zanjiriga tushadi.
ANTHROPIC_API_KEY = config("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = config("ANTHROPIC_MODEL", default="claude-sonnet-5-5")
AI_TUTOR_HISTORY_LIMIT = config("AI_TUTOR_HISTORY_LIMIT", default=20, cast=int)  # Claude'ga yuboriladigan oxirgi xabarlar soni
AI_TUTOR_MAX_TOOL_ROUNDS = config("AI_TUTOR_MAX_TOOL_ROUNDS", default=8, cast=int)

# === Speaking (ixtiyoriy: pip install -r requirements/speaking.txt) ===
WHISPER_MODEL_SIZE = config("WHISPER_MODEL_SIZE", default="small")  # tiny | base | small | medium | large-v3
SPEAKING_MAX_UPLOAD_MB = config("SPEAKING_MAX_UPLOAD_MB", default=10, cast=int)


# Production uchun vaqtinchalik lokal kesh
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "talim-production-cache",
    }
}


CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


import os
from dotenv import load_dotenv

load_dotenv()


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "neondb",
        "USER": "neondb_owner",
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": "ep-falling-sound-b5rr4l98-pooler.c-7.us-east-2.aws.neon.tech",
        "PORT": "5432",
        "OPTIONS": {
            "sslmode": "require",
            "channel_binding": "require",
        },
    }
}
