from rest_framework import serializers
from .models import LearningPath, LearningPathItem


class LearningPathItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningPathItem
        fields = ["id", "order", "cefr_level", "math_topic", "status"]


class LearningPathSerializer(serializers.ModelSerializer):
    items = LearningPathItemSerializer(many=True, read_only=True)

    class Meta:
        model = LearningPath
        fields = ["id", "subject", "generated_at", "is_active", "items"]
