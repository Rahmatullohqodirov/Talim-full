from rest_framework import serializers
from .models import SpeechAnalysis, GeneratedLesson, AIChatThread, AIChatMessage, LearnerMemory


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
        fields = ["id", "role", "content", "meta", "created_at"]
        read_only_fields = ["id", "meta", "created_at"]


class _SubjectFieldsMixin(serializers.Serializer):
    subject_code = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()

    def get_subject_code(self, obj):
        return obj.subject.code if obj.subject_id else None

    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject_id else None


class AIChatThreadListSerializer(_SubjectFieldsMixin, serializers.ModelSerializer):
    """Ro'yxat uchun yengil ko'rinish (xabarlarsiz)."""
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AIChatThread
        fields = ["id", "subject", "subject_code", "subject_name", "title", "last_message", "updated_at"]

    def get_last_message(self, obj):
        msgs = getattr(obj, "prefetched_last", None)
        msg = msgs[0] if msgs else obj.messages.order_by("-created_at").first()
        return msg.content[:120] if msg else ""


class AIChatThreadSerializer(_SubjectFieldsMixin, serializers.ModelSerializer):
    messages = AIChatMessageSerializer(many=True, read_only=True)
    # Yaratishda fan kodini ham qabul qilamiz: {"subject_code": "english"}
    subject_code_input = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    lesson = serializers.SerializerMethodField()

    class Meta:
        model = AIChatThread
        fields = ["id", "subject", "subject_code", "subject_name", "subject_code_input", "title", "messages",
                  "lesson", "updated_at"]

    def get_lesson(self, obj):
        from .learner import lesson_state
        return lesson_state(obj) if obj.pk else None
        read_only_fields = ["id", "messages", "updated_at"]

    def validate(self, attrs):
        code = attrs.pop("subject_code_input", None)
        if code:
            from apps.subjects.models import Subject
            subject = Subject.objects.filter(code=code).first()
            if not subject:
                raise serializers.ValidationError({"subject_code": f"'{code}' fani topilmadi"})
            attrs["subject"] = subject
        return attrs


class LearnerMemorySerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    subject_code = serializers.SerializerMethodField()

    class Meta:
        model = LearnerMemory
        fields = ["id", "category", "category_label", "subject_code", "text", "updated_at"]
        read_only_fields = fields

    def get_subject_code(self, obj):
        return obj.subject.code if obj.subject_id else None
