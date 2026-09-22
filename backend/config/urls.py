from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.subjects.views import SubjectViewSet
from apps.session.views import LearningSessionViewSet
from apps.math_practice.views import MathProblemViewSet
from apps.avatars.views import AvatarViewSet
from apps.practice_tools.views import QuizViewSet, FlashcardReviewViewSet, FlashcardViewSet

router = DefaultRouter()
router.register("subjects", SubjectViewSet)
router.register("sessions", LearningSessionViewSet, basename="session")
router.register("math/problems", MathProblemViewSet)
router.register("avatars", AvatarViewSet)
router.register("quizzes", QuizViewSet)
router.register("flashcards/reviews", FlashcardReviewViewSet, basename="flashcard-review")
router.register("flashcards/items", FlashcardViewSet, basename="flashcard-item")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/", include(router.urls)),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/statistics/", include("apps.statistics.urls")),
    path("api/v1/learning-path/", include("apps.learning_path.urls")),
    path("api/v1/leaderboard/", include("apps.gamification.urls")),
    path("api/v1/youtube/", include("apps.youtube_recommendations.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/ai-teacher/", include("apps.ai_teacher.urls")),
    path("api/v1/integrations/", include("apps.integrations.urls")),
]
