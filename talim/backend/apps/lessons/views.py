from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Lesson, LessonExercise, Story, StoryQuestion, UserLessonProgress, UserStoryResult
from .serializers import (
    LessonAdminSerializer, LessonDetailSerializer, LessonListSerializer,
    StoryAdminSerializer, StoryDetailSerializer, StoryListSerializer,
)


def _filtered(qs, request):
    subject = request.query_params.get("subject")
    level = request.query_params.get("level") or request.query_params.get("cefr")
    if subject:
        qs = qs.filter(subject__code=subject)
    if level:
        qs = qs.filter(cefr_level__code=level.upper())
    return qs


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /lessons/?subject=english&level=A1 — darslar ro'yxati va bitta dars tafsiloti."""
    queryset = Lesson.objects.filter(is_published=True).select_related("subject", "cefr_level")
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _filtered(super().get_queryset(), self.request).prefetch_related("words", "exercises", "progress")

    def get_serializer_class(self):
        return LessonDetailSerializer if self.action == "retrieve" else LessonListSerializer

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """POST /lessons/{id}/submit/  {answers: {exercise_id: "foydalanuvchi javobi"}}

        Javoblar serverda, mashqning yashirin `answer` maydoniga solishtirib tekshiriladi —
        mijoz o'zi "to'g'ri" deb aytib kirib olmasligi uchun.
        """
        lesson = self.get_object()
        answers = request.data.get("answers") or {}
        exercises = list(lesson.exercises.all())
        correct = 0
        for ex in exercises:
            given = str(answers.get(str(ex.id), "")).strip().lower()
            if given and given == ex.answer.strip().lower():
                correct += 1
        total = len(exercises)
        progress, _ = UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        progress.correct, progress.total = correct, total
        completed = total > 0 and correct >= max(1, round(total * 0.6))
        progress.completed = completed or progress.completed
        points = 0
        if completed and not progress.points_awarded:
            from apps.gamification.services import record_activity
            points = 15
            record_activity(request.user, lesson.subject, points=points, source="lesson")
            progress.points_awarded = True
        progress.save()
        return Response({
            "correct": correct, "total": total, "completed": progress.completed, "points": points,
            "answers": {str(ex.id): ex.answer for ex in exercises},
        })


class StoryViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /stories/?subject=english&level=A1 — "Tinglang va o'qing" kutubxonasi."""
    queryset = Story.objects.filter(is_published=True).select_related("subject", "cefr_level")
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _filtered(super().get_queryset(), self.request).prefetch_related("questions", "results")

    def get_serializer_class(self):
        return StoryDetailSerializer if self.action == "retrieve" else StoryListSerializer

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """POST /stories/{id}/submit/  {answers: {question_id: "tanlangan variant"}}"""
        story = self.get_object()
        answers = request.data.get("answers") or {}
        questions = list(story.questions.all())
        correct = sum(1 for q in questions if str(answers.get(str(q.id), "")).strip().lower() == q.correct.strip().lower())
        total = len(questions)
        result, _ = UserStoryResult.objects.get_or_create(user=request.user, story=story)
        improved = correct > result.correct or result.total == 0
        if improved:
            result.correct, result.total = correct, total
        points = 0
        if correct >= max(1, round(total * 0.6)) and not result.points_awarded:
            from apps.gamification.services import record_activity
            points = 10
            record_activity(request.user, story.subject, points=points, source="story")
            result.points_awarded = True
        result.save()
        return Response({
            "correct": correct, "total": total, "points": points,
            "answers": {str(q.id): q.correct for q in questions},
        })


class AdminLessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related("subject", "cefr_level").prefetch_related("words", "exercises")
    serializer_class = LessonAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["subject", "cefr_level", "is_published"]

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """POST /lessons/admin/lessons/generate/  {subject: "english", level: "A1"} — AI bilan darslar to'plamini tuzadi."""
        from apps.subjects.models import CEFRLevel, Subject
        from .services import generate_lessons_for_level

        subject = Subject.objects.filter(code=request.data.get("subject", "english")).first()
        level = CEFRLevel.objects.filter(subject=subject, code=str(request.data.get("level", "A1")).upper()).first() if subject else None
        if not subject or not level:
            return Response({"detail": "Fan yoki daraja topilmadi."}, status=status.HTTP_400_BAD_REQUEST)
        created = generate_lessons_for_level(subject, level)
        return Response({"created": created})


class AdminStoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.select_related("subject", "cefr_level").prefetch_related("questions")
    serializer_class = StoryAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["subject", "cefr_level", "is_published"]

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """POST /lessons/admin/stories/generate/  {subject: "english", level: "A1"}"""
        from apps.subjects.models import CEFRLevel, Subject
        from .services import generate_stories_for_level

        subject = Subject.objects.filter(code=request.data.get("subject", "english")).first()
        level = CEFRLevel.objects.filter(subject=subject, code=str(request.data.get("level", "A1")).upper()).first() if subject else None
        if not subject or not level:
            return Response({"detail": "Fan yoki daraja topilmadi."}, status=status.HTTP_400_BAD_REQUEST)
        created = generate_stories_for_level(subject, level)
        return Response({"created": created})
