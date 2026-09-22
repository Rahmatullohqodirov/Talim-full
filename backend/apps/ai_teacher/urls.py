from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import GeneratedLessonViewSet, AIChatThreadViewSet

router = DefaultRouter()
router.register("lessons", GeneratedLessonViewSet, basename="ai-lesson")
router.register("chat", AIChatThreadViewSet, basename="ai-chat")

urlpatterns = [path("", include(router.urls))]
