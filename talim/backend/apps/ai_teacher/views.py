import logging
import os
import tempfile

from django.conf import settings
from django.db.models import Prefetch
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AIChatMessage, AIChatThread, GeneratedLesson, LearnerMemory
from .serializers import (
    AIChatMessageSerializer, AIChatThreadListSerializer, AIChatThreadSerializer, GeneratedLessonSerializer,
    LearnerMemorySerializer,
)
from .services import chat_with_ai, generate_lesson

logger = logging.getLogger(__name__)

MAX_MESSAGE_CHARS = 4000


class GeneratedLessonViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GeneratedLessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GeneratedLesson.objects.filter(user=self.request.user).select_related("subject", "cefr_level")

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """POST /ai-teacher/lessons/generate/  {subject, cefr_level?}"""
        from apps.subjects.models import Subject, CEFRLevel
        subject = Subject.objects.filter(id=request.data.get("subject")).first()
        if not subject:
            return Response({"detail": "Fan topilmadi"}, status=status.HTTP_400_BAD_REQUEST)
        level = CEFRLevel.objects.filter(id=request.data.get("cefr_level")).first()
        try:
            lesson = generate_lesson(request.user, subject, level)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(GeneratedLessonSerializer(lesson).data, status=status.HTTP_201_CREATED)


