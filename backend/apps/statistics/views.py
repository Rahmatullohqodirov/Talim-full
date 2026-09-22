from datetime import timedelta
from django.db import models
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import SubjectStats, DailyActivity, WeeklyReport
from .serializers import SubjectStatsSerializer, DailyActivitySerializer, WeeklyReportSerializer


def _series_for_range(user, range_key):
    """Kunlik/haftalik/oylik/yillik vaqt bo'yicha guruhlangan faollik statistikasi.

    range_key: "daily" (oxirgi 30 kun), "weekly" (oxirgi 12 hafta),
               "monthly" (oxirgi 12 oy), "yearly" (oxirgi 5 yil)
    Har bir nuqta: {label, minutes, sessions}
    """
    qs = DailyActivity.objects.filter(user=user)
    today = timezone.now().date()

    if range_key == "daily":
        since = today - timedelta(days=29)
        rows = qs.filter(date__gte=since).values("date").annotate(
            minutes=models.Sum("minutes_spent"), sessions=models.Sum("sessions_count")
        )
        by_date = {r["date"]: r for r in rows}
        points = []
        for i in range(30):
            d = since + timedelta(days=i)
            r = by_date.get(d)
            points.append({
                "label": d.strftime("%d.%m"),
                "date": d.isoformat(),
                "minutes": (r["minutes"] or 0) if r else 0,
                "sessions": (r["sessions"] or 0) if r else 0,
            })
        return points

    if range_key == "weekly":
        since = today - timedelta(weeks=11)
        rows = (
            qs.filter(date__gte=since)
            .annotate(period=TruncWeek("date"))
            .values("period")
            .annotate(minutes=models.Sum("minutes_spent"), sessions=models.Sum("sessions_count"))
            .order_by("period")
        )
        by_period = {r["period"]: r for r in rows}
        points = []
        cursor = since - timedelta(days=since.weekday())
        for i in range(12):
            wk = cursor + timedelta(weeks=i)
            r = by_period.get(wk)
            points.append({
                "label": wk.strftime("%d.%m"),
                "date": wk.isoformat(),
                "minutes": (r["minutes"] or 0) if r else 0,
                "sessions": (r["sessions"] or 0) if r else 0,
            })
        return points

    if range_key == "monthly":
        rows = (
            qs.annotate(period=TruncMonth("date"))
            .values("period")
            .annotate(minutes=models.Sum("minutes_spent"), sessions=models.Sum("sessions_count"))
        )
        by_period = {(r["period"].year, r["period"].month): r for r in rows}
        points = []
        y, m = today.year, today.month
        months = []
        for i in range(11, -1, -1):
            mm = m - i
            yy = y
            while mm <= 0:
                mm += 12
                yy -= 1
            months.append((yy, mm))
        oy_nomlari = ["Yan", "Fev", "Mar", "Apr", "May", "Iyun", "Iyul", "Avg", "Sen", "Okt", "Noy", "Dek"]
        for (yy, mm) in months:
            r = by_period.get((yy, mm))
            points.append({
                "label": f"{oy_nomlari[mm-1]} {yy}",
                "date": f"{yy}-{mm:02d}-01",
                "minutes": (r["minutes"] or 0) if r else 0,
                "sessions": (r["sessions"] or 0) if r else 0,
            })
        return points

    if range_key == "yearly":
        rows = (
            qs.annotate(period=TruncYear("date"))
            .values("period")
            .annotate(minutes=models.Sum("minutes_spent"), sessions=models.Sum("sessions_count"))
        )
        by_year = {r["period"].year: r for r in rows}
        points = []
        for i in range(4, -1, -1):
            yy = today.year - i
            r = by_year.get(yy)
            points.append({
                "label": str(yy),
                "date": f"{yy}-01-01",
                "minutes": (r["minutes"] or 0) if r else 0,
                "sessions": (r["sessions"] or 0) if r else 0,
            })
        return points

    return []


class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        since = timezone.now().date() - timedelta(days=90)
        stats = SubjectStats.objects.filter(user=user).select_related("subject")
        heatmap = DailyActivity.objects.filter(user=user, date__gte=since)
        latest_report = WeeklyReport.objects.filter(user=user).order_by("-week_start").first()
        prev_report = WeeklyReport.objects.filter(user=user).order_by("-week_start")[1:2].first()

        growth_percent = latest_report.growth_percent if latest_report else 0

        return Response({
            "total_minutes": sum(s.total_minutes for s in stats),
            "total_sessions": sum(s.sessions_completed for s in stats),
            "subjects": SubjectStatsSerializer(stats, many=True).data,
            "heatmap": DailyActivitySerializer(heatmap, many=True).data,
            "latest_weekly_report": WeeklyReportSerializer(latest_report).data if latest_report else None,
            "growth_percent": growth_percent,
            "series": {
                "daily": _series_for_range(user, "daily"),
                "weekly": _series_for_range(user, "weekly"),
                "monthly": _series_for_range(user, "monthly"),
                "yearly": _series_for_range(user, "yearly"),
            },
        })


class AdminStatsView(APIView):
    """GET /statistics/admin/overview/ — butun platforma bo'yicha umumiy ko'rsatkichlar."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from apps.session.models import LearningSession
        User = get_user_model()

        total_users = User.objects.count()
        premium_users = User.objects.filter(is_premium=True).count()
        today_sessions = LearningSession.objects.filter(started_at__date=timezone.now().date()).count()
        avg_streak = SubjectStats.objects.aggregate(avg=models.Avg("current_streak_days"))["avg"] or 0

        return Response({
            "total_users": total_users,
            "premium_users": premium_users,
            "today_sessions": today_sessions,
            "avg_streak_days": round(avg_streak, 1),
        })
