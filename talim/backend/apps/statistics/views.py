from datetime import timedelta
from django.db import models
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
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


def _dashboard_extras(user):
    """Dashboard uchun qo'shimcha ma'lumot: ism, bugungi maqsad, streak, darajalar, reyting, reja, oxirgi natijalar."""
    from django.db.models import Avg, Count, Max, Sum
    from apps.ai_teacher.models import AssessmentResult, GeneratedLesson
    from apps.ai_teacher.plans import active_plans, serialize_plan
    from apps.english_library.models import VocabularyProgress
    from apps.gamification.models import PointEvent
    from apps.gamification.services import display_name, overall_streak
    from apps.practice_tools.models import FlashcardReview, QuizAttempt
    from apps.subjects.models import UserSubjectLevel

    today = timezone.localdate()
    profile = getattr(user, "profile", None)
    goal = getattr(profile, "daily_goal_minutes", 15) or 15
    today_rows = DailyActivity.objects.filter(user=user, date=today).aggregate(
        m=models.Sum("minutes_spent"), s=models.Sum("sessions_count"))
    week_start = today - timedelta(days=today.weekday())
    week_minutes = DailyActivity.objects.filter(user=user, date__gte=week_start).aggregate(
        m=models.Sum("minutes_spent"))["m"] or 0
    week_days = [
        {"date": (week_start + timedelta(days=i)).isoformat(),
         "label": ["Du", "Se", "Cho", "Pa", "Ju", "Sha", "Ya"][i],
         "minutes": 0}
        for i in range(7)
    ]
    for r in DailyActivity.objects.filter(user=user, date__gte=week_start).values("date").annotate(m=models.Sum("minutes_spent")):
        week_days[(r["date"] - week_start).days]["minutes"] = r["m"] or 0

    # Reyting o'rni (umumiy va shu hafta)
    my_total = SubjectStats.objects.filter(user=user).aggregate(t=Sum("total_points"))["t"] or 0
    totals = SubjectStats.objects.values("user_id").annotate(t=Sum("total_points"))
    rank_all = totals.filter(t__gt=my_total).count() + 1 if my_total else None
    my_week = PointEvent.objects.filter(user=user, created_at__date__gte=week_start).aggregate(t=Sum("points"))["t"] or 0
    week_totals = PointEvent.objects.filter(created_at__date__gte=week_start).values("user_id").annotate(t=Sum("points"))
    rank_week = week_totals.filter(t__gt=my_week).count() + 1 if my_week else None

    quiz = QuizAttempt.objects.filter(user=user).aggregate(avg=Avg("score_percent"), n=Count("quiz", distinct=True))
    last_lesson = GeneratedLesson.objects.filter(user=user, is_completed=True).order_by("-completed_at").first()
    weak = []
    for r in AssessmentResult.objects.filter(user=user).exclude(kind="speaking").order_by("-created_at")[:5]:
        for t in r.weak_topics:
            if t not in weak:
                weak.append(t)

    recent = []
    for r in AssessmentResult.objects.filter(user=user).select_related("subject").order_by("-created_at")[:4]:
        recent.append({"kind": r.kind, "label": r.get_kind_display(), "subject": r.subject.code,
                       "score": None if r.kind == "speaking" else round(r.score_percent),
                       "title": (r.details or {}).get("title", ""), "at": r.created_at.isoformat()})
    for a in QuizAttempt.objects.filter(user=user).select_related("quiz").order_by("-completed_at")[:4]:
        recent.append({"kind": "quiz", "label": "Quiz", "subject": None, "score": round(a.score_percent),
                       "title": a.quiz.title, "at": a.completed_at.isoformat()})
    recent.sort(key=lambda x: x["at"], reverse=True)

    return {
        "user": {"name": display_name(user), "first_name": user.first_name or user.username,
                 "is_premium": user.is_premium},
        "today": {"minutes": today_rows["m"] or 0, "sessions": today_rows["s"] or 0, "goal_minutes": goal},
        "week": {"minutes": week_minutes, "days": week_days},
        "streak": overall_streak(user),
        "longest_streak": SubjectStats.objects.filter(user=user).aggregate(m=Max("longest_streak_days"))["m"] or 0,
        "levels": [
            {"subject_code": r.subject.code, "subject_name": r.subject.name, "level": r.current_level.code}
            for r in UserSubjectLevel.objects.filter(user=user, current_level__isnull=False).select_related("subject", "current_level")
        ],
        "points": {"total": my_total, "week": my_week, "rank_all": rank_all, "rank_week": rank_week},
        "learning": {
            "words_mastered": VocabularyProgress.objects.filter(user=user, mastery__gte=100).count(),
            "words_learning": VocabularyProgress.objects.filter(user=user, mastery__gt=0, mastery__lt=100).count(),
            "quiz_avg": round(quiz["avg"]) if quiz["avg"] is not None else None,
            "quizzes_done": quiz["n"],
            "cards_mastered": FlashcardReview.objects.filter(user=user, interval_days__gte=21).count(),
            "cards_due": FlashcardReview.objects.filter(user=user, repetitions__gt=0, next_review_at__lte=timezone.now()).count(),
            "ai_lessons": GeneratedLesson.objects.filter(user=user, is_completed=True).count(),
        },
        "next": {
            "lesson_title": last_lesson.title if last_lesson else None,
            "next_step": last_lesson.next_step if last_lesson else None,
            "weak_topics": weak[:5],
        },
        "plans": [serialize_plan(p, today) for p in active_plans(user)],
        "recent": recent[:6],
    }


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
            **_dashboard_extras(user),
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
    """GET /statistics/admin/overview/ — butun platforma bo'yicha ko'rsatkichlar."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from django.db.models import Count, Sum
        from apps.ai_teacher.models import AIChatMessage, SupportTicket
        from apps.payments.models import PaymentTransaction
        from apps.session.models import LearningSession
        User = get_user_model()

        today = timezone.localdate()
        week_ago = today - timedelta(days=6)
        month_start = today.replace(day=1)
        active_today = DailyActivity.objects.filter(date=today).values("user").distinct().count()
        active_week = DailyActivity.objects.filter(date__gte=week_ago).values("user").distinct().count()
        revenue = PaymentTransaction.objects.filter(status="success", paid_at__date__gte=month_start) \
            .exclude(provider_transaction_id__startswith="demo-").aggregate(s=Sum("amount_uzs"))["s"] or 0
        signups = (
            User.objects.filter(date_joined__date__gte=week_ago)
            .annotate(d=TruncDate("date_joined")).values("d").annotate(n=Count("id"))
        )
        by_day = {str(r["d"]): r["n"] for r in signups}
        activity = {
            r["date"]: r["m"] for r in DailyActivity.objects.filter(date__gte=week_ago)
            .values("date").annotate(m=Sum("minutes_spent"))
        }
        days = [week_ago + timedelta(days=i) for i in range(7)]
        return Response({
            "total_users": User.objects.count(),
            "premium_users": User.objects.filter(is_premium=True).count(),
            "new_users_week": User.objects.filter(date_joined__date__gte=week_ago).count(),
            "active_today": active_today,
            "active_week": active_week,
            "today_sessions": LearningSession.objects.filter(started_at__date=today).count(),
            "ai_messages_today": AIChatMessage.objects.filter(role="user", created_at__date=today).count(),
            "revenue_month_uzs": float(revenue),
            "open_tickets": SupportTicket.objects.filter(status="open").count(),
            "avg_streak_days": round(SubjectStats.objects.aggregate(avg=models.Avg("current_streak_days"))["avg"] or 0, 1),
            "week": [{"date": d.isoformat(), "label": d.strftime("%d.%m"), "signups": by_day.get(d.isoformat(), 0),
                      "minutes": activity.get(d, 0) or 0} for d in days],
        })


class LogActivityView(APIView):
    """POST /statistics/log-activity/  {subject_code, minutes, sessions=1}

    Avatar-chatdan tashqarida (Quiz, Flashcard, MathPractice sahifalarida) o'tkazilgan
    mashq vaqtini qayd etadi. Avval faqat avatar-sessiyalari LearningSession orqali
    kuzatilardi — shu sabab dashboard statistikasi "umuman ishlamayapti" kabi ko'rinardi,
    chunki quiz/flashcard/matematika vaqti hech qayerga yozilmasdi."""
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "activity"

    def post(self, request):
        from apps.gamification.services import record_activity
        from apps.subjects.models import Subject

        subject_code = request.data.get("subject_code", "english")
        try:
            minutes = int(request.data.get("minutes", 0) or 0)
            sessions = int(request.data.get("sessions", 1) if request.data.get("sessions") is not None else 1)
        except (TypeError, ValueError):
            return Response({"detail": "minutes va sessions son bo'lishi kerak."}, status=400)
        if minutes <= 0:
            return Response({"detail": "minutes musbat son bo'lishi kerak."}, status=400)
        minutes = min(minutes, 180)  # bir so'rovda haddan tashqari qiymat yozilishining oldini olamiz

        subject = Subject.objects.filter(code=subject_code).first() or Subject.objects.first()
        if not subject:
            return Response({"detail": "Hech qanday fan topilmadi."}, status=400)

        res = record_activity(request.user, subject, minutes=minutes, sessions=max(0, sessions))
        today_minutes = DailyActivity.objects.filter(user=request.user, date=timezone.localdate()) \
            .aggregate(m=models.Sum("minutes_spent"))["m"] or 0
        return Response({"detail": "Qayd etildi.", "total_minutes_today": today_minutes, "streak": res["streak"]})
