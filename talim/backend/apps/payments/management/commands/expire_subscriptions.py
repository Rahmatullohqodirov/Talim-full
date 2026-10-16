"""Muddati tugagan obunalarni o'chiradi (is_premium=False). Har kuni cron/Celery beat bilan ishga tushiring:

    python manage.py expire_subscriptions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User, UserSubscription


class Command(BaseCommand):
    help = "Muddati tugagan Premium obunalarni o'chiradi"

    def handle(self, *args, **opts):
        expired_ids = UserSubscription.objects.filter(expires_at__lte=timezone.now()).values_list("user_id", flat=True)
        n = User.objects.filter(id__in=expired_ids, is_premium=True).update(is_premium=False)
        self.stdout.write(self.style.SUCCESS(f"{n} ta obuna muddati tugagani uchun o'chirildi"))
