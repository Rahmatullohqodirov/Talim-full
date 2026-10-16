from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import ExternalCourseViewSet, SavedExternalCourseViewSet

router = DefaultRouter()
router.register("courses", ExternalCourseViewSet, basename="external-course")
router.register("saved", SavedExternalCourseViewSet, basename="saved-external-course")

urlpatterns = [path("", include(router.urls))]
