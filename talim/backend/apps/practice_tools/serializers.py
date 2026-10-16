from rest_framework import serializers
from .models import Quiz, QuizQuestion, FlashcardReview, Flashcard


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        # To'g'ri javob (correct_index) shu yerda ataylab qo'shilgan: bu mashq (Duolingo uslubidagi)
        # vositasi, imtihon emas — PWA javobni bir marta yuklab olgach, offline holatda ham
        # foydalanuvchi javobini darhol mahalliy (client-side) tekshira olishi uchun kerak.
        fields = ["id", "text", "choices", "correct_index"]


def quiz_category(title):
    low = (title or "").lower()
    if "vocabulary" in low or "so'z" in low:
        return "vocabulary"
    if "grammar" in low or "simple" in low or "predlog" in low or "sifat" in low:
        return "grammar"
    return "other"


class QuizListSerializer(serializers.ModelSerializer):
    """Ro'yxat uchun yengil ko'rinish: savollarsiz (500+ quizda 10 mingta savolni yuklamaslik uchun)."""
    level = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    question_count = serializers.IntegerField(read_only=True)
    best_score = serializers.FloatField(read_only=True, allow_null=True)
    attempts = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ["id", "title", "subject", "subject_code", "level", "category", "question_count", "best_score", "attempts",
                  "is_published"]

    def get_level(self, obj):
        return obj.cefr_level.code if obj.cefr_level_id else None

    def get_category(self, obj):
        return quiz_category(obj.title)

    def get_attempts(self, obj):
        return getattr(obj, "attempts_n", 0)


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    level = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ["id", "subject", "cefr_level", "level", "title", "questions"]

    def get_level(self, obj):
        return obj.cefr_level.code if obj.cefr_level_id else None


class FlashcardReviewSerializer(serializers.ModelSerializer):
    front_text = serializers.CharField(source="flashcard.front_text", read_only=True)
    back_text = serializers.CharField(source="flashcard.back_text", read_only=True)
    audio_url = serializers.CharField(source="flashcard.audio_url", read_only=True)
    is_new = serializers.SerializerMethodField()

    class Meta:
        model = FlashcardReview
        fields = ["id", "flashcard", "front_text", "back_text", "audio_url", "ease_factor", "interval_days",
                  "repetitions", "next_review_at", "is_new"]
        read_only_fields = ["ease_factor", "interval_days", "repetitions", "next_review_at"]

    def get_is_new(self, obj):
        return obj.repetitions == 0 and obj.interval_days <= 1 and obj.ease_factor == 2.5


class FlashcardSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Flashcard
        fields = ["id", "subject", "subject_name", "front_text", "back_text", "audio_url"]
