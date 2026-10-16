"""Vocabulary: darajalar progressi, o'rganish sessiyasi, AI orqali tarjima."""
import json
import logging
import re

from django.db.models import Count, Q
from django.utils import timezone

from .models import Vocabulary, VocabularyProgress

logger = logging.getLogger(__name__)

LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
LEVEL_INFO = {
    "A1": "Boshlang'ich", "A2": "Elementar", "B1": "O'rta",
    "B2": "O'rtadan yuqori", "C1": "Yuqori", "C2": "Mukammal",
}
MASTERED = 100
CORRECT_STEP = 25   # 4 ta to'g'ri javob = o'zlashtirildi
WRONG_STEP = 15


def recommended_level(user):
    from apps.subjects.models import UserSubjectLevel

    row = UserSubjectLevel.objects.filter(user=user, subject__code="english").select_related("current_level").first()
    if row and row.current_level and row.current_level.code in LEVEL_ORDER:
        return row.current_level.code
    # Daraja aniqlanmagan: 80% o'zlashtirilmagan birinchi daraja
    for lvl in get_levels(user, with_recommended=False):
        if lvl["total"] and lvl["percent"] < 80:
            return lvl["level"]
    return "A1"


def get_levels(user, with_recommended=True):
    totals = dict(Vocabulary.objects.values_list("cefr").annotate(n=Count("id")))
    progress = (
        VocabularyProgress.objects.filter(user=user)
        .values("vocabulary__cefr")
        .annotate(mastered=Count("id", filter=Q(mastery__gte=MASTERED)),
                  learning=Count("id", filter=Q(mastery__gt=0, mastery__lt=MASTERED)))
    )
    by_level = {r["vocabulary__cefr"]: r for r in progress}
    rec = recommended_level(user) if with_recommended else None
    result = []
    for lvl in LEVEL_ORDER:
        total = totals.get(lvl, 0)
        mastered = by_level.get(lvl, {}).get("mastered", 0)
        result.append({
            "level": lvl,
            "description": LEVEL_INFO[lvl],
            "total": total,
            "mastered": mastered,
            "learning": by_level.get(lvl, {}).get("learning", 0),
            "percent": round(mastered / total * 100) if total else 0,
            "progress": round(mastered / total * 100) if total else 0,  # eski frontend uchun
            "status": "current" if lvl == rec else ("unavailable" if not total else "open"),
            "locked": not total,
            "recommended": lvl == rec,
        })
    return result


def word_payload(word, progress=None):
    return {
        "id": word.id,
        "headword": word.headword,
        "pos": word.pos,
        "cefr": word.cefr,
        "uz": word.uz,
        "example": word.example,
        "example_uz": word.example_uz,
        "mastery": progress.mastery if progress else 0,
        "correct_answers": progress.correct_answers if progress else 0,
        "wrong_answers": progress.wrong_answers if progress else 0,
        "status": _status(progress),
    }


def _status(progress):
    if not progress or progress.mastery <= 0:
        return "new"
    return "mastered" if progress.mastery >= MASTERED else "learning"


def build_session(user, level, size=10):
    """Takrorlash kerak bo'lgan (o'rganilayotgan) so'zlar + yangi so'zlar."""
    size = max(4, min(20, size))
    progress = VocabularyProgress.objects.filter(user=user, vocabulary__cefr=level)
    review_n = size // 2
    learning = list(
        progress.filter(mastery__gt=0, mastery__lt=MASTERED)
        .filter(Q(last_reviewed__isnull=True) | Q(last_reviewed__lte=timezone.now() - timezone.timedelta(hours=8)))
        .select_related("vocabulary").order_by("last_reviewed")[:review_n]
    )
    seen_ids = progress.values_list("vocabulary_id", flat=True)
    # Yangi so'zlar: tasodifiy, lekin bir xil headword takrorlanmasin va "a.m./A.M." kabi yozuvlar chetda qolsin
    pool = list(
        Vocabulary.objects.filter(cefr=level).exclude(id__in=seen_ids).exclude(headword__contains="/")
        .order_by("?")[: (size - len(learning)) * 3]
    )
    new_words, heads = [], {p.vocabulary.headword.lower() for p in learning}
    for w in pool:
        if w.headword.lower() not in heads:
            heads.add(w.headword.lower())
            new_words.append(w)
        if len(new_words) >= size - len(learning):
            break
    words = [p.vocabulary for p in learning] + new_words
    ensure_translations(words)
    pmap = {p.vocabulary_id: p for p in learning}
    return [word_payload(w, pmap.get(w.id)) for w in words]


