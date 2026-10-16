""""What is the CEFR-J level of this grammatical item?" savolli quizlarni yashiradi:
ular o'quvchiga grammatika o'rgatmaydi. `python manage.py rebuild_quizzes` (AI kaliti bilan)
ularni haqiqiy grammatika savollariga aylantiradi va qayta e'lon qiladi."""
from django.db import migrations


def forwards(apps, schema_editor):
    Quiz = apps.get_model("practice_tools", "Quiz")
    QuizQuestion = apps.get_model("practice_tools", "QuizQuestion")
    ids = QuizQuestion.objects.filter(text__startswith="What is the CEFR-J level").values_list("quiz_id", flat=True)
    Quiz.objects.filter(id__in=set(ids)).update(is_published=False)


class Migration(migrations.Migration):
    dependencies = [("practice_tools", "0003_quiz_is_published")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
