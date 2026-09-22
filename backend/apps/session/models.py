from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from common.models import BaseModel

PERCENT_VALIDATORS = [MinValueValidator(0), MaxValueValidator(100)]


class LearningSession(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ABORTED = "aborted", "Aborted"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="sessions")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.PROTECT, related_name="sessions")
    avatar = models.ForeignKey("avatars.Avatar", null=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["user", "subject", "started_at"])]

    def __str__(self):
        return f"{self.user_id} / {self.subject.code} @ {self.started_at:%Y-%m-%d}"


class Transcript(BaseModel):
    class Speaker(models.TextChoices):
        USER = "user", "User"
        AVATAR = "avatar", "Avatar"

    session = models.ForeignKey(LearningSession, on_delete=models.CASCADE, related_name="turns")
    speaker = models.CharField(max_length=8, choices=Speaker.choices)
    text = models.TextField()
    audio_url = models.URLField(blank=True)
    pronunciation_score = models.FloatField(null=True, blank=True, validators=PERCENT_VALIDATORS)
    grammar_score = models.FloatField(null=True, blank=True, validators=PERCENT_VALIDATORS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class VoiceCloningRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="voice_clone_requests")
    sample_audio_url = models.URLField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    voice_model_id = models.CharField(max_length=100, blank=True)
