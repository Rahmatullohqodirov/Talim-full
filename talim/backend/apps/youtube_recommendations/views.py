from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import RecommendedVideo, SavedVideo, WatchHistory, VideoRating, YoutubeVideo
from .serializers import (
    RecommendedVideoSerializer, SavedVideoSerializer, WatchHistorySerializer, VideoRatingSerializer,
    YoutubeVideoSerializer,
)


class RecommendedVideoViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """GET /youtube/recommendations/?session=<id> — AI tomonidan tavsiya qilingan videolar."""
    serializer_class = RecommendedVideoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = RecommendedVideo.objects.filter(user=self.request.user).select_related("video")
        session_id = self.request.query_params.get("session")
        if session_id:
            return qs.filter(session_id=session_id)

        # Recommendation seed bo'lmagan yangi foydalanuvchida ham katalog bo'sh qolmasin.
        if not qs.exists():
            videos = list(
                YoutubeVideo.objects.all().order_by("-avg_rating", "-view_count")[:10]
            )
            for rank, video in enumerate(videos, start=1):
                RecommendedVideo.objects.get_or_create(
                    user=self.request.user,
                    video=video,
                    defaults={
                        "reason": RecommendedVideo.Reason.LEVEL_MATCH,
                        "rank": rank,
                    },
                )
            qs = RecommendedVideo.objects.filter(user=self.request.user).select_related("video")
        return qs.order_by("rank", "-created_at")

    @action(detail=True, methods=["post"])
    def click(self, request, pk=None):
        """POST /youtube/recommendations/{id}/click/ — tavsiya bosilganini belgilaydi (statistikaga)."""
        rec = self.get_object()
        rec.was_clicked = True
        rec.save()
        return Response(RecommendedVideoSerializer(rec).data)


class SavedVideoViewSet(viewsets.ModelViewSet):
    """Sevimli videolar — GET/POST/DELETE /youtube/saved/"""
    serializer_class = SavedVideoSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head"]

    def get_queryset(self):
        return SavedVideo.objects.filter(user=self.request.user).select_related("video")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WatchHistoryViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Ko'rilgan videolar tarixi — GET/POST /youtube/history/"""
    serializer_class = WatchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WatchHistory.objects.filter(user=self.request.user).select_related("video")

    def perform_create(self, serializer):
        from django.utils import timezone
        from apps.gamification.services import record_activity

        video = serializer.validated_data["video"]
        first_today = not WatchHistory.objects.filter(
            user=self.request.user, video=video, watched_at__date=timezone.localdate()).exists()
        history = serializer.save(user=self.request.user)
        if first_today:  # bir videoni qayta-qayta ochib ball yig'ishning oldini olamiz
            record_activity(self.request.user, video.subject, points=2, source="video")
        video = history.video
        video.view_count = video.view_count + 1
        video.save(update_fields=["view_count"])


class VideoRatingViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Video baholash — POST /youtube/ratings/ (signal orqali YoutubeVideo.avg_rating yangilanadi)."""
    serializer_class = VideoRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VideoRating.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AdminYoutubeVideoViewSet(viewsets.ModelViewSet):
    """GET/POST/PATCH/DELETE /youtube/admin/videos/ — video kutubxonasini to'liq boshqarish
    (avtomatik topilganlarni ko'rish + admin qo'lda video qo'shishi/tahrirlashi/o'chirishi mumkin)."""
    queryset = YoutubeVideo.objects.select_related("subject").all()
    serializer_class = YoutubeVideoSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "post", "patch", "delete", "head"]
    filterset_fields = ["subject", "difficulty", "language"]

    def create(self, request, *args, **kwargs):
        import re
        data = request.data.copy()
        raw = str(data.get("youtube_id", "")).strip()
        m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([\w-]{11})", raw)
        data["youtube_id"] = m.group(1) if m else raw
        if not data.get("thumbnail_url") and re.fullmatch(r"[\w-]{11}", data["youtube_id"] or ""):
            data["thumbnail_url"] = f"https://i.ytimg.com/vi/{data['youtube_id']}/hqdefault.jpg"
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


class YoutubeSearchView(APIView):
    """GET /youtube/search/?q=present+perfect&duration=medium

    q bo'sh bo'lsa — o'quvchi darajasiga mos tayyor so'rovlar (suggestions) qaytadi.
    YouTube kaliti yo'q yoki limit tugagan bo'lsa — bazadagi videolar ichidan qidiradi.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "youtube_search"

    def get(self, request):
        from django.db.models import Q
        from .services import YoutubeSearchError, search_suggestions, youtube_search

        q = (request.query_params.get("q") or "").strip()[:120]
        suggestions = search_suggestions(request.user)
        if not q:
            return Response({"query": "", "results": [], "source": None, **suggestions})
        duration = request.query_params.get("duration")
        try:
            results = youtube_search(q, duration=duration)
            return Response({"query": q, "results": results, "source": "youtube", **suggestions})
        except YoutubeSearchError as e:
            words = [w for w in q.split() if len(w) > 2][:4]
            local = YoutubeVideo.objects.all()
            if words:
                cond = Q()
                for w in words:
                    cond |= Q(title__icontains=w) | Q(channel_title__icontains=w)
                local = local.filter(cond)
            return Response({
                "query": q,
                "results": YoutubeVideoSerializer(local.order_by("-view_count")[:12], many=True).data,
                "source": "local",
                "notice": f"{e} — platformadagi saqlangan videolar ichidan ko'rsatilmoqda.",
                "error_code": e.code,
                **suggestions,
            })
