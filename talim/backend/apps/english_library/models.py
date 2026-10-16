from django.db import models
from django.conf import settings
from django.db import models

class Vocabulary(models.Model):
    headword = models.CharField(max_length=255, db_index=True)
    pos = models.CharField(max_length=100, blank=True)
    cefr = models.CharField(max_length=20, db_index=True)
    core_inventory_1 = models.CharField(max_length=100, blank=True)
    core_inventory_2 = models.CharField(max_length=100, blank=True)
    threshold = models.CharField(max_length=100, blank=True)

    # O'zbekcha tarjima va misol (flashcardlardan yoki AI orqali bir marta to'ldiriladi, keyin keshda turadi)
    uz = models.CharField(max_length=255, blank=True)
    example = models.CharField(max_length=300, blank=True)
    example_uz = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["cefr", "headword"]
        indexes = [
            models.Index(fields=["cefr", "headword"]),
        ]

    def __str__(self):
        return f"{self.headword} ({self.cefr})"


class Grammar(models.Model):
    code = models.CharField(max_length=100, blank=True)
    shorthand_code = models.CharField(max_length=100, blank=True)
    grammatical_item = models.CharField(max_length=500)
    sentence_type = models.CharField(max_length=100, blank=True)
    cefr_level = models.CharField(max_length=20, blank=True, db_index=True)
    freq_disp = models.CharField(max_length=100, blank=True)
    core_inventory = models.CharField(max_length=100, blank=True)
    egp = models.CharField(max_length=100, blank=True)
    gselo = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["cefr_level", "grammatical_item"]

    def __str__(self):
        return f"{self.grammatical_item} ({self.cefr_level})"

class VocabularyProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vocabulary_progress",
    )

    vocabulary = models.ForeignKey(
        Vocabulary,
        on_delete=models.CASCADE,
        related_name="user_progress",
    )

    # 0 - 100
    mastery = models.PositiveSmallIntegerField(default=0)

    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)

    last_reviewed = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "vocabulary"],
                name="unique_user_vocabulary_progress",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "vocabulary"]),
            models.Index(fields=["user", "mastery"]),
        ]

    def __str__(self):
        return (
            f"{self.user_id} - "
            f"{self.vocabulary.headword} - "
            f"{self.mastery}%"
        )