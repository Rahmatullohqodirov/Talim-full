from rest_framework import serializers
from .models import ExternalCourse, SavedExternalCourse


class ExternalCourseSerializer(serializers.ModelSerializer):
    source_label = serializers.CharField(source="get_source_display", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True, default=None)

    class Meta:
        model = ExternalCourse
        fields = [
            "id", "source", "source_label", "subject", "subject_name",
            "title", "description", "url", "thumbnail_url", "level", "is_premium_only",
        ]


class SavedExternalCourseSerializer(serializers.ModelSerializer):
    course = ExternalCourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(queryset=ExternalCourse.objects.all(), source="course", write_only=True)

    class Meta:
        model = SavedExternalCourse
        fields = ["id", "course", "course_id", "created_at"]
