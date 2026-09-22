from rest_framework import serializers
from .models import SpeechAnalysis, GeneratedLesson, AIChatThread, AIChatMessage


class SpeechAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechAnalysis
        fields = ["transcript", "recognized_text", "confidence", "pronunciation_score",
                  "accent_similarity", "detected_accent", "phoneme_errors"]


class GeneratedLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedLesson
        fields = ["id", "subject", "cefr_level", "title", "objective", "content_blocks", "is_completed", "created_at"]
        read_only_fields = ["id", "title", "objective", "content_blocks", "created_at"]


class AIChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class AIChatThreadSerializer(serializers.ModelSerializer):
    messages = AIChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AIChatThread
        fields = ["id", "subject", "title", "messages", "updated_at"]
