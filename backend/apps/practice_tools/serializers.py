from rest_framework import serializers
from .models import Quiz, QuizQuestion, FlashcardReview, Flashcard


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        # To'g'ri javob (correct_index) shu yerda ataylab qo'shilgan: bu mashq (Duolingo uslubidagi)
        # vositasi, imtihon emas — PWA javobni bir marta yuklab olgach, offline holatda ham
        # foydalanuvchi javobini darhol mahalliy (client-side) tekshira olishi uchun kerak.
        fields = ["id", "text", "choices", "correct_index"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "subject", "cefr_level", "title", "questions"]


class FlashcardReviewSerializer(serializers.ModelSerializer):
    front_text = serializers.CharField(source="flashcard.front_text", read_only=True)
    back_text = serializers.CharField(source="flashcard.back_text", read_only=True)

    class Meta:
        model = FlashcardReview
        fields = ["id", "flashcard", "front_text", "back_text", "ease_factor", "interval_days", "next_review_at"]
        read_only_fields = ["ease_factor", "interval_days", "next_review_at"]


class FlashcardSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = Flashcard
        fields = ["id", "subject", "subject_name", "front_text", "back_text", "audio_url"]
