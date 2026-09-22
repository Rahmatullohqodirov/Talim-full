from rest_framework import serializers
from .models import LearningSession, Transcript


class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = ["id", "speaker", "text", "audio_url", "pronunciation_score", "grammar_score", "created_at"]
        read_only_fields = ["id", "created_at"]


class LearningSessionSerializer(serializers.ModelSerializer):
    turns = TranscriptSerializer(many=True, read_only=True)

    class Meta:
        model = LearningSession
        fields = ["id", "subject", "avatar", "status", "started_at", "ended_at", "duration_seconds", "turns"]
        read_only_fields = ["id", "status", "started_at", "ended_at", "duration_seconds"]
