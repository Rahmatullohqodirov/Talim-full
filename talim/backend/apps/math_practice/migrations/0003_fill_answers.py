"""Mavjud masalalar uchun to'g'ri javoblarni yechim qadamlaridan chiqarib `answers` ga yozadi."""
from django.db import migrations


def forwards(apps, schema_editor):
    from apps.math_practice.services import extract_answers

    MathProblem = apps.get_model("math_practice", "MathProblem")
    for p in MathProblem.objects.all():
        if not p.answers:
            p.answers = extract_answers(p.statement, p.solution_steps or [])
            p.save(update_fields=["answers"])


class Migration(migrations.Migration):
    dependencies = [("math_practice", "0002_problem_answers")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
