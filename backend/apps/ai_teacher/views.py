from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import GeneratedLesson, AIChatThread
from .serializers import GeneratedLessonSerializer, AIChatThreadSerializer, AIChatMessageSerializer
from .services import generate_lesson, chat_with_ai


class GeneratedLessonViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GeneratedLessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GeneratedLesson.objects.filter(user=self.request.user).select_related("subject", "cefr_level")

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """POST /ai-teacher/lessons/generate/  {subject, cefr_level?}"""
        from apps.subjects.models import Subject, CEFRLevel
        subject = Subject.objects.get(id=request.data["subject"])
        level = CEFRLevel.objects.filter(id=request.data.get("cefr_level")).first()
        try:
            lesson = generate_lesson(request.user, subject, level)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(GeneratedLessonSerializer(lesson).data, status=status.HTTP_201_CREATED)


class AIChatThreadViewSet(viewsets.ModelViewSet):
    serializer_class = AIChatThreadSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head"]

    def get_queryset(self):
        return AIChatThread.objects.filter(user=self.request.user).prefetch_related("messages")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """POST /ai-teacher/chat/{id}/send/  {message: str} -> AI javobi"""
        import logging
        thread = self.get_object()
        try:
            reply = chat_with_ai(thread, request.data.get("message", ""))
        except Exception as e:
            logging.getLogger(__name__).exception("AI chat send failed")
            return Response({"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(AIChatMessageSerializer(reply).data)
