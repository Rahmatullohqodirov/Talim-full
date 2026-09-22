from rest_framework import viewsets, permissions
from .models import ExternalCourse, SavedExternalCourse
from .serializers import ExternalCourseSerializer, SavedExternalCourseSerializer


class ExternalCourseViewSet(viewsets.ModelViewSet):
    """GET /integrations/courses/ — LinkedIn Learning, Coursera, Khan Academy, Google Books kurslari."""
    queryset = ExternalCourse.objects.select_related("subject").all()
    serializer_class = ExternalCourseSerializer
    filterset_fields = ["source", "subject"]
    http_method_names = ["get", "post", "patch", "delete", "head"]

    def get_permissions(self):
        if self.request.method in ("POST", "PATCH", "DELETE"):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]


class SavedExternalCourseViewSet(viewsets.ModelViewSet):
    """Foydalanuvchi sevimli tashqi kurslari — GET/POST/DELETE /integrations/saved/"""
    serializer_class = SavedExternalCourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head"]

    def get_queryset(self):
        return SavedExternalCourse.objects.filter(user=self.request.user).select_related("course")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
