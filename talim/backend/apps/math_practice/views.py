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
        if self.request.method == "GET" or getattr(self, "action", None) in ("submit", "ai_explain"):
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

    def get_queryset(self):
        from django.db.models import Exists, OuterRef
        qs = MathProblem.objects.select_related("topic").order_by("topic__name", "difficulty", "created_at")
        user = self.request.user
        if user.is_authenticated:
            qs = qs.annotate(
                solved=Exists(MathAttempt.objects.filter(user=user, problem=OuterRef("pk"), is_correct=True)),
                tried=Exists(MathAttempt.objects.filter(user=user, problem=OuterRef("pk"))),
            )
        return qs

    @action(detail=False, methods=["get"])
    def progress(self, request):
        """GET /math/problems/progress/ — mavzular bo'yicha: jami, yechilgan, urinilgan."""
        from django.db.models import Count, Q
        from .models import MathTopic
        rows = (
            MathTopic.objects.annotate(
                total=Count("problems", distinct=True),
                solved=Count("problems", filter=Q(problems__attempts__user=request.user, problems__attempts__is_correct=True), distinct=True),
                tried=Count("problems", filter=Q(problems__attempts__user=request.user), distinct=True),
            ).filter(total__gt=0).order_by("name")
        )
        return Response([{"id": str(t.id), "name": t.name, "total": t.total, "solved": t.solved, "tried": t.tried} for t in rows])

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """POST /math/problems/{id}/submit/  {user_answer} yoki {self_correct: true|false} (isbot masalalari)."""
        from .services import check_answer

        problem = self.get_object()
        user_answer = str(request.data.get("user_answer", ""))[:500]
        result = check_answer(problem, user_answer)
        if result is None:
            if "self_correct" not in request.data:
                return Response({"needs_self_check": True, "is_correct": None,
                                 "solution_steps": problem.solution_steps})
            result = bool(request.data.get("self_correct"))
        already = MathAttempt.objects.filter(user=request.user, problem=problem, is_correct=True).exists()
        attempts_before = MathAttempt.objects.filter(user=request.user, problem=problem).count()
        try:
            spent = max(0, min(3600, int(request.data.get("time_spent_seconds", 0) or 0)))
        except (TypeError, ValueError):
            spent = 0
        attempt = MathAttempt.objects.create(
            user=request.user, problem=problem, session_id=request.data.get("session") or None,
            user_answer=user_answer, is_correct=result, time_spent_seconds=spent,
        )
        points = 0
        if result and not already:  # bir masala uchun ball faqat bir marta
            from apps.gamification.services import record_activity
            from apps.subjects.models import Subject
            points = {1: 10, 2: 15, 3: 20}.get(problem.difficulty, 10)
            record_activity(request.user, Subject.objects.filter(code="math").first(), points=points, source="math")
        data = MathAttemptSerializer(attempt).data
        data.update({
            "points": points,
            "attempt_number": attempts_before + 1,
            # 2 marta xato qilgach yoki to'g'ri topgach — to'g'ri javob ko'rsatiladi
            "answers": problem.answers if (result or attempts_before + 1 >= 2) else None,
        })
        return Response(data)

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
