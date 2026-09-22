import uuid

from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from common.models import BaseModel


class User(AbstractUser):
    """Loyihaning custom foydalanuvchi modeli (AUTH_USER_MODEL)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=20, blank=True)
    ui_language = models.CharField(max_length=8, default="uz")
    is_premium = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_joined"]
        indexes = [models.Index(fields=["phone"])]

    def __str__(self):
        return self.username or self.phone


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar_preference = models.ForeignKey(
        "avatars.Avatar", null=True, blank=True, on_delete=models.SET_NULL
    )
    daily_goal_minutes = models.PositiveIntegerField(default=15, validators=[MinValueValidator(1)])
    timezone = models.CharField(max_length=64, default="Asia/Tashkent")
    onboarding_goal = models.CharField(max_length=30, blank=True)
    onboarding_role = models.CharField(max_length=30, blank=True)
    onboarding_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile<{self.user_id}>"


class SubscriptionPlan(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    price_usd = models.DecimalField(max_digits=6, decimal_places=2)
    voice_cloning_enabled = models.BooleanField(default=False)
    max_sessions_per_day = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class UserSubscription(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscribers")
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_active(self):
        from django.utils import timezone as tz
        return self.expires_at is None or self.expires_at > tz.now()


class OfflineDevice(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_id = models.CharField(max_length=128, unique=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    platform = models.CharField(max_length=10, choices=[("android", "Android"), ("ios", "iOS")])
