"""Darslar: grammatika darsi (so'zlar lug'ati + mashqlar) va "Tinglang va o'qing" hikoyalar kutubxonasi.

Raqobatchi ilovalardagi tuzilmaga mos: har bir dars -> so'zlar ro'yxati + bir nechta mashq turi
(ingl->uzb, uzb->ingl, bo'shliqni to'ldirish, gap tuzish). Hikoyalar alohida, darajaga ko'ra, har
birida audio (edge-tts) va tushunish testi bor.
"""
from django.db import models

from common.models import BaseModel


class Lesson(BaseModel):
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="lessons")
    cefr_level = models.ForeignKey("subjects.CEFRLevel", on_delete=models.CASCADE, related_name="lessons")
    order = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=150)          # "Fe'lning asosiy shakli"
    explanation = models.TextField(blank=True)         # qisqa grammatika tushuntirishi (o'zbekcha)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["cefr_level__order", "order"]

    def __str__(self):
        return f"{self.cefr_level.code}: {self.title}"


class LessonWord(BaseModel):
    """Darsdagi so'zlar lug'ati."""
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="words")
    word = models.CharField(max_length=80)
    translation = models.CharField(max_length=150)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class LessonExercise(BaseModel):
    """Bitta mashq: tarjima (ikki yo'nalishda), bo'shliqni to'ldirish yoki gap tuzish."""

    class Kind(models.TextChoices):
        EN_UZ = "en_uz", "Inglizcha -> O'zbekcha"
        UZ_EN = "uz_en", "O'zbekcha -> Inglizcha"
        FILL_BLANK = "fill_blank", "Tushib qolgan so'zni topish"
        BUILD_SENTENCE = "build_sentence", "Matn tuzish"

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="exercises")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    prompt = models.CharField(max_length=300)          # savol/so'z/bo'shliqli gap
    bank = models.JSONField(default=list, blank=True)  # so'z banki (variantlar)
    answer = models.CharField(max_length=300)          # to'g'ri javob
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class UserLessonProgress(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    completed = models.BooleanField(default=False)
    correct = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    points_awarded = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "lesson")


class Story(BaseModel):
    """"Tinglang va o'qing" kutubxonasidagi bitta hikoya."""
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="stories")
    cefr_level = models.ForeignKey("subjects.CEFRLevel", on_delete=models.CASCADE, related_name="stories")
    order = models.PositiveSmallIntegerField(default=0)
    title = models.CharField(max_length=150)
    cover_emoji = models.CharField(max_length=8, default="📖")   # rasm o'rniga yengil, tezkor belgi
    cover_color = models.CharField(max_length=20, default="violet")
    text = models.TextField()
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["cefr_level__order", "order"]

    def __str__(self):
        return self.title


class StoryQuestion(BaseModel):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="questions")
    question = models.CharField(max_length=300)
    options = models.JSONField(default=list)
    correct = models.CharField(max_length=200)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class UserStoryResult(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="story_results")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="results")
    correct = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    points_awarded = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "story")
