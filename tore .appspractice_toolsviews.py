from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Quiz, QuizAttempt, Flashcard, FlashcardReview
from .serializers import QuizSerializer, FlashcardReviewSerializer, FlashcardSerializer


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.prefetch_related("questions").all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """POST /practice-tools/quizzes/{id}/submit/  {answers: {question_id: choice_index, ...}}

        Odatda javob mahalliy (client-side, offline) tekshiriladi — bu endpoint faqat
        natijani serverga saqlash (QuizAttempt) uchun ishlatiladi, internet qaytganda
        chaqiriladi. Shu sabab bu yerda ham xavfsizlik uchun ballni serverda qayta hisoblaymiz
        (frontend yuborgan ball emas, haqiqiy to'g'ri javoblar asosida)."""
        quiz = self.get_object()
        answers = request.data.get("answers", {})
        questions = list(quiz.questions.all())
        if not questions:
            return Response({"detail": "Bu quizda savollar yo'q."}, status=400)

        correct = 0
        review = []
        for q in questions:
            chosen = answers.get(str(q.id))
            is_correct = chosen is not None and int(chosen) == q.correct_index
            if is_correct:
                correct += 1
            review.append({
                "question_id": q.id, "correct_index": q.correct_index,
                "chosen_index": chosen, "is_correct": is_correct,
            })

        score_percent = round((correct / len(questions)) * 100, 1)
        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz, score_percent=score_percent)
        return Response({
            "attempt_id": attempt.id, "score_percent": score_percent,
            "correct_count": correct, "total": len(questions), "review": review,
        })


class FlashcardReviewViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head"]

    def get_queryset(self):
        return FlashcardReview.objects.filter(user=self.request.user).select_related("flashcard")

    @action(detail=False, methods=["get"])
    def due(self, request):
        # Yangi foydalanuvchida ham kartalar darhol ishlashi uchun
        # mavjud Flashcard lar uchun birinchi review yozuvlarini yaratamiz.
        subject_id = request.query_params.get("subject")
        cards = Flashcard.objects.all()
        if subject_id:
            cards = cards.filter(subject_id=subject_id)
        existing = set(
            self.get_queryset().filter(flashcard__in=cards).values_list("flashcard_id", flat=True)
        )
        now = timezone.now()
        missing = [
            FlashcardReview(user=request.user, flashcard=card, next_review_at=now)
            for card in cards.exclude(id__in=existing)
        ]
        if missing:
            FlashcardReview.objects.bulk_create(missing, ignore_conflicts=True)
        due = self.get_queryset().filter(next_review_at__lte=timezone.now())
        if subject_id:
            due = due.filter(flashcard__subject_id=subject_id)
        return Response(FlashcardReviewSerializer(due, many=True).data)

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        review = self.get_object()
        quality = int(request.data.get("quality", 3))
        review.ease_factor = max(1.3, review.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        review.repetitions = review.repetitions + 1 if quality >= 3 else 0
        review.interval_days = 1 if review.repetitions <= 1 else round(review.interval_days * review.ease_factor)
        review.next_review_at = timezone.now() + timezone.timedelta(days=review.interval_days)
        review.save()
        return Response(FlashcardReviewSerializer(review).data)


class FlashcardViewSet(viewsets.ModelViewSet):
    """Admin uchun Flashcard CRUD; o'quvchi GET orqali kartalar ro'yxatini ko'rishi mumkin."""
    queryset = Flashcard.objects.select_related("subject").all()
    serializer_class = FlashcardSerializer
    http_method_names = ["get", "post", "patch", "delete", "head"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
