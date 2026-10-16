from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminLessonViewSet, AdminStoryViewSet, LessonViewSet, StoryViewSet

router = DefaultRouter()
router.register("lessons", LessonViewSet, basename="lesson")
router.register("stories", StoryViewSet, basename="story")
router.register("admin/lessons", AdminLessonViewSet, basename="admin-lesson")
router.register("admin/stories", AdminStoryViewSet, basename="admin-story")

urlpatterns = [
    path("", include(router.urls)),
]
