from rest_framework import serializers
from .models import MathProblem, MathAttempt


class MathProblemSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    difficulty_label = serializers.CharField(source="get_difficulty_display", read_only=True)
    solution_steps = serializers.JSONField(read_only=True)

    class Meta:
        model = MathProblem
        fields = [
            "id", "topic", "topic_name", "statement", "difficulty",
            "difficulty_label", "solution_steps", "graph_data",
        ]


class MathAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = MathAttempt
        fields = ["id", "problem", "session", "user_answer", "is_correct", "time_spent_seconds", "created_at"]
        read_only_fields = ["id", "is_correct", "created_at"]