class AIChatThreadViewSet(viewsets.ModelViewSet):
    """AI Ustoz suhbatlari.

    GET    /ai-teacher/chat/                 — suhbatlar ro'yxati
    POST   /ai-teacher/chat/                 — yangi suhbat {subject_code_input?: "english"}
    GET    /ai-teacher/chat/{id}/            — suhbat va xabarlar
    PATCH  /ai-teacher/chat/{id}/            — nom yoki fanni o'zgartirish
    DELETE /ai-teacher/chat/{id}/            — o'chirish
    POST   /ai-teacher/chat/{id}/send/       — {message} -> AI Ustoz javobi
    POST   /ai-teacher/chat/{id}/speak/      — multipart audio -> speaking javobi (+ mp3)
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head"]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_serializer_class(self):
        return AIChatThreadListSerializer if self.action == "list" else AIChatThreadSerializer

    def get_queryset(self):
        qs = AIChatThread.objects.filter(user=self.request.user).select_related("subject")
        if self.action == "list":
            return qs.prefetch_related(Prefetch(
                "messages", queryset=AIChatMessage.objects.order_by("-created_at"), to_attr="prefetched_last",
            ))
        return qs.prefetch_related("messages")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """POST /ai-teacher/chat/{id}/send/  {message: str} -> AI javobi"""
        thread = self.get_object()
        text = (request.data.get("message") or "").strip()
        if not text:
            return Response({"detail": "Xabar bo'sh"}, status=status.HTTP_400_BAD_REQUEST)
        if len(text) > MAX_MESSAGE_CHARS:
            return Response({"detail": f"Xabar juda uzun (ko'pi bilan {MAX_MESSAGE_CHARS} belgi)"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            reply = chat_with_ai(thread, text)
        except Exception as e:
            logger.exception("AI chat send failed")
            return Response({"detail": "AI Ustoz hozir javob bera olmadi. Birozdan keyin qayta urinib ko'ring."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        from .learner import lesson_state

        thread.refresh_from_db(fields=["title", "subject", "updated_at"])
        data = AIChatMessageSerializer(reply).data
        data["thread"] = {"id": str(thread.id), "title": thread.title,
                          "subject_code": thread.subject.code if thread.subject_id else None,
                          "lesson": lesson_state(thread)}
        return Response(data)

    @action(detail=True, methods=["post"])
    def voice(self, request, pk=None):
        """POST /ai-teacher/chat/{id}/voice/  multipart: audio — o'zbek/rus/ingliz tilida erkin ovozli savol."""
        return self._audio_turn(request, mode="voice")

    def _audio_turn(self, request, mode):
        from .agent import ClaudeUnavailable
        from .speaking import EmptyAudio, SpeakingUnavailable, speaking_turn, voice_chat_turn

        thread = self.get_object()
        upload = request.FILES.get("audio")
        if not upload:
            return Response({"detail": "Audio fayl yuborilmadi"}, status=status.HTTP_400_BAD_REQUEST)
        if upload.size > settings.SPEAKING_MAX_UPLOAD_MB * 1024 * 1024:
            return Response({"detail": "Audio juda katta"}, status=status.HTTP_400_BAD_REQUEST)
        suffix = os.path.splitext(upload.name or "")[1] or ".webm"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        try:
            for chunk in upload.chunks():
                tmp.write(chunk)
            tmp.close()
            if mode == "voice":
                result = voice_chat_turn(request.user, thread, tmp.name)
            else:
                result = speaking_turn(request.user, thread, tmp.name)
        except SpeakingUnavailable as e:
            return Response({"detail": f"Serverda ovozni tanish ishlamayapti: {e}", "code": "speaking_unavailable"},
                            status=status.HTTP_501_NOT_IMPLEMENTED)
        except EmptyAudio:
            return Response({"detail": "Ovoz eshitilmadi. Mikrofonga yaqinroq gapirib, qayta urinib ko'ring.",
                             "code": "empty_audio"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ClaudeUnavailable:
            return Response({"detail": "AI Ustoz hozir javob bera olmadi. Birozdan keyin qayta urinib ko'ring."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception:
            logger.exception("Audio turn failed (%s)", mode)
            return Response({"detail": "Audioni qayta ishlab bo'lmadi. Brauzer orqali tanishga o'tib ko'ring.",
                             "code": "audio_failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

        from .learner import lesson_state
        payload = {
            "user_message": AIChatMessageSerializer(result["user_message"]).data if result.get("user_message") else None,
            "reply": AIChatMessageSerializer(result["reply"]).data,
            "audio_base64": result["audio_base64"],
            "audio_mime": result["audio_mime"],
            "weak_words": result.get("weak_words", []),
            "lang": result.get("lang"),
            "speech_lang": result.get("speech_lang"),
        }
        thread.refresh_from_db(fields=["title", "subject", "updated_at"])
        payload["thread"] = {"id": str(thread.id), "title": thread.title,
                             "subject_code": thread.subject.code if thread.subject_id else None,
                             "lesson": lesson_state(thread)}
        return Response(payload)

    @action(detail=True, methods=["post"])
    def speak(self, request, pk=None):
        """POST /ai-teacher/chat/{id}/speak/  multipart: audio — til mashqi (Speaking)."""
        return self._audio_turn(request, mode="speaking")

class TutorStatusView(APIView):
    """GET /ai-teacher/status/ — AI va ovoz modullari serverda sozlanganmi."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .speaking import capabilities
        return Response(capabilities())


class LearnerMemoryViewSet(mixins.DestroyModelMixin, viewsets.ReadOnlyModelViewSet):
    """O'quvchi AI Ustoz u haqida nimani eslab qolganini ko'radi va o'chiradi.

    GET    /ai-teacher/memory/         — ro'yxat
    DELETE /ai-teacher/memory/{id}/    — bitta faktni o'chirish
    POST   /ai-teacher/memory/clear/   — hammasini o'chirish
    """
    serializer_class = LearnerMemorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LearnerMemory.objects.filter(user=self.request.user).select_related("subject")

    @action(detail=False, methods=["post"])
    def clear(self, request):
        deleted, _ = self.get_queryset().delete()
        return Response({"deleted": deleted})


class StudyPlanViewSet(viewsets.GenericViewSet):
    """O'quv rejalari (AI Ustoz tuzadi).

    GET    /ai-teacher/plans/                     — faol rejalar (kunlik, haftalik, oylik)
    POST   /ai-teacher/plans/{id}/toggle/         — {item_id, done} bandni belgilash
    DELETE /ai-teacher/plans/{id}/                — rejani o'chirish (arxivlash)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import StudyPlan
        return StudyPlan.objects.filter(user=self.request.user).select_related("subject")

    def list(self, request):
        from .plans import active_plans, serialize_plan
        return Response([serialize_plan(p) for p in active_plans(request.user)])

    def destroy(self, request, pk=None):
        plan = self.get_object()
        plan.is_active = False
        plan.save(update_fields=["is_active", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        from .plans import serialize_plan, set_item_done
        plan = self.get_object()
        result = set_item_done(plan, str(request.data.get("item_id", "")), bool(request.data.get("done", True)))
        if result is None:
            return Response({"detail": "Band topilmadi"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_plan(plan))


class AdminSupportTicketViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """GET/PATCH /ai-teacher/admin/tickets/ — AI Ustoz adminga uzatgan murojaatlar."""
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "patch", "head"]

    def get_queryset(self):
        from .models import SupportTicket
        qs = SupportTicket.objects.select_related("user").order_by("status", "-created_at")
        st = self.request.query_params.get("status")
        return qs.filter(status=st) if st else qs

    def get_serializer_class(self):
        from rest_framework import serializers as s
        from .models import SupportTicket

        class TicketSerializer(s.ModelSerializer):
            username = s.CharField(source="user.username", read_only=True)
            email = s.CharField(source="user.email", read_only=True)
            category_label = s.CharField(source="get_category_display", read_only=True)

            class Meta:
                model = SupportTicket
                fields = ["id", "username", "email", "category", "category_label", "reason", "status", "thread", "created_at"]
                read_only_fields = ["id", "username", "email", "category", "category_label", "reason", "thread", "created_at"]
        return TicketSerializer
