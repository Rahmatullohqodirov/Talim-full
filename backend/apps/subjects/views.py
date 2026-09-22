from rest_framework import viewsets, permissions
from .models import Subject
from .serializers import SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    """GET — hamma uchun ochiq. POST/PATCH/DELETE — faqat admin (fanlarni boshqarish)."""
    queryset = Subject.objects.prefetch_related("levels").all()
    serializer_class = SubjectSerializer
    http_method_names = ["get", "post", "patch", "delete", "head"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
