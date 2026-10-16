from rest_framework import serializers

from .models import Lesson, LessonExercise, LessonWord, Story, StoryQuestion


class LessonWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonWord
        fields = ["id", "word", "translation"]


class LessonExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonExercise
        fields = ["id", "kind", "prompt", "bank"]  # 'answer' studentga ko'rinmaydi


class LessonExerciseAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonExercise
        fields = ["id", "kind", "prompt", "bank", "answer", "order"]


class LessonListSerializer(serializers.ModelSerializer):
    level = serializers.CharField(source="cefr_level.code", read_only=True)
    word_count = serializers.IntegerField(source="words.count", read_only=True)
    exercise_count = serializers.IntegerField(source="exercises.count", read_only=True)
    completed = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "title", "level", "order", "word_count", "exercise_count", "completed", "score"]

    def get_progress(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return None
        return obj.progress.filter(user=user).first()

    def get_completed(self, obj):
        p = self.get_progress(obj)
        return bool(p and p.completed)

    def get_score(self, obj):
        p = self.get_progress(obj)
        return {"correct": p.correct, "total": p.total} if p else None


class LessonDetailSerializer(LessonListSerializer):
    words = LessonWordSerializer(many=True, read_only=True)
    exercises = LessonExerciseSerializer(many=True, read_only=True)

    class Meta(LessonListSerializer.Meta):
        fields = LessonListSerializer.Meta.fields + ["explanation", "words", "exercises"]


class LessonAdminSerializer(serializers.ModelSerializer):
    words = LessonWordSerializer(many=True, read_only=True)
    exercises = LessonExerciseAdminSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ["id", "subject", "cefr_level", "order", "title", "explanation", "is_published", "words", "exercises"]


class StoryQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryQuestion
        fields = ["id", "question", "options"]  # 'correct' studentga ko'rinmaydi


class StoryListSerializer(serializers.ModelSerializer):
    level = serializers.CharField(source="cefr_level.code", read_only=True)
    question_count = serializers.IntegerField(source="questions.count", read_only=True)
    my_result = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ["id", "title", "level", "order", "cover_emoji", "cover_color", "question_count", "my_result"]

    def get_my_result(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return None
        r = obj.results.filter(user=user).first()
        return {"correct": r.correct, "total": r.total} if r else None


class StoryDetailSerializer(StoryListSerializer):
    questions = StoryQuestionSerializer(many=True, read_only=True)

    class Meta(StoryListSerializer.Meta):
        fields = StoryListSerializer.Meta.fields + ["text", "questions"]


class StoryAdminSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ["id", "subject", "cefr_level", "order", "title", "text", "cover_emoji", "cover_color",
                  "is_published", "questions"]

    def get_questions(self, obj):
        return [{"id": q.id, "question": q.question, "options": q.options, "correct": q.correct}
                for q in obj.questions.all()]
