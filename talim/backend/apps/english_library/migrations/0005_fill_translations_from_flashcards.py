"""Flashcard'lardagi inglizcha-o'zbekcha juftliklardan Vocabulary.uz ni to'ldiradi."""
from django.db import migrations


def forwards(apps, schema_editor):
    Vocabulary = apps.get_model("english_library", "Vocabulary")
    Flashcard = apps.get_model("practice_tools", "Flashcard")
    pairs = {}
    for front, back in Flashcard.objects.filter(subject__code="english").values_list("front_text", "back_text"):
        key = (front or "").strip().lower()
        if key and back and key not in pairs:
            pairs[key] = back.strip()[:255]
    for word in Vocabulary.objects.filter(uz=""):
        variants = [word.headword.strip().lower()] + [v.strip().lower() for v in word.headword.split("/")]
        for v in variants:
            if v in pairs:
                word.uz = pairs[v]
                word.save(update_fields=["uz"])
                break


class Migration(migrations.Migration):
    dependencies = [
        ("english_library", "0004_vocabulary_translation"),
        ("practice_tools", "0001_initial"),
    ]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
