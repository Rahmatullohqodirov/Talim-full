"""O'quv rejalari: yaratish, bugungi bandlar, avtomatik belgilash."""
from datetime import timedelta

from django.utils import timezone

ITEM_TYPES = ["lesson", "vocabulary", "quiz", "flashcard", "speaking", "video", "grammar", "reading", "writing", "math"]

# Reja bandi turi -> ilovadagi sahifa (frontend shu yerga olib boradi)
TYPE_LINKS = {
    "lesson": "/app/ai-chat", "grammar": "/app/ai-chat", "writing": "/app/ai-chat", "reading": "/app/ai-chat",
    "speaking": "/app/ai-chat", "vocabulary": "/app/vocabulary", "quiz": "/app/quiz",
    "flashcard": "/app/vocabulary?tab=cards", "video": "/app/videos", "math": "/app/math",
}


def period_range(period, start):
    if period == "daily":
        return start, start
    if period == "weekly":
        return start, start + timedelta(days=6)
    return start, start + timedelta(days=27)  # oylik = 4 hafta


def normalize_items(period, start, raw_items):
    """Model bergan bandlarni tekshiradi va sanalarni serverda hisoblaydi (model sanada adashmasligi uchun)."""
    _, end = period_range(period, start)
    items = []
    for i, it in enumerate(raw_items or []):
        title = str(it.get("title", "")).strip()[:160]
        if not title:
            continue
        typ = it.get("type") if it.get("type") in ITEM_TYPES else "lesson"
        try:
            minutes = max(5, min(120, int(it.get("minutes", 15))))
        except (TypeError, ValueError):
            minutes = 15
        date, week = None, None
        if period == "monthly":
            try:
                week = max(1, min(4, int(it.get("week", 1))))
            except (TypeError, ValueError):
                week = 1
        else:
            try:
                day = max(1, min(7 if period == "weekly" else 1, int(it.get("day", 1))))
            except (TypeError, ValueError):
                day = 1
            d = start + timedelta(days=day - 1)
            date = min(d, end).isoformat()
        items.append({
            "id": f"i{i + 1}", "date": date, "week": week, "title": title, "type": typ,
            "minutes": minutes, "note": str(it.get("note", ""))[:200], "done": False, "done_at": None,
        })
    return items[:60]


def week_of(plan, day):
    return (day - plan.start_date).days // 7 + 1


def items_for_day(plan, day):
    """Shu kunga tegishli bandlar. Oylik rejada — shu haftaning bandlari."""
    if plan.period == "monthly":
        w = week_of(plan, day)
        return [it for it in plan.items if it.get("week") == w]
    iso = day.isoformat()
    return [it for it in plan.items if it.get("date") == iso]


def active_plans(user):
    from .models import StudyPlan

    today = timezone.localdate()
    return list(
        StudyPlan.objects.filter(user=user, is_active=True, end_date__gte=today, start_date__lte=today)
        .select_related("subject").order_by("period", "-created_at")
    )


def plan_progress(plan):
    total = len(plan.items)
    done = sum(1 for it in plan.items if it.get("done"))
    return {"done": done, "total": total, "percent": round(done / total * 100) if total else 0}


def serialize_plan(plan, today=None):
    today = today or timezone.localdate()
    return {
        "id": str(plan.id),
        "period": plan.period,
        "period_label": plan.get_period_display(),
        "title": plan.title,
        "goal": plan.goal,
        "subject_code": plan.subject.code if plan.subject_id else None,
        "minutes_per_day": plan.minutes_per_day,
        "start_date": plan.start_date.isoformat(),
        "end_date": plan.end_date.isoformat(),
        "is_active": plan.is_active,
        "current_week": week_of(plan, today) if plan.period == "monthly" else None,
        "items": [{**it, "link": TYPE_LINKS.get(it.get("type"), "/app/ai-chat")} for it in plan.items],
        "today": [it["id"] for it in items_for_day(plan, today)],
        "progress": plan_progress(plan),
    }


PLAN_ITEM_POINTS = 5


def set_item_done(plan, item_id, done=True):
    """Bandni belgilaydi. Birinchi marta bajarilganda 5 ball beriladi."""
    changed, _reward = False, False
    for it in plan.items:
        if it.get("id") == item_id:
            if bool(it.get("done")) != bool(done):
                it["done"] = bool(done)
                it["done_at"] = timezone.now().isoformat() if done else None
                changed = True
                if done and not it.get("rewarded"):
                    it["rewarded"] = True
                    _reward = True
            break
    else:
        return None
    if changed:
        plan.save(update_fields=["items", "updated_at"])
    if _reward:
        from apps.gamification.models import PointEvent
        from apps.statistics.models import SubjectStats
        subject = plan.subject
        if subject is None:
            from apps.subjects.models import Subject
            subject = Subject.objects.filter(code="english").first()
        if subject:
            stats, _ = SubjectStats.objects.get_or_create(user=plan.user, subject=subject)
            stats.total_points += PLAN_ITEM_POINTS
            stats.save(update_fields=["total_points", "updated_at"])
            PointEvent.objects.create(user=plan.user, subject=subject, points=PLAN_ITEM_POINTS, source="plan")
    return changed


def auto_complete_today(user, subject, types):
    """Mashq bajarilganda bugungi rejadagi mos (shu turdagi) birinchi bajarilmagan bandni belgilaydi."""
    today = timezone.localdate()
    for plan in active_plans(user):
        if plan.subject_id and subject and plan.subject_id != subject.id:
            continue
        for it in items_for_day(plan, today):
            if not it.get("done") and it.get("type") in types:
                set_item_done(plan, it["id"], True)
                break
