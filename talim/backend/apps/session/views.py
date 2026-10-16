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

    def create(self, request, *args, **kwargs):
        """Bir xil fan + avatar + vaziyat uchun oxirgi 6 soatdagi faol sessiya qayta ishlatiladi
        (har kirishda bo'sh sessiya yaratilmasligi uchun). Premium avatar faqat premium o'quvchiga."""
        from datetime import timedelta
        from apps.avatars.models import Avatar

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar = serializer.validated_data.get("avatar")
        if avatar and avatar.is_premium_only and not request.user.is_premium:
            return Response({"detail": "Bu avatar faqat Premium obunada.", "code": "premium_required"},
                            status=status.HTTP_403_FORBIDDEN)
        scenario = (request.data.get("scenario") or "free")[:30]
        existing = LearningSession.objects.filter(
            user=request.user, subject=serializer.validated_data["subject"], avatar=avatar, scenario=scenario,
            status=LearningSession.Status.ACTIVE, started_at__gte=timezone.now() - timedelta(hours=6),
        ).order_by("-started_at").first()
        if existing and not request.data.get("fresh"):
            return Response(LearningSessionSerializer(existing).data, status=status.HTTP_200_OK)
        session = serializer.save(user=request.user, scenario=scenario)
        return Response(LearningSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def add_turn(self, request, pk=None):
        session = self.get_object()
        serializer = TranscriptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(session=session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def chat(self, request, pk=None):
        """POST /sessions/{id}/chat/  {message, accent} — avatar javobi (+ ovoz va tuzatishlar)."""
        from .avatar_chat import generate_reply, synthesize_reply

        session = self.get_object()
        message = (request.data.get("message") or "").strip()[:1000]
        accent = request.data.get("accent", "american")
        if not message:
            return Response({"detail": "Xabar bo'sh."}, status=status.HTTP_400_BAD_REQUEST)

        user_turn = Transcript.objects.create(session=session, speaker=Transcript.Speaker.USER, text=message)
        text, feedback = generate_reply(session, accent)
        if not text:
            text = "Sorry, I didn't catch that. Could you say it again?"
        avatar_turn = Transcript.objects.create(
            session=session, speaker=Transcript.Speaker.AVATAR, text=text, feedback=feedback,
        )
        if len(message.split()) >= 3:
            from apps.gamification.services import record_activity
            record_activity(request.user, session.subject, points=2, source="speaking")
        speech_lang, audio = (None, None)
        if request.data.get("voice", True):
            speech_lang, audio = synthesize_reply(session, accent, text)
        return Response({
            "user_turn": TranscriptSerializer(user_turn).data,
            "reply": TranscriptSerializer(avatar_turn).data,
            "audio_base64": audio,
            "speech_lang": speech_lang,
        })

    @action(detail=False, methods=["get"])
    def scenarios(self, request):
        """GET /sessions/scenarios/ — avatar bilan suhbat vaziyatlari."""
        from .avatar_chat import SCENARIOS
        return Response([{"key": k, "label": v[0]} for k, v in SCENARIOS.items()])

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        session = self.get_object()
        session.ended_at = timezone.now()
        session.duration_seconds = int((session.ended_at - session.started_at).total_seconds())
        session.status = LearningSession.Status.COMPLETED
        session.save()
        return Response(LearningSessionSerializer(session).data)
