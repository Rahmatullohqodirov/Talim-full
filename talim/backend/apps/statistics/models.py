from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from common.models import BaseModel

PERCENT_VALIDATORS = [MinValueValidator(0), MaxValueValidator(100)]


class SubjectStats(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="subject_stats")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE)
    total_minutes = models.PositiveIntegerField(default=0)
    sessions_completed = models.PositiveIntegerField(default=0)
    avg_session_minutes = models.FloatField(default=0)
    avg_pronunciation_score = models.FloatField(null=True, blank=True, validators=PERCENT_VALIDATORS)
    avg_grammar_score = models.FloatField(null=True, blank=True, validators=PERCENT_VALIDATORS)
    current_streak_days = models.PositiveIntegerField(default=0)
    longest_streak_days = models.PositiveIntegerField(default=0)
    total_points = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "subject")
        indexes = [models.Index(fields=["user", "subject"])]

    def __str__(self):
        return f"Stats<{self.user_id},{self.subject.code}>"


class DailyActivity(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="daily_activity")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE)
    date = models.DateField()
    minutes_spent = models.PositiveIntegerField(default=0)
    sessions_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ("user", "subject", "date")
        indexes = [models.Index(fields=["user", "date"])]
        ordering = ["-date"]


class WeeklyReport(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="weekly_reports")
    week_start = models.DateField()
    total_minutes = models.PositiveIntegerField(default=0)
    growth_percent = models.FloatField(default=0)
    weakest_topics = models.JSONField(default=list, blank=True)
    pdf_url = models.URLField(blank=True)
    sent_via_email = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "week_start")
        ordering = ["-week_start"]
