from datetime import timedelta

from django.db.models import Count, Max, Q
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.gamification.services import record_activity
from .models import Flashcard, FlashcardReview, Quiz, QuizAttempt
from .serializers import (
    FlashcardReviewSerializer, FlashcardSerializer, QuizListSerializer, QuizSerializer,
)

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


# ======================================================================
# QUIZ
# ======================================================================

class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /quizzes/?level=B1&category=grammar&subject=english — yengil ro'yxat (savollarsiz)
    GET /quizzes/levels/ — darajalar bo'yicha soni, o'quvchi darajasi va progress
    GET /quizzes/{id}/ — savollar bilan
    POST /quizzes/{id}/submit/ — natija
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return QuizListSerializer if self.action == "list" else QuizSerializer

    def get_queryset(self):
        qs = Quiz.objects.select_related("subject", "cefr_level")
        if not self.request.user.is_staff:
            qs = qs.filter(is_published=True)
        if self.action != "list":
            return qs.prefetch_related("questions")
        p = self.request.query_params
        if p.get("subject"):
            qs = qs.filter(subject__code=p["subject"])
        level = (p.get("level") or "").upper()
        if level == "NONE":
            qs = qs.filter(cefr_level__isnull=True)
        elif level:
            qs = qs.filter(cefr_level__code=level)
        cat = p.get("category")
        if cat == "vocabulary":
            qs = qs.filter(Q(title__icontains="vocabulary") | Q(title__icontains="so'z"))
        elif cat == "grammar":
            qs = qs.filter(Q(title__icontains="grammar") | Q(title__icontains="simple") |
                           Q(title__icontains="predlog") | Q(title__icontains="sifat"))
        if p.get("search"):
            qs = qs.filter(title__icontains=p["search"])
        user = self.request.user
        return qs.annotate(
            question_count=Count("questions", distinct=True),
            best_score=Max("attempts__score_percent", filter=Q(attempts__user=user)),
            attempts_n=Count("attempts", filter=Q(attempts__user=user), distinct=True),
        ).order_by("cefr_level__order", "title")

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        data = QuizListSerializer(qs, many=True).data
        # Bir xil nomli bo'limlarni tabiiy tartibda (Bo'lim 2 < Bo'lim 10)
        import re
        data.sort(key=lambda r: (LEVEL_ORDER.index(r["level"]) if r["level"] in LEVEL_ORDER else 9,
                                 r["category"], [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", r["title"])]))
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        from .quiz_builder import ensure_quiz_ready
        quiz = self.get_object()
        if ensure_quiz_ready(quiz):
            quiz = self.get_queryset().get(pk=quiz.pk)
        return Response(QuizSerializer(quiz).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def publish(self, request, pk=None):
        """POST /quizzes/{id}/publish/  {is_published: bool} — admin."""
        quiz = Quiz.objects.get(pk=pk)
        quiz.is_published = bool(request.data.get("is_published", True))
        quiz.save(update_fields=["is_published"])
        return Response({"id": str(quiz.id), "is_published": quiz.is_published})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def rebuild(self, request, pk=None):
        """POST /quizzes/{id}/rebuild/ — admin: meta-savolli quizni haqiqiy savollarga aylantirish (AI)."""
        from .quiz_builder import kind_of, rebuild_grammar_quiz, rebuild_vocabulary_quiz
        quiz = Quiz.objects.get(pk=pk)
        kind = kind_of(quiz)
        ok = rebuild_vocabulary_quiz(quiz) if kind == "vocab" else rebuild_grammar_quiz(quiz) if kind == "grammar" else False
        quiz.refresh_from_db()
        return Response({"rebuilt": ok, "is_published": quiz.is_published,
                         "detail": None if ok else "Qayta tuzib bo'lmadi (AI kaliti yoki quiz turi)."},
                        status=200 if ok else 400)

    @action(detail=False, methods=["get"])
    def levels(self, request):
        from apps.subjects.models import UserSubjectLevel

        subject = request.query_params.get("subject", "english")
        user = request.user
        rows = (
            Quiz.objects.filter(subject__code=subject, is_published=True)
            .values("cefr_level__code")
            .annotate(total=Count("id", distinct=True),
                      done=Count("id", filter=Q(attempts__user=user, attempts__score_percent__gte=70), distinct=True))
        )
        by_code = {r["cefr_level__code"]: r for r in rows}
        mine = UserSubjectLevel.objects.filter(user=user, subject__code=subject).select_related("current_level").first()
        result = [
            {"level": code, "total": by_code.get(code, {}).get("total", 0), "passed": by_code.get(code, {}).get("done", 0)}
            for code in LEVEL_ORDER
        ]
        if None in by_code:
            result.append({"level": None, "total": by_code[None]["total"], "passed": by_code[None]["done"]})
        return Response({
            "levels": result,
            "my_level": mine.current_level.code if mine and mine.current_level else None,
        })

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """POST /quizzes/{id}/submit/  {answers: {question_id: choice_index}}

        Javoblar serverda qayta tekshiriladi. Har bir to'g'ri javob — 10 ball.
        """
        quiz = self.get_object()
        answers = request.data.get("answers", {}) or {}
        questions = list(quiz.questions.all())
        if not questions:
            return Response({"detail": "Bu quizda savollar yo'q."}, status=400)

        correct, review = 0, []
        for q in questions:
            chosen = answers.get(str(q.id))
            try:
                chosen = int(chosen) if chosen is not None else None
            except (TypeError, ValueError):
                chosen = None
            ok = chosen is not None and chosen == q.correct_index
            correct += ok
            review.append({"question_id": str(q.id), "correct_index": q.correct_index,
                           "chosen_index": chosen, "is_correct": ok})

        score = round(correct / len(questions) * 100, 1)
        best_before = QuizAttempt.objects.filter(user=request.user, quiz=quiz).aggregate(m=Max("score_percent"))["m"]
        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz, score_percent=score)

        # Bir quizni qayta-qayta yechib ball "ishlab olish"ning oldini olish: faqat yaxshilangan qismi uchun ball
        prev_correct = round((best_before or 0) / 100 * len(questions))
        earned = max(0, correct - prev_correct) * 10
        # Vaqtni ActivityTracker (frontend) yozadi, bu yerda faqat sessiya va ball
        res = record_activity(request.user, quiz.subject, points=earned, sessions=1, source="quiz")

        return Response({
            "attempt_id": str(attempt.id),
            "score_percent": score,
            "correct_count": correct,
            "total": len(questions),
            "earned_points": earned,
            "total_points": res["total_points"],
            "streak": res["streak"],
            "review": review,
        })


# ======================================================================
# FLASHCARD (takrorlash: SM-2 algoritmi, 4 ta baho)
# ======================================================================

AGAIN, HARD, GOOD, EASY = 1, 3, 4, 5
MASTERED_DAYS = 21


def schedule(review, quality):
    """Yangi (ease, repetitions, interval_days, next_review_at) — saqlamasdan hisoblaydi."""
    now = timezone.now()
    ease = review.ease_factor
    reps = review.repetitions
    interval = review.interval_days
    if quality < 3:
        return max(1.3, ease - 0.2), 0, 0, now + timedelta(minutes=10)
    ease = max(1.3, ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
    reps += 1
    if reps == 1:
        interval = {HARD: 1, GOOD: 2, EASY: 4}.get(quality, 2)
    elif reps == 2:
        interval = {HARD: 2, GOOD: 3, EASY: 6}.get(quality, 3)
    else:
        mult = {HARD: 1.2, GOOD: ease, EASY: ease * 1.3}.get(quality, ease)
        interval = max(interval + 1, round(max(interval, 1) * mult))
    return ease, reps, interval, now + timedelta(days=interval)


def interval_label(quality, review):
    _, _, days, _ = schedule(review, quality)
    if days == 0:
        return "10 daq"
    if days < 30:
        return f"{days} kun"
    return f"{round(days / 30)} oy"


class FlashcardReviewViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head"]

    def get_queryset(self):
        return FlashcardReview.objects.filter(user=self.request.user).select_related("flashcard")

    def _stats(self, cards):
        user = self.request.user
        reviews = FlashcardReview.objects.filter(user=user, flashcard__in=cards)
        total = cards.count()
        started = reviews.filter(repetitions__gt=0)
        today = timezone.localdate()
        return {
            "total": total,
            "new": total - started.count(),
            "learning": started.filter(interval_days__lt=MASTERED_DAYS).count(),
            "mastered": started.filter(interval_days__gte=MASTERED_DAYS).count(),
            "due_now": started.filter(next_review_at__lte=timezone.now()).count(),
            "reviewed_today": reviews.filter(updated_at__date=today, repetitions__gt=0).count(),
        }

    def _with_intervals(self, reviews):
        data = FlashcardReviewSerializer(reviews, many=True).data
        for row, r in zip(data, reviews):
            row["intervals"] = {str(q): interval_label(q, r) for q in (AGAIN, HARD, GOOD, EASY)}
        return data

    @action(detail=False, methods=["get"])
    def session(self, request):
        """GET /flashcards/reviews/session/?subject=<id>&new=10&limit=30

        Takrorlash vaqti kelgan kartalar + bir nechta yangi karta (hammasi birdaniga emas).
        """
        p = request.query_params
        new_limit = min(30, max(0, int(p.get("new", 10) or 10)))
        limit = min(100, max(5, int(p.get("limit", 30) or 30)))
        cards = Flashcard.objects.all()
        if p.get("subject"):
            cards = cards.filter(subject_id=p["subject"])

        now = timezone.now()
        mine = self.get_queryset().filter(flashcard__in=cards)
        due = list(mine.filter(repetitions__gt=0, next_review_at__lte=now).order_by("next_review_at")[:limit])

        new_rows = list(mine.filter(repetitions=0).order_by("created_at")[:new_limit])
        if len(new_rows) < new_limit:
            have = mine.values_list("flashcard_id", flat=True)
            fresh = list(cards.exclude(id__in=have).order_by("created_at")[: new_limit - len(new_rows)])
            FlashcardReview.objects.bulk_create(
                [FlashcardReview(user=request.user, flashcard=c, next_review_at=now) for c in fresh],
                ignore_conflicts=True,
            )
            new_rows += list(self.get_queryset().filter(flashcard__in=fresh))

        return Response({
            "cards": self._with_intervals(due + new_rows[: max(0, limit - len(due))]),
            "stats": self._stats(cards),
        })

    @action(detail=False, methods=["get"])
    def due(self, request):
        """Eski frontend uchun: faqat takrorlash vaqti kelganlar + 10 ta yangi."""
        return self.session(request)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        cards = Flashcard.objects.all()
        if request.query_params.get("subject"):
            cards = cards.filter(subject_id=request.query_params["subject"])
        return Response(self._stats(cards))

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        """POST /flashcards/reviews/{id}/grade/  {quality: 1|3|4|5}  (Qayta | Qiyin | Yaxshi | Oson)"""
        review = self.get_object()
        try:
            quality = int(request.data.get("quality", GOOD))
        except (TypeError, ValueError):
            quality = GOOD
        quality = min(5, max(0, quality))
        was_new = review.repetitions == 0
        review.ease_factor, review.repetitions, review.interval_days, review.next_review_at = schedule(review, quality)
        review.save()

        points = 0
        if quality >= 3:
            points = 3 if was_new else 2
        res = record_activity(request.user, review.flashcard.subject, points=points, source="flashcard")
        data = FlashcardReviewSerializer(review).data
        data.update({"earned_points": points, "streak": res["streak"],
                     "again": quality < 3, "next_in": interval_label(quality, review) if quality < 3 else
                     (f"{review.interval_days} kun" if review.interval_days < 30 else f"{round(review.interval_days / 30)} oy")})
        return Response(data)


class FlashcardViewSet(viewsets.ModelViewSet):
    """Admin uchun Flashcard CRUD; o'quvchi GET orqali kartalarni ko'rishi mumkin."""
    queryset = Flashcard.objects.select_related("subject").all()
    serializer_class = FlashcardSerializer
    http_method_names = ["get", "post", "patch", "delete", "head"]

    def get_permissions(self):
        if self.request.method in ["GET", "HEAD"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
