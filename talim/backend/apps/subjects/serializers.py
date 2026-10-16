from rest_framework import serializers
from .models import Subject, CEFRLevel


class CEFRLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CEFRLevel
        fields = ["id", "code", "order"]


class SubjectSerializer(serializers.ModelSerializer):
    levels = CEFRLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ["id", "code", "name", "kind", "is_active_in_mvp", "levels"]
