"""Quizlarga CEFR darajasini nomidan aniqlab belgilaydi (masalan "B2 Vocabulary — Bo'lim 3" -> B2).

Nomida daraja yo'q quizlar uchun mavzuga qarab taxminiy daraja beriladi.
"""
import re

from django.db import migrations

ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
TOPIC_LEVELS = {
    "present simple": "A1",
    "predlog": "A1",
    "prepositions": "A1",
    "kundalik": "A1",
    "past simple": "A2",
    "sifatlar": "A2",
}


def guess_level(title):
    m = re.search(r"\b([ABC][12])", title.upper())
    if m:
        return m.group(1)
    low = title.lower()
    for key, lvl in TOPIC_LEVELS.items():
        if key in low:
            return lvl
    return None


def forwards(apps, schema_editor):
    Quiz = apps.get_model("practice_tools", "Quiz")
    CEFRLevel = apps.get_model("subjects", "CEFRLevel")
    for quiz in Quiz.objects.filter(cefr_level__isnull=True):
        code = guess_level(quiz.title)
        if not code:
            continue
        level, _ = CEFRLevel.objects.get_or_create(
            subject_id=quiz.subject_id, code=code, defaults={"order": ORDER.index(code) + 1}
        )
        quiz.cefr_level = level
        quiz.save(update_fields=["cefr_level"])


class Migration(migrations.Migration):
    dependencies = [
        ("practice_tools", "0001_initial"),
        ("subjects", "0001_initial"),
    ]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
