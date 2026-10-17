import re
from django.db import transaction
from apps.subjects.models import CEFRLevel, Subject
from apps.practice_tools.models import Quiz

codes = ["A1", "A2", "B1", "B2", "C1", "C2"]
english = Subject.objects.get(code="english")

with transaction.atomic():
    for order, code in enumerate(codes, 1):
        CEFRLevel.objects.get_or_create(
            subject=english,
            code=code,
            defaults={"order": order},
        )

    levels = {
        x.code: x.id
        for x in CEFRLevel.objects.filter(subject=english)
    }

    counts = {code: 0 for code in codes}
    unmatched = []

    for quiz in Quiz.objects.filter(subject=english, cefr_level__isnull=True).only("id", "title"):
        match = re.match(r"^(A1|A2|B1|B2|C1|C2)\b", quiz.title.strip(), re.I)
        if match:
            code = match.group(1).upper()
            quiz.cefr_level_id = levels[code]
            counts[code] += 1
        else:
            unmatched.append(quiz.title)

    Quiz.objects.bulk_update(
        [q for q in Quiz.objects.filter(subject=english, cefr_level__isnull=True).only("id", "title") if False],
        ["cefr_level"],
    )

    print("CEFR darajalari yaratildi:", list(levels))
    print("Mos kelmagan nomlar:", unmatched[:10])
