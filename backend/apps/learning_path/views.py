from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import LearningPath
from .serializers import LearningPathSerializer
from .services import generate_personalized_path


class ActiveLearningPathView(generics.ListAPIView):
    """GET /learning-path/?subject=<code>"""
    serializer_class = LearningPathSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = LearningPath.objects.filter(user=self.request.user, is_active=True).prefetch_related("items")
        subject = self.request.query_params.get("subject")
        return qs.filter(subject__code=subject) if subject else qs


class GeneratePathView(APIView):
    """POST /learning-path/generate/  {subject: id} -> AI orqali yangi shaxsiy yo'nalish tuzadi."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from apps.subjects.models import Subject
        subject = Subject.objects.get(id=request.data["subject"])
        path = generate_personalized_path(request.user, subject)
        return Response(LearningPathSerializer(path).data, status=status.HTTP_201_CREATED)
