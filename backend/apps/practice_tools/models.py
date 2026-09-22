from django.db import models
from common.models import BaseModel


class Quiz(BaseModel):
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="quizzes")
    cefr_level = models.ForeignKey("subjects.CEFRLevel", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=150)


class QuizQuestion(BaseModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    choices = models.JSONField(default=list)
    correct_index = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["id"]


class QuizAttempt(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    score_percent = models.FloatField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)


class Flashcard(BaseModel):
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="flashcards")
    front_text = models.CharField(max_length=255)
    back_text = models.CharField(max_length=255)
    audio_url = models.URLField(blank=True)


class FlashcardReview(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="flashcard_reviews")
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name="reviews")
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=1)
    repetitions = models.PositiveIntegerField(default=0)
    next_review_at = models.DateTimeField()

    class Meta:
        unique_together = ("user", "flashcard")
        indexes = [models.Index(fields=["user", "next_review_at"])]
