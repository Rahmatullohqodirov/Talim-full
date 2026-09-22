from rest_framework import serializers
from .models import SubjectStats, DailyActivity, WeeklyReport


class SubjectStatsSerializer(serializers.ModelSerializer):
    subject_code = serializers.CharField(source="subject.code", read_only=True)

    class Meta:
        model = SubjectStats
        fields = [
            "subject_code", "total_minutes", "sessions_completed", "avg_session_minutes",
            "avg_pronunciation_score", "avg_grammar_score",
            "current_streak_days", "longest_streak_days", "total_points",
        ]


class DailyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = ["date", "subject", "minutes_spent", "sessions_count"]


class WeeklyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyReport
        fields = ["week_start", "total_minutes", "growth_percent", "weakest_topics", "pdf_url"]
