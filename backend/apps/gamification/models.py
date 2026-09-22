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
