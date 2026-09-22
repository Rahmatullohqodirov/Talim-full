from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from common.models import BaseModel

PERCENT_VALIDATORS = [MinValueValidator(0), MaxValueValidator(100)]


class SpeechAnalysis(BaseModel):
    """Har Transcript (foydalanuvchi repliкasi) uchun STT + talaffuz/aksent tahlili natijasi."""
    transcript = models.OneToOneField("session.Transcript", on_delete=models.CASCADE, related_name="speech_analysis")
    recognized_text = models.TextField()             # Whisper/STT natijasi
    confidence = models.FloatField(default=0, validators=PERCENT_VALIDATORS)
    pronunciation_score = models.FloatField(null=True, blank=True, validators=PERCENT_VALIDATORS)
    accent_similarity = models.FloatField(null=True, blank=True, validators=PERCENT_VALIDATORS)  # target aksentga yaqinlik
    detected_accent = models.CharField(max_length=50, blank=True)   # masalan "uzbek-influenced", "native-like"
    phoneme_errors = models.JSONField(default=list, blank=True)     # [{"phoneme": "th", "word": "think", "score": 42}]

    def __str__(self):
        return f"SpeechAnalysis<{self.transcript_id}>"


class GeneratedLesson(BaseModel):
    """AI Lesson Generator natijasi — foydalanuvchi darajasiga mos avtomatik tuzilgan dars."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="generated_lessons")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE)
    cefr_level = models.ForeignKey("subjects.CEFRLevel", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200)
    objective = models.TextField(blank=True)          # dars maqsadi
    content_blocks = models.JSONField(default=list)   # [{"type": "vocab"|"grammar"|"exercise", "data": {...}}]
    generated_by_model = models.CharField(max_length=50, default="claude")
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]


class AIChatThread(BaseModel):
    """Erkin AI Chat (avatar sessiyasidan tashqari, matnli yordamchi/repetitor suhbati)."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="ai_chat_threads")
    subject = models.ForeignKey("subjects.Subject", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ["-updated_at"]


class AIChatMessage(BaseModel):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    thread = models.ForeignKey(AIChatThread, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]
