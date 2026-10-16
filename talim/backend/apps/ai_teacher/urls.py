from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import GeneratedLessonViewSet, AIChatThreadViewSet, LearnerMemoryViewSet, StudyPlanViewSet, TutorStatusView, AdminSupportTicketViewSet

router = DefaultRouter()
router.register("lessons", GeneratedLessonViewSet, basename="ai-lesson")
router.register("chat", AIChatThreadViewSet, basename="ai-chat")
router.register("memory", LearnerMemoryViewSet, basename="ai-memory")
router.register("plans", StudyPlanViewSet, basename="ai-plan")
router.register("admin/tickets", AdminSupportTicketViewSet, basename="ai-admin-ticket")

urlpatterns = [
    path("status/", TutorStatusView.as_view(), name="ai-status"),
    path("", include(router.urls)),
]
