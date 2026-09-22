from celery import shared_task


@shared_task
def recompute_subject_stats(user_id: str, subject_id: str):
    """Session tugagach chaqiriladi: SubjectStats va DailyActivity'ni qayta hisoblaydi,
    streakni yangilaydi va Redis orqali dashboard kanaliga push qiladi."""
    from datetime import timedelta
    from django.db.models import Sum, Avg, Count
    from django.utils import timezone
    from apps.session.models import LearningSession, Transcript
    from .models import SubjectStats, DailyActivity

    sessions = LearningSession.objects.filter(
        user_id=user_id, subject_id=subject_id, status="completed"
    )
    agg = sessions.aggregate(total=Sum("duration_seconds"), count=Count("id"))
    stats, _ = SubjectStats.objects.get_or_create(user_id=user_id, subject_id=subject_id)
    stats.total_minutes = (agg["total"] or 0) // 60
    stats.sessions_completed = agg["count"] or 0
    stats.avg_session_minutes = (stats.total_minutes / stats.sessions_completed) if stats.sessions_completed else 0

    score_agg = Transcript.objects.filter(session__in=sessions).aggregate(
        pron=Avg("pronunciation_score"), gram=Avg("grammar_score")
    )
    stats.avg_pronunciation_score = score_agg["pron"]
    stats.avg_grammar_score = score_agg["gram"]

    # --- DailyActivity: bugungi kun uchun yozuvni yangilaymiz/yaratamiz ---
    today = timezone.now().date()
    today_agg = sessions.filter(started_at__date=today).aggregate(total=Sum("duration_seconds"), count=Count("id"))
    activity, _ = DailyActivity.objects.get_or_create(
        user_id=user_id, subject_id=subject_id, date=today,
        defaults={"minutes_spent": 0, "sessions_count": 0},
    )
    activity.minutes_spent = (today_agg["total"] or 0) // 60
    activity.sessions_count = today_agg["count"] or 0
    activity.save()

    # --- Streak: foydalanuvchining istalgan fan bo'yicha faolligi asosida ---
    active_dates = set(
        DailyActivity.objects.filter(user_id=user_id, minutes_spent__gt=0)
        .values_list("date", flat=True)
    )
    current_streak = 0
    cursor = today
    while cursor in active_dates:
        current_streak += 1
        cursor -= timedelta(days=1)

    longest_streak = 0
    running = 0
    for d in sorted(active_dates):
        if (d - timedelta(days=1)) in active_dates:
            running += 1
        else:
            running = 1
        longest_streak = max(longest_streak, running)

    stats.current_streak_days = current_streak
    stats.longest_streak_days = max(stats.longest_streak_days, longest_streak)
    stats.save()


@shared_task
def generate_weekly_reports():
    """Celery beat: har dushanba yaratiladi — foydalanuvchining o'tgan haftalik
    faolligini joriy haftaga solishtirib WeeklyReport yozuvini yaratadi
    (o'sish foizi, eng zaif mavzular)."""
    from datetime import timedelta
    from django.contrib.auth import get_user_model
    from django.db.models import Sum
    from django.utils import timezone
    from .models import DailyActivity, WeeklyReport, SubjectStats

    User = get_user_model()
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    prev_week_start = week_start - timedelta(days=7)

    for user in User.objects.all():
        this_week = DailyActivity.objects.filter(
            user=user, date__gte=week_start, date__lte=today
        ).aggregate(total=Sum("minutes_spent"))["total"] or 0
        prev_week = DailyActivity.objects.filter(
            user=user, date__gte=prev_week_start, date__lt=week_start
        ).aggregate(total=Sum("minutes_spent"))["total"] or 0

        growth = 0.0
        if prev_week > 0:
            growth = round(((this_week - prev_week) / prev_week) * 100, 1)
        elif this_week > 0:
            growth = 100.0

        weakest = list(
            SubjectStats.objects.filter(user=user)
            .exclude(avg_pronunciation_score__isnull=True)
            .order_by("avg_pronunciation_score")
            .values_list("subject__code", flat=True)[:3]
        )

        WeeklyReport.objects.update_or_create(
            user=user, week_start=week_start,
            defaults={
                "total_minutes": this_week,
                "growth_percent": growth,
                "weakest_topics": weakest,
            },
        )
