from rest_framework import serializers
from .models import MathProblem, MathAttempt


class MathProblemSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    difficulty_label = serializers.CharField(source="get_difficulty_display", read_only=True)
    solution_steps = serializers.JSONField(required=False)
    answers = serializers.JSONField(required=False)
    answer_type = serializers.SerializerMethodField()
    solved = serializers.SerializerMethodField()
    tried = serializers.SerializerMethodField()

    class Meta:
        model = MathProblem
        fields = [
            "id", "topic", "topic_name", "statement", "difficulty",
            "difficulty_label", "solution_steps", "answers", "answer_type", "graph_data", "solved", "tried",
        ]

    def to_representation(self, obj):
        data = super().to_representation(obj)
        request = self.context.get("request")
        if not (request and request.user.is_staff):
            data.pop("answers", None)  # o'quvchiga javob oldindan ko'rsatilmaydi
        return data

    def get_answer_type(self, obj):
        return "numeric" if obj.answers else "self"

    def get_solved(self, obj):
        return bool(getattr(obj, "solved", False))

    def get_tried(self, obj):
        return bool(getattr(obj, "tried", False))

    def validate(self, attrs):
        # Admin javobni kiritmasa — yechim qadamlaridan avtomatik chiqaramiz
        from .services import extract_answers
        if not attrs.get("answers") and attrs.get("solution_steps"):
            attrs["answers"] = extract_answers(attrs.get("statement", ""), attrs["solution_steps"])
        return attrs


class MathAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = MathAttempt
        fields = ["id", "problem", "session", "user_answer", "is_correct", "time_spent_seconds", "created_at"]
        read_only_fields = ["id", "is_correct", "created_at"]
