import random

from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Vocabulary, VocabularyProgress
from .services import (
    LEVEL_ORDER, MASTERED, answer, build_session, ensure_translations, get_levels, mark_known,
    recommended_level, word_payload,
)


def _level_param(request):
    level = str(request.query_params.get("cefr") or request.query_params.get("level") or "").strip().upper()
    return level if level in LEVEL_ORDER else None


class VocabularyLevelsView(APIView):
    """GET /english-library/vocabulary/levels/ — darajalar, progress va tavsiya etilgan daraja."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        levels = get_levels(request.user)
        rec = next((l["level"] for l in levels if l["recommended"]), "A1")
        return Response({"levels": levels, "recommended": rec})


class VocabularySessionView(APIView):
    """GET /english-library/vocabulary/session/?cefr=A2&size=10 — o'rganish uchun so'zlar to'plami
    (takrorlash kerak bo'lganlar + yangilar), tarjima va misollar bilan."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        level = _level_param(request) or recommended_level(request.user)
        try:
            size = int(request.query_params.get("size", 10))
        except (TypeError, ValueError):
            size = 10
        words = build_session(request.user, level, size)
        return Response({"level": level, "words": words})


class VocabularyWordsView(APIView):
    """GET /english-library/vocabulary/?cefr=B1&page=1&page_size=30&search=&status=new|learning|mastered"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        level = _level_param(request)
        if not level:
            return Response({"detail": "cefr parametri noto'g'ri", "allowed": LEVEL_ORDER},
                            status=status.HTTP_400_BAD_REQUEST)
        words = Vocabulary.objects.filter(cefr=level)
        search = (request.query_params.get("search") or "").strip()
        if search:
            words = words.filter(Q(headword__icontains=search) | Q(uz__icontains=search))
        st = request.query_params.get("status")
        mine = VocabularyProgress.objects.filter(user=request.user)
        if st == "mastered":
            words = words.filter(id__in=mine.filter(mastery__gte=MASTERED).values("vocabulary_id"))
        elif st == "learning":
            words = words.filter(id__in=mine.filter(mastery__gt=0, mastery__lt=MASTERED).values("vocabulary_id"))
        elif st == "new":
            words = words.exclude(id__in=mine.filter(mastery__gt=0).values("vocabulary_id"))
        words = words.order_by("headword")

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(50, max(1, int(request.query_params.get("page_size", 30))))
        except (TypeError, ValueError):
            page, page_size = 1, 30
        total = words.count()
        page_words = list(words[(page - 1) * page_size: page * page_size])
        if request.query_params.get("translate") == "1":
            ensure_translations(page_words, limit=30)
        pmap = {p.vocabulary_id: p for p in mine.filter(vocabulary_id__in=[w.id for w in page_words])}
        return Response({
            "level": level, "total": total, "page": page, "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
            "results": [word_payload(w, pmap.get(w.id)) for w in page_words],
        })


class VocabularyTestView(APIView):
    """Eski frontend uchun: so'zning tarjimasini 4 variantdan topish."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, vocabulary_id):
        word = Vocabulary.objects.filter(id=vocabulary_id).first()
        if not word:
            return Response({"detail": "So'z topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        ensure_translations([word])
        others = list(Vocabulary.objects.filter(cefr=word.cefr).exclude(id=word.id).exclude(uz="").order_by("?")[:3])
        options = [{"id": word.id, "headword": word.uz or word.headword}] + [{"id": o.id, "headword": o.uz} for o in others]
        random.shuffle(options)
        return Response({"vocabulary_id": word.id, "question": f"\"{word.headword}\" so'zining tarjimasini toping",
                         "options": options})


class VocabularyAnswerView(APIView):
    """POST /english-library/vocabulary/{id}/answer/  {correct: bool}  yoki eski {selected_id}"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, vocabulary_id):
        word = Vocabulary.objects.filter(id=vocabulary_id).first()
        if not word:
            return Response({"detail": "So'z topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        if "correct" in request.data:
            correct = bool(request.data.get("correct"))
        else:
            try:
                correct = int(request.data.get("selected_id")) == word.id
            except (TypeError, ValueError):
                return Response({"detail": "selected_id noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST)
        progress, points = answer(request.user, word, correct)
        return Response({
            "correct": correct,
            "correct_answer": {"id": word.id, "headword": word.headword, "uz": word.uz},
            "mastery": progress.mastery,
            "correct_answers": progress.correct_answers,
            "wrong_answers": progress.wrong_answers,
            "mastered": progress.mastery >= MASTERED,
            "earned_points": points,
        })


class VocabularyKnownView(APIView):
    """POST /english-library/vocabulary/{id}/known/ — "Bu so'zni bilaman" (o'zlashtirilgan deb belgilash)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, vocabulary_id):
        word = Vocabulary.objects.filter(id=vocabulary_id).first()
        if not word:
            return Response({"detail": "So'z topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        progress = mark_known(request.user, word)
        return Response(word_payload(word, progress))


class DictionaryView(APIView):
    """GET /english-library/dictionary/?q=apple — inglizcha yoki o'zbekcha so'z bo'yicha qidiruv.
    q bo'sh bo'lsa — kun so'zi (o'quvchi darajasidan)."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        import datetime

        q = (request.query_params.get("q") or "").strip()[:60]
        mine = VocabularyProgress.objects.filter(user=request.user)
        if not q:
            level = recommended_level(request.user)
            pool = Vocabulary.objects.filter(cefr=level).exclude(headword__contains="/").order_by("id")
            n = pool.count()
            word = pool[datetime.date.today().toordinal() % n] if n else None
            if word:
                ensure_translations([word])
            p = mine.filter(vocabulary=word).first() if word else None
            return Response({"query": "", "results": [], "word_of_day": word_payload(word, p) if word else None})

        low = q.lower()
        exact = list(Vocabulary.objects.filter(headword__iexact=q)[:5])
        starts = list(Vocabulary.objects.filter(headword__istartswith=low).exclude(id__in=[w.id for w in exact])
                      .order_by("headword")[:15])
        by_uz = list(Vocabulary.objects.filter(uz__icontains=low).exclude(id__in=[w.id for w in exact + starts])[:10])
        results = (exact + starts + by_uz)[:20]
        ensure_translations(results[:8], limit=8)
        pmap = {p.vocabulary_id: p for p in mine.filter(vocabulary_id__in=[w.id for w in results])}
        return Response({
            "query": q,
            "results": [word_payload(w, pmap.get(w.id)) for w in results],
            "word_of_day": None,
        })


class AddToLearningView(APIView):
    """POST /english-library/vocabulary/{id}/learn/ — so'zni o'rganish ro'yxatiga qo'shadi
    (keyingi "O'rganish" sessiyalarida takrorlash uchun chiqadi)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, vocabulary_id):
        word = Vocabulary.objects.filter(id=vocabulary_id).first()
        if not word:
            return Response({"detail": "So'z topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        progress, created = VocabularyProgress.objects.get_or_create(user=request.user, vocabulary=word)
        if progress.mastery == 0:
            progress.mastery = 5  # "o'rganilmoqda" — sessiyada takrorlash uchun chiqadi
            progress.save(update_fields=["mastery"])
        return Response(word_payload(word, progress))
