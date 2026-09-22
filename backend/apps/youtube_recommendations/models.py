from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from common.models import BaseModel


class YoutubeVideo(BaseModel):
    """YouTube Data API orqali topilgan va keshlangan video metama'lumoti."""
    youtube_id = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=255)
    channel_title = models.CharField(max_length=150, blank=True)
    thumbnail_url = models.URLField(blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=8, default="en")
    subject = models.ForeignKey("subjects.Subject", null=True, blank=True, on_delete=models.SET_NULL, related_name="youtube_videos")
    topic_tags = models.JSONField(default=list, blank=True)          # ["kvadrat tenglama", "algebra"]
    difficulty = models.CharField(
        max_length=12,
        choices=[("beginner", "Beginner"), ("intermediate", "Intermediate"), ("advanced", "Advanced")],
        default="beginner",
    )
    avg_rating = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    view_count = models.PositiveIntegerField(default=0)   # YouTube'dagi ko'rishlar soni (sinxronlanadi)

    class Meta:
        ordering = ["-avg_rating"]
        indexes = [models.Index(fields=["subject", "difficulty"])]

    def __str__(self):
        return self.title


class RecommendedVideo(BaseModel):
    """AI tomonidan foydalanuvchiga tavsiya qilingan videolar (dars/mashq natijasidan keyin)."""
    class Reason(models.TextChoices):
        WEAK_TOPIC = "weak_topic", "Weak topic follow-up"
        LEVEL_MATCH = "level_match", "CEFR/daraja mos"
        POST_LESSON = "post_lesson", "Dars tugagach"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="recommended_videos")
    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE, related_name="recommendations")
    session = models.ForeignKey("session.LearningSession", null=True, blank=True, on_delete=models.SET_NULL)
    reason = models.CharField(max_length=16, choices=Reason.choices, default=Reason.POST_LESSON)
    rank = models.PositiveSmallIntegerField(default=1)   # 1-5 (eng mos videodan boshlab)
    was_clicked = models.BooleanField(default=False)

    class Meta:
        ordering = ["rank"]
        indexes = [models.Index(fields=["user", "created_at"])]


class SavedVideo(BaseModel):
    """Foydalanuvchi sevimlilar ro'yxatiga saqlagan videolar."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="saved_videos")
    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE, related_name="saved_by")

    class Meta:
        unique_together = ("user", "video")


class WatchHistory(BaseModel):
    """Ko'rilgan videolar tarixi — statistika va keyingi tavsiyalar uchun."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="watch_history")
    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE, related_name="watch_events")
    watched_seconds = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-watched_at"]
        indexes = [models.Index(fields=["user", "watched_at"])]


class VideoRating(BaseModel):
    """Foydalanuvchi bahosi — avg_rating ni yangilash uchun signal chaqiradi."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="video_ratings")
    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE, related_name="ratings")
    stars = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        unique_together = ("user", "video")
