from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LearningSession, Transcript
from .serializers import LearningSessionSerializer, TranscriptSerializer


class LearningSessionViewSet(viewsets.ModelViewSet):
    serializer_class = LearningSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head"]

    def get_queryset(self):
        return LearningSession.objects.filter(user=self.request.user).select_related("subject", "avatar")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def add_turn(self, request, pk=None):
        session = self.get_object()
        serializer = TranscriptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(session=session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def chat(self, request, pk=None):
        """POST /sessions/{id}/chat/ — ingliz tili avatarining AI javobi."""
        from apps.ai_teacher.services import call_ai

        session = self.get_object()
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response({"detail": "message majburiy."}, status=status.HTTP_400_BAD_REQUEST)

        user_turn = Transcript.objects.create(
            session=session,
            speaker=Transcript.Speaker.USER,
            text=message,
        )
        history = session.turns.order_by("created_at").values("speaker", "text")
        prompt = "\n".join(f"{item['speaker']}: {item['text']}" for item in history)
        system = (
            "Sen ingliz tili bo'yicha samimiy AI avatar-repetitorsan. "
            "O'quvchi bilan faqat ingliz tilida suhbat qil. "
            "Javobni qisqa va tabiiy ber, xatolarini muloyim tuzat, keyin suhbatni davom ettiruvchi savol ber."
        )
        reply_text = call_ai(prompt, system=system)
        avatar_turn = Transcript.objects.create(
            session=session,
            speaker=Transcript.Speaker.AVATAR,
            text=reply_text,
        )
        return Response({
            "user_turn": TranscriptSerializer(user_turn).data,
            "reply": TranscriptSerializer(avatar_turn).data,
        })

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        session = self.get_object()
        session.ended_at = timezone.now()
        session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
        session.status = LearningSession.Status.COMPLETED
        session.save()
        return Response(LearningSessionSerializer(session).data)
