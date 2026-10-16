from django.db import models
from common.models import BaseModel


class LeaderboardEntry(BaseModel):
    class Scope(models.TextChoices):
        FRIENDS = "friends", "Friends"
        GLOBAL_ANON = "global_anon", "Global anonymous"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="leaderboard_entries")
    scope = models.CharField(max_length=12, choices=Scope.choices)
    week_start = models.DateField()
    total_points = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "scope", "week_start")
        ordering = ["scope", "week_start", "rank"]


class PointEvent(BaseModel):
    """Har bir ball qo'shilishi (quiz, flashcard, vocabulary, AI dars...).

    Haftalik/oylik reyting shu jadvaldan hisoblanadi; umumiy ball esa SubjectStats.total_points da.
    """
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="point_events")
    subject = models.ForeignKey("subjects.Subject", null=True, blank=True, on_delete=models.SET_NULL)
    points = models.PositiveIntegerField()
    source = models.CharField(max_length=20, blank=True)  # quiz | flashcard | vocabulary | ai_lesson | plan | speaking | math

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at", "user"])]
