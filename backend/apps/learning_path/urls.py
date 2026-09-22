from django.urls import path
from .views import ActiveLearningPathView, GeneratePathView

urlpatterns = [
    path("", ActiveLearningPathView.as_view(), name="learning-path-active"),
    path("generate/", GeneratePathView.as_view(), name="learning-path-generate"),
]
