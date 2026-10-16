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

    # --- AI Ustoz chatida qadamma-qadam o'tiladigan dars ---
    # content_blocks: [{"title": str, "type": "explain"|"example"|"exercise"|"quiz"|"speaking"|"review",
    #                   "done": bool, "result": "correct"|"partly"|"wrong"|"done"|None, "note": str}]
    thread = models.ForeignKey("ai_teacher.AIChatThread", null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="lessons")
    current_step = models.PositiveSmallIntegerField(default=0)   # 0-based
    summary = models.TextField(blank=True)
    next_step = models.TextField(blank=True)
    score_percent = models.FloatField(null=True, blank=True, validators=PERCENT_VALIDATORS)
    completed_at = models.DateTimeField(null=True, blank=True)

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
    # Qo'shimcha ma'lumot: {"mode": "speaking", "feedback": "...", "weak_words": [...], "tools_used": [...]}
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]


class AssessmentResult(BaseModel):
    """AI Ustoz o'tkazgan test yoki speaking mashqi natijasi.

    Test va talaffuz ballari alohida `kind` bilan saqlanadi, shunda o'rtacha
    test bali talaffuz taxminlari bilan aralashib ketmaydi.
    """

    class Kind(models.TextChoices):
        PLACEMENT = "placement", "Daraja testi"
        TEST = "test", "Test"
        SPEAKING = "speaking", "Speaking"
        LESSON = "lesson", "Dars"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="ai_assessments")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.TEST)
    score_percent = models.FloatField(validators=PERCENT_VALIDATORS)
    weak_topics = models.JSONField(default=list, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "subject", "kind"])]


class SupportTicket(BaseModel):
    """AI Ustoz hal qila olmagan muammo (to'lov, texnik nosozlik, shikoyat) — admin ko'rishi uchun."""

    class Category(models.TextChoices):
        PAYMENT = "payment", "To'lov"
        TECHNICAL = "technical", "Texnik nosozlik"
        COMPLAINT = "complaint", "Shikoyat"
        OTHER = "other", "Boshqa"

    class Status(models.TextChoices):
        OPEN = "open", "Ochiq"
        IN_PROGRESS = "in_progress", "Ko'rib chiqilmoqda"
        RESOLVED = "resolved", "Hal qilindi"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="support_tickets")
    thread = models.ForeignKey(AIChatThread, null=True, blank=True, on_delete=models.SET_NULL)
    category = models.CharField(max_length=12, choices=Category.choices, default=Category.OTHER)
    reason = models.TextField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ticket<{self.get_category_display()}, {self.status}>"


class LearnerMemory(BaseModel):
    """AI Ustoz o'quvchi haqida uzoq muddat eslab qoladigan, faqat o'qishga oid faktlar.

    Har bir so'rovda "o'quvchi kartasi" sifatida Claude'ga beriladi, shuning uchun yangi
    suhbatda ham Ustoz o'quvchining qiziqishi, uslubi va xatolarini biladi.
    O'quvchi ularni "Ustoz xotirasi" panelida ko'rishi va o'chirishi mumkin.
    """

    class Category(models.TextChoices):
        INTEREST = "interest", "Qiziqish"
        GOAL = "goal", "Maqsad"
        STYLE = "style", "O'rganish uslubi"
        MISTAKE = "mistake", "Takrorlanadigan xato"
        STRENGTH = "strength", "Kuchli tomon"
        OTHER = "other", "Boshqa"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="ai_memories")
    subject = models.ForeignKey("subjects.Subject", null=True, blank=True, on_delete=models.SET_NULL)
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.OTHER)
    text = models.CharField(max_length=300)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["user", "-updated_at"])]

    def __str__(self):
        return f"{self.get_category_display()}: {self.text[:50]}"


class StudyPlan(BaseModel):
    """Kunlik / haftalik / oylik o'quv rejasi (AI Ustoz tuzadi, o'quvchi Dashboard'da belgilaydi).

    items: [{"id": "d1-1", "date": "2026-10-10" | None, "week": 1 | None, "title": str,
             "type": "lesson"|"vocabulary"|"quiz"|"flashcard"|"speaking"|"video"|"grammar"|"reading"|"writing"|"math",
             "minutes": int, "done": bool, "done_at": iso | None}]
    """

    class Period(models.TextChoices):
        DAILY = "daily", "Kunlik"
        WEEKLY = "weekly", "Haftalik"
        MONTHLY = "monthly", "Oylik"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="study_plans")
    subject = models.ForeignKey("subjects.Subject", null=True, blank=True, on_delete=models.SET_NULL)
    period = models.CharField(max_length=8, choices=Period.choices)
    title = models.CharField(max_length=200)
    goal = models.TextField(blank=True)
    minutes_per_day = models.PositiveSmallIntegerField(default=20)
    start_date = models.DateField()
    end_date = models.DateField()
    items = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_active", "period"])]

    def __str__(self):
        return f"{self.get_period_display()} reja: {self.title}"