def answer(user, word, correct):
    from apps.gamification.services import record_activity

    progress, _ = VocabularyProgress.objects.get_or_create(user=user, vocabulary=word)
    was_mastered = progress.mastery >= MASTERED
    if correct:
        progress.correct_answers += 1
        progress.mastery = min(MASTERED, progress.mastery + CORRECT_STEP)
    else:
        progress.wrong_answers += 1
        progress.mastery = max(5, progress.mastery - WRONG_STEP)  # 5 = ko'rilgan, o'rganilmoqda
    progress.last_reviewed = timezone.now()
    progress.save()
    points = 0
    if correct:
        points = 2 + (5 if progress.mastery >= MASTERED and not was_mastered else 0)
    record_activity(user, _english(), points=points, source="vocabulary")
    return progress, points


def mark_known(user, word):
    progress, _ = VocabularyProgress.objects.get_or_create(user=user, vocabulary=word)
    progress.mastery = MASTERED
    progress.last_reviewed = timezone.now()
    progress.save()
    return progress


def _english():
    from apps.subjects.models import Subject
    return Subject.objects.filter(code="english").first()


# --------------------------------------------------------------------------
# AI orqali tarjima (bir marta, keyin bazada saqlanadi)
# --------------------------------------------------------------------------

TRANSLATE_SYSTEM = (
    "Sen ingliz-o'zbek lug'atchisisan. Faqat JSON qaytar, boshqa hech narsa yozma."
)


def ensure_translations(words, limit=12):
    missing = [w for w in words if not w.uz][:limit]
    if not missing:
        return
    listing = "\n".join(f"- {w.headword} ({w.pos}, {w.cefr})" for w in missing)
    prompt = (
        "Quyidagi inglizcha so'zlarni o'zbek tiliga (lotin yozuvida) tarjima qil. Har biri uchun shu darajaga mos "
        "qisqa inglizcha misol gap va uning o'zbekcha tarjimasini ber.\n"
        'Format: [{"word": "...", "uz": "...", "example": "...", "example_uz": "..."}]\n\n' + listing
    )
    raw = _ai_json(prompt)
    if not raw:
        return
    by_word = {}
    for row in raw if isinstance(raw, list) else []:
        if isinstance(row, dict) and row.get("word") and row.get("uz"):
            by_word[str(row["word"]).strip().lower()] = row
    for w in missing:
        row = by_word.get(w.headword.strip().lower())
        if not row:
            continue
        w.uz = str(row.get("uz", ""))[:255]
        w.example = str(row.get("example", ""))[:300]
        w.example_uz = str(row.get("example_uz", ""))[:300]
        w.save(update_fields=["uz", "example", "example_uz"])


def _ai_json(prompt):
    """Claude -> xAI -> Groq. Ishlamasa None (so'zlar tarjimasiz ko'rsatiladi)."""
    from apps.ai_teacher.agent import ClaudeUnavailable, simple_completion
    from apps.ai_teacher.services import _call_groq, _call_xai, OFFLINE_FALLBACK_REPLY

    text = None
    try:
        text = simple_completion(prompt, system=TRANSLATE_SYSTEM, max_tokens=2000)
    except ClaudeUnavailable:
        try:
            text = _call_xai(prompt, system=TRANSLATE_SYSTEM) or _call_groq(prompt, system=TRANSLATE_SYSTEM)
        except Exception:  # noqa: BLE001
            text = None
    if not text or text == OFFLINE_FALLBACK_REPLY:
        return None
    m = re.search(r"\[.*\]", text, re.S)
    try:
        return json.loads(m.group(0) if m else text)
    except (ValueError, AttributeError):
        logger.warning("Tarjima javobini o'qib bo'lmadi: %s", text[:200])
        return None
