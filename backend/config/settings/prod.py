from .base import *
from decouple import config

DEBUG = False
ALLOWED_HOSTS = [h.strip() for h in config("ALLOWED_HOSTS", default="").split(",") if h.strip()]

# --- HTTPS / transport xavfsizligi ---
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # frontend JS CSRF tokenini o'qishi kerak bo'lsa False qoladi
# Reverse proxy (nginx) orqasida ishlaganda Django https ekanini bilishi uchun:
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# --- HSTS: brauzerga "faqat https orqali kir" deb aytadi ---
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 kun; barqaror ishlagach 1 yilga (31536000) oshiring
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --- Qo'shimcha browser-darajasidagi himoya ---
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# --- CSRF: frontend domenidan kelayotgan so'rovlarga ishonch ---
# Payme/Click webhooklari CSRF-dan ozod qilingan (@csrf_exempt), lekin admin panel/POST
# so'rovlar uchun frontendning haqiqiy domenini bu yerga qo'shish SHART, aks holda 403 xato beradi.
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)

# --- CORS: production'da faqat aniq domenlarga ruxsat, wildcard ishlatilmaydi ---
CORS_ALLOW_ALL_ORIGINS = False

# --- Cookie/JWT umr sig'imi ---
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 kun

# --- Log: production xatolarini kuzatish uchun (Sentry ulanmagan bo'lsa ham fayl/console log) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

SENTRY_DSN = config("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )

if not SECRET_KEY or SECRET_KEY == "dev-secret-key-change-me":
    raise RuntimeError(
        "SECRET_KEY production uchun sozlanmagan! .env fayliga tasodifiy, uzun SECRET_KEY qo'ying "
        "(masalan: python -c \"import secrets; print(secrets.token_urlsafe(50))\")."
    )
if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS bo'sh — .env fayliga real domeningizni yozing (masalan: talim.uz,www.talim.uz).")
