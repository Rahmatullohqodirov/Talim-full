from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    RecommendedVideoViewSet, SavedVideoViewSet, WatchHistoryViewSet, VideoRatingViewSet,
    AdminYoutubeVideoViewSet
)

router = DefaultRouter()
router.register("recommendations", RecommendedVideoViewSet, basename="youtube-recommendation")
router.register("saved", SavedVideoViewSet, basename="youtube-saved")
router.register("history", WatchHistoryViewSet, basename="youtube-history")
router.register("ratings", VideoRatingViewSet, basename="youtube-rating")
router.register("admin/videos", AdminYoutubeVideoViewSet, basename="admin-youtube-video")
urlpatterns = [path("", include(router.urls))]
