from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MathProblem, MathAttempt
from .serializers import MathProblemSerializer, MathAttemptSerializer
from .services import check_answer_with_sympy


class MathProblemViewSet(viewsets.ModelViewSet):
    queryset = MathProblem.objects.select_related("topic").all()
    serializer_class = MathProblemSerializer
    filterset_fields = ["topic", "difficulty"]
    http_method_names = ["get", "post", "patch", "delete", "head"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def create(self, request, *args, **kwargs):
        from .models import MathTopic
        data = request.data.copy()
        topic_name = data.pop("topic_name", None)
        if topic_name and not data.get("topic"):
            topic, _ = MathTopic.objects.get_or_create(name=topic_name if isinstance(topic_name, str) else topic_name[0])
            data["topic"] = topic.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        problem = self.get_object()
        is_correct = check_answer_with_sympy(problem, request.data.get("user_answer", ""))
        attempt = MathAttempt.objects.create(
            user=request.user, problem=problem, session_id=request.data.get("session"),
            user_answer=request.data.get("user_answer", ""), is_correct=is_correct,
            time_spent_seconds=request.data.get("time_spent_seconds", 0),
        )
        return Response(MathAttemptSerializer(attempt).data)

    @action(detail=True, methods=["post"])
    def ai_explain(self, request, pk=None):
        """POST /math/problems/{id}/ai_explain/ — AI Math Teacher: masalani qadam-baqadam tushuntiradi."""
        from apps.ai_teacher.services import call_ai
        problem = self.get_object()
        prompt = (
            f"Quyidagi matematik masalani o'zbek tilida, o'quvchi uchun tushunarli qilib, "
            f"qadam-baqadam yech va oxirida javobni aniq ko'rsat:\n\n{problem.statement}"
        )
        try:
            explanation = call_ai(prompt, system="Sen AI Math Teacher — matematika o'qituvchisisan.")
        except Exception as e:
            explanation = f"AI xizmati vaqtincha mavjud emas: {e}"
        return Response({"problem": problem.id, "explanation": explanation})
