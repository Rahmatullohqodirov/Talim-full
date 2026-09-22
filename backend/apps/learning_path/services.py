"""Personalized Learning Engine — LearningPath/LearningPathItem generatsiyasi.

Foydalanuvchining SubjectStats (aniqlik/streak) va MathAttempt/Transcript
natijalari asosida keyingi eng mos mavzular ketma-ketligini tuzadi.
"""
from django.db import transaction


def build_language_path(user, subject):
    from apps.subjects.models import CEFRLevel, UserSubjectLevel
    from .models import LearningPath, LearningPathItem

    current = UserSubjectLevel.objects.filter(user=user, subject=subject).select_related("current_level").first()
    start_order = current.current_level.order if current and current.current_level else 1
    upcoming_levels = CEFRLevel.objects.filter(subject=subject, order__gte=start_order).order_by("order")[:5]

    with transaction.atomic():
        LearningPath.objects.filter(user=user, subject=subject, is_active=True).update(is_active=False)
        path = LearningPath.objects.create(user=user, subject=subject)
        LearningPathItem.objects.bulk_create([
            LearningPathItem(path=path, order=i + 1, cefr_level=level)
            for i, level in enumerate(upcoming_levels)
        ])
    return path


def build_math_path(user, subject):
    from apps.math_practice.models import MathAttempt, MathTopic
    from django.db.models import Avg, Count
    from .models import LearningPath, LearningPathItem

    weak_topics = (
        MathAttempt.objects.filter(user=user, problem__topic__isnull=False)
        .values("problem__topic")
        .annotate(accuracy=Avg("is_correct"), attempts=Count("id"))
        .filter(attempts__gte=1)
        .order_by("accuracy")[:5]
    )
    topic_ids = [w["problem__topic"] for w in weak_topics] or list(MathTopic.objects.values_list("id", flat=True)[:5])

    with transaction.atomic():
        LearningPath.objects.filter(user=user, subject=subject, is_active=True).update(is_active=False)
        path = LearningPath.objects.create(user=user, subject=subject)
        LearningPathItem.objects.bulk_create([
            LearningPathItem(path=path, order=i + 1, math_topic_id=tid)
            for i, tid in enumerate(topic_ids)
        ])
    return path


def generate_personalized_path(user, subject):
    """Fan turiga qarab tegishli generatorni chaqiradi."""
    if subject.kind == subject.Kind.MATH:
        return build_math_path(user, subject)
    return build_language_path(user, subject)
