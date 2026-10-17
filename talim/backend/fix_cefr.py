
import re

from django.db import connection, transaction
from apps.subjects.models import Subject, CEFRLevel
from apps.practice_tools.models import Quiz

codes = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Uzoq kutib qolmasligi uchun
with connection.cursor() as cursor:
    cursor.execute("SET statement_timeout = 15000")

print("1. Ingliz tili fanini qidiryapman...", flush=True)
english = Subject.objects.get(code="english")
print("Fan topildi:", english.name, flush=True)

print("2. CEFR darajalarini yaratyapman...", flush=True)

with transaction.atomic():
    levels = {}

    for order, code in enumerate(codes, start=1):
        level, created = CEFRLevel.objects.get_or_create(
            subject=english,
            code=code,
            defaults={"order": order},
        )
        levels[code] = level
        print(code, "yaratildi" if created else "mavjud", flush=True)

    print("3. Quizlarni bog'layapman...", flush=True)

    quizzes = Quiz.objects.filter(
        subject=english,
        cefr_level__isnull=True,
    )

    to_update = []

    for quiz in quizzes.iterator():
        match = re.match(
            r"^(A1|A2|B1|B2|C1|C2)\b",
            quiz.title.strip(),
            re.IGNORECASE,
        )

        if match:
            code = match.group(1).upper()
            quiz.cefr_level = levels[code]
            to_update.append(quiz)

    Quiz.objects.bulk_update(
        to_update,
        ["cefr_level", "updated_at"],
        batch_size=100,
    )

print("\n--- NATIJA ---")
for code in codes:
    count = Quiz.objects.filter(
        subject=english,
        cefr_level__code=code,
    ).count()
    print(f"{code}: {count} ta quiz")

print("Bog'langan quizlar:", len(to_update))
print(
    "Darajasiz qolgan quizlar:",
    Quiz.objects.filter(
        subject=english,
        cefr_level__isnull=True,
    ).count(),
)
