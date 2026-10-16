from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Lokal (faqat kompyuteringizda) ishga tushirish uchun Redis/Postgres shart emas:
# cache -> xotirada (locmem), Celery -> darhol bajariladi (eager), Channels -> xotirada.
# Agar .env faylida REDIS_URL sozlangan bo'lsa va Redis ishlab tursa, buni base.py dagi
# sozlamalar bilan almashtirib qo'yishingiz mumkin (production uchun config/settings/prod.py'ga qarang).
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
