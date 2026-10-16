"""AI yordamida darslar va hikoyalar kontentini tuzish.

Claude -> xAI -> Groq zaxira zanjiridan foydalanadi (apps.english_library.services._ai_json bilan bir xil
yondashuv). Natija har doim admin panelda qo'lda tahrirlanishi mumkin — AI faqat boshlang'ich kontentni beradi.
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

TOPICS_BY_LEVEL = {
    "A1": [
        "Fe'lning asosiy shakli (to be)", "So'roq so'zlar (what, where, who)", "Olmoshlar (I, you, he, she)",
        "Egalik olmoshlari (my, your, his)", "Ko'plik son (plural nouns)", "Ko'rsatkich so'zlar (this, that, these, those)",
        "Old ko'makchilar (in, on, at)", "There is / There are", "Present Simple", "Sonlar va vaqt",
    ],
    "A2": [
        "Past Simple", "Present Continuous", "Sifat darajalari (comparatives)", "Turli kasblar",
        "Modal fe'llar (can, must, should)", "Future (going to)", "Old ko'makchilar (vaqt va joy)",
        "Miqdor so'zlari (some, any, much, many)", "Present Perfect kirish", "Imperativ gaplar",
    ],
}

STORY_TOPICS_BY_LEVEL = {
    "A1": ["My day", "My family", "My home", "At school", "Food I like", "My best friend"],
    "A2": ["My weekend", "A trip to the city", "My favourite season", "Shopping day", "A letter to a friend"],
}


def _ai_json(prompt, system, max_tokens=3000):
    from apps.ai_teacher.agent import ClaudeUnavailable, simple_completion
    from apps.ai_teacher.services import OFFLINE_FALLBACK_REPLY, _call_groq, _call_xai

    text = None
    try:
        text = simple_completion(prompt, system=system, max_tokens=max_tokens)
    except Exception as e:  # noqa: BLE001 — ClaudeUnavailable yoki kutilmagan xato: zaxiraga o'tamiz
        if not isinstance(e, ClaudeUnavailable):
            logger.warning("Dars/hikoya generatsiyasi: Claude xatosi: %s", e)
        try:
            text = _call_xai(prompt, system=system) or _call_groq(prompt, system=system)
        except Exception:  # noqa: BLE001
            text = None
    if not text or text == OFFLINE_FALLBACK_REPLY:
        return None
    m = re.search(r"[\[{].*[\]}]", text, re.S)
    try:
        return json.loads(m.group(0) if m else text)
    except (ValueError, AttributeError):
        logger.warning("AI javobini o'qib bo'lmadi: %s", (text or "")[:200])
        return None


LESSON_SYSTEM = (
    "Sen ingliz tili o'quv dasturi tuzuvchisisan. Faqat so'ralgan JSON formatda javob ber, boshqa matn yozma."
)


def generate_lesson(subject, cefr_level, topic, order=0):
    """Bitta dars: tushuntirish + so'zlar + mashqlar. Muvaffaqiyatli bo'lsa Lesson obyektini qaytaradi."""
    from .models import Lesson, LessonExercise, LessonWord

    prompt = (
        f"\"{topic}\" mavzusida {cefr_level} darajadagi ingliz tili o'quvchisi uchun bitta dars tuz.\n"
        "Format (faqat shu JSON, boshqa izohsiz):\n"
        "{\n"
        '  "title": "qisqa sarlavha (o\'zbekcha)",\n'
        '  "explanation": "mavzuni 3-5 jumlada oddiy o\'zbek tilida tushuntir, 1-2 ta inglizcha misol bilan",\n'
        '  "words": [{"word": "inglizcha so\'z", "translation": "o\'zbekcha tarjima"}, ... 8 ta],\n'
        '  "exercises": [\n'
        '    {"kind": "en_uz", "prompt": "inglizcha so\'z", "answer": "o\'zbekcha tarjima"}, ... 4 ta,\n'
        '    {"kind": "uz_en", "prompt": "o\'zbekcha so\'z", "answer": "inglizcha tarjima"}, ... 4 ta,\n'
        '    {"kind": "fill_blank", "prompt": "gap, bo\'shliq ___ bilan", "answer": "to\'g\'ri so\'z",'
        ' "bank": ["to\'g\'ri so\'z", "3 ta noto\'g\'ri variant"]}, ... 3 ta,\n'
        '    {"kind": "build_sentence", "prompt": "aralashtirilgan so\'zlar (bank)", "answer": "to\'g\'ri gap",'
        ' "bank": ["so\'z1", "so\'z2", "..."]}, ... 2 ta\n'
        "  ]\n"
        "}"
    )
    data = _ai_json(prompt, LESSON_SYSTEM)
    if not isinstance(data, dict) or not data.get("title"):
        return None
    lesson = Lesson.objects.create(
        subject=subject, cefr_level=cefr_level, order=order,
        title=str(data["title"])[:150], explanation=str(data.get("explanation", ""))[:2000],
        is_published=True,
    )
    words = [w for w in data.get("words", []) if isinstance(w, dict) and w.get("word") and w.get("translation")]
    LessonWord.objects.bulk_create([
        LessonWord(lesson=lesson, word=str(w["word"])[:80], translation=str(w["translation"])[:150], order=i)
        for i, w in enumerate(words[:12])
    ])
    exercises = [e for e in data.get("exercises", []) if isinstance(e, dict) and e.get("prompt") and e.get("answer")]
    LessonExercise.objects.bulk_create([
        LessonExercise(
            lesson=lesson, kind=e.get("kind") if e.get("kind") in LessonExercise.Kind.values else "en_uz",
            prompt=str(e["prompt"])[:300], answer=str(e["answer"])[:300],
            bank=[str(x)[:60] for x in e.get("bank", [])][:8], order=i,
        )
        for i, e in enumerate(exercises[:16])
    ])
    return lesson


def generate_lessons_for_level(subject, cefr_level, topics=None):
    """Berilgan daraja uchun bir nechta dars yaratadi. Qaytaradi: yaratilgan darslar soni."""
    from .models import Lesson

    topics = topics or TOPICS_BY_LEVEL.get(cefr_level.code, [])
    start = Lesson.objects.filter(subject=subject, cefr_level=cefr_level).count()
    created = 0
    for i, topic in enumerate(topics):
        try:
            if generate_lesson(subject, cefr_level, topic, order=start + i):
                created += 1
        except Exception:  # noqa: BLE001 — bitta dars ishlamasa ham qolganlari davom etsin
            logger.exception("Dars yaratilmadi: %s / %s", cefr_level.code, topic)
    return created


def generate_story(subject, cefr_level, topic, order=0):
    """Bitta "tinglang va o'qing" hikoyasi: matn + tushunish savollari."""
    from .models import Story, StoryQuestion

    prompt = (
        f"\"{topic}\" mavzusida {cefr_level} darajadagi ingliz tili o'quvchisi uchun qisqa (80-130 so'z) "
        "hikoya yoz. Oddiy gaplar, shu daraja grammatikasi bilan.\n"
        "Format (faqat shu JSON):\n"
        "{\n"
        '  "title": "qisqa sarlavha (inglizcha)",\n'
        '  "emoji": "mavzuga mos BITTA emoji",\n'
        '  "text": "hikoya matni (inglizcha, 80-130 so\'z)",\n'
        '  "questions": [\n'
        '    {"question": "inglizcha tushunish savoli", "options": ["4 ta variant"], "correct": "to\'g\'ri variant matni"},'
        " ... 5 ta\n"
        "  ]\n"
        "}"
    )
    data = _ai_json(prompt, LESSON_SYSTEM)
    if not isinstance(data, dict) or not data.get("text") or not data.get("title"):
        return None
    colors = ["violet", "amber", "teal", "rose", "sky", "lime"]
    story = Story.objects.create(
        subject=subject, cefr_level=cefr_level, order=order,
        title=str(data["title"])[:150], text=str(data["text"])[:3000],
        cover_emoji=str(data.get("emoji", "📖"))[:8], cover_color=colors[order % len(colors)],
        is_published=True,
    )
    questions = [q for q in data.get("questions", [])
                 if isinstance(q, dict) and q.get("question") and q.get("correct") and q.get("options")]
    StoryQuestion.objects.bulk_create([
        StoryQuestion(
            story=story, question=str(q["question"])[:300], correct=str(q["correct"])[:200],
            options=[str(o)[:150] for o in q["options"]][:5], order=i,
        )
        for i, q in enumerate(questions[:6])
    ])
    return story


def generate_stories_for_level(subject, cefr_level, topics=None):
    from .models import Story

    topics = topics or STORY_TOPICS_BY_LEVEL.get(cefr_level.code, [])
    start = Story.objects.filter(subject=subject, cefr_level=cefr_level).count()
    created = 0
    for i, topic in enumerate(topics):
        try:
            if generate_story(subject, cefr_level, topic, order=start + i):
                created += 1
        except Exception:  # noqa: BLE001
            logger.exception("Hikoya yaratilmadi: %s / %s", cefr_level.code, topic)
    return created
