"""Ball, faollik va streak — barcha bo'limlar uchun yagona joy.

Har qanday mashq (quiz, flashcard, vocabulary, AI dars, matematika) natijasini
record_activity() orqali yozing: SubjectStats, DailyActivity, PointEvent va streak
bir joyda yangilanadi, leaderboard va dashboard shu ma'lumotdan foydalanadi.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone


def _default_subject():
    from apps.subjects.models import Subject
    return Subject.objects.filter(code="english").first() or Subject.objects.first()


@transaction.atomic
def record_activity(user, subject=None, *, points=0, minutes=0, sessions=0, source=""):
    """Faollikni yozadi. Qaytaradi: {"points_added", "total_points", "streak"}."""
    from apps.statistics.models import DailyActivity, SubjectStats
    from .models import PointEvent

    subject = subject or _default_subject()
    if subject is None:
        return {"points_added": 0, "total_points": 0, "streak": 0}

    today = timezone.localdate()
    points, minutes, sessions = max(0, int(points)), max(0, int(minutes)), max(0, int(sessions))

    activity, created = DailyActivity.objects.select_for_update().get_or_create(
        user=user, subject=subject, date=today, defaults={"minutes_spent": 0, "sessions_count": 0},
    )
    first_today = created or (activity.minutes_spent == 0 and activity.sessions_count == 0)
    activity.minutes_spent += minutes
    activity.sessions_count += sessions
    activity.save(update_fields=["minutes_spent", "sessions_count", "updated_at"])

    stats, _ = SubjectStats.objects.select_for_update().get_or_create(user=user, subject=subject)
    stats.total_minutes += minutes
    stats.sessions_completed += sessions
    stats.total_points += points
    if stats.sessions_completed:
        stats.avg_session_minutes = round(stats.total_minutes / stats.sessions_completed, 1)

    # Streak: bugun birinchi marta faol bo'lsa, kechagi kunga qarab davom ettiramiz yoki 1 dan boshlaymiz
    if first_today:
        had_yesterday = DailyActivity.objects.filter(
            user=user, subject=subject, date=today - timedelta(days=1)
        ).exists()
        stats.current_streak_days = stats.current_streak_days + 1 if had_yesterday else 1
        stats.longest_streak_days = max(stats.longest_streak_days, stats.current_streak_days)
    stats.save()

    if points:
        PointEvent.objects.create(user=user, subject=subject, points=points, source=source[:20])
    if source:
        _complete_plan_items(user, subject, source)

    return {"points_added": points, "total_points": stats.total_points, "streak": stats.current_streak_days}


# Faollik turi -> o'quv rejasidagi qaysi bandlarni avtomatik bajarilgan qiladi
SOURCE_TO_PLAN_TYPES = {
    "quiz": {"quiz"},
    "flashcard": {"flashcard"},
    "vocabulary": {"vocabulary"},
    "ai_lesson": {"lesson", "grammar"},
    "speaking": {"speaking"},
    "math": {"math"},
    "video": {"video"},
}


def _complete_plan_items(user, subject, source):
    types = SOURCE_TO_PLAN_TYPES.get(source)
    if not types:
        return
    try:
        from apps.ai_teacher.plans import auto_complete_today
    except ImportError:
        return
    auto_complete_today(user, subject, types)


def overall_streak(user):
    """Barcha fanlar bo'yicha: ketma-ket necha kun faol bo'lgan (bugun yoki kechadan boshlab)."""
    from apps.statistics.models import DailyActivity

    days = set(
        DailyActivity.objects.filter(user=user, date__gte=timezone.localdate() - timedelta(days=400))
        .filter(models_q_active())
        .values_list("date", flat=True)
    )
    day = timezone.localdate()
    if day not in days:
        day -= timedelta(days=1)
    streak = 0
    while day in days:
        streak += 1
        day -= timedelta(days=1)
    return streak


def models_q_active():
    from django.db.models import Q
    return Q(minutes_spent__gt=0) | Q(sessions_count__gt=0)


def display_name(user):
    first = (user.first_name or "").strip()
    last = (user.last_name or "").strip()
    if first:
        return f"{first} {last[:1]}." if last else first
    return user.username
