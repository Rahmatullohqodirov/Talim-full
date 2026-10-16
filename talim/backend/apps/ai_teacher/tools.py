"""AI Ustoz tool'lari.

Muhim: hech bir sxemada `user_id` yo'q. Foydalanuvchi har doim backend tomonidan
(request.user) beriladi, shuning uchun model boshqa o'quvchining ma'lumotini so'ray olmaydi.
"""
import logging
from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

CEFR_CODES = ["A1", "A2", "B1", "B2", "C1", "C2"]
SUBJECT_CODES = ["english", "german", "russian", "turkish", "uzbek", "math"]

_subject_prop = {
    "type": "string",
    "enum": SUBJECT_CODES,
    "description": "Fan kodi",
}

TOOLS = [
    {
        "name": "get_user_level",
        "description": "O'quvchining tanlangan fan bo'yicha joriy darajasini (A1-C2) qaytaradi. Daraja aniqlanmagan bo'lsa level=null.",
        "input_schema": {
            "type": "object",
            "properties": {"subject": _subject_prop},
            "required": ["subject"],
        },
    },
    {
        "name": "update_user_level",
        "description": "Daraja testi tugagach, aniqlangan darajani o'quvchi profiliga saqlaydi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": _subject_prop,
                "level": {"type": "string", "enum": CEFR_CODES},
            },
            "required": ["subject", "level"],
        },
    },
    {
        "name": "create_lesson_plan",
        "description": "O'quvchining darajasi va natijalariga qarab shaxsiy o'quv yo'lini (dars rejasini) yaratadi va bosqichlarini qaytaradi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": _subject_prop,
                "goal": {"type": "string", "description": "masalan: IELTS, kundalik muloqot, imtihon"},
                "weeks": {"type": "integer", "minimum": 1, "maximum": 52},
            },
            "required": ["subject"],
        },
    },
    {
        "name": "save_test_result",
        "description": "AI Ustoz o'tkazgan test yoki daraja testi natijasini saqlaydi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": _subject_prop,
                "kind": {"type": "string", "enum": ["placement", "test"],
                         "description": "placement = daraja testi, test = oddiy mashq/test"},
                "score_percent": {"type": "number", "minimum": 0, "maximum": 100},
                "weak_topics": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["subject", "kind", "score_percent"],
        },
    },
    {
        "name": "get_statistics",
        "description": "O'quvchining o'qish vaqti, darslar soni, o'rganilgan so'zlar, test va talaffuz natijalari statistikasi. Fan berilmasa barcha fanlar bo'yicha.",
        "input_schema": {
            "type": "object",
            "properties": {"subject": _subject_prop},
        },
    },
    {
        "name": "get_vocabulary",
        "description": "Daraja bo'yicha platforma lug'at bazasidan yangi so'zlar (o'quvchi hali o'zlashtirmaganlari). Hozircha faqat ingliz tili uchun baza bor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": _subject_prop,
                "level": {"type": "string", "enum": CEFR_CODES},
                "count": {"type": "integer", "minimum": 1, "maximum": 20},
            },
            "required": ["subject", "level"],
        },
    },
    {
        "name": "get_subscription_status",
        "description": "O'quvchining obunasi (tarif, amal qilish muddati) va oxirgi to'lovlari holatini qaytaradi.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "remember_about_student",
        "description": (
            "O'quvchi haqida uzoq muddat eslab qolish kerak bo'lgan, O'QISHGA OID barqaror faktni saqlaydi: "
            "qiziqishlari, maqsadi, o'rganish uslubi (masalan, qisqa tushuntirishni yoqtiradi), "
            "takrorlanadigan xatosi yoki kuchli tomoni. Bir martalik gaplarni saqlama. "
            "Manzil, telefon, sog'liq, oilaviy muammolar, parol va to'lov ma'lumotlarini HECH QACHON saqlama. "
            "Fakt kartada allaqachon bo'lsa, qayta saqlama; o'zgargan bo'lsa avval eskisini forget_about_student bilan o'chir."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["interest", "goal", "style", "mistake", "strength", "other"]},
                "text": {"type": "string", "description": "Qisqa fakt, o'zbek tilida. Masalan: 'Futbolni yaxshi ko'radi', 'Past Simple'da -ed qo'shishni unutadi'"},
                "subject": {**_subject_prop, "description": "Fakt aniq bir fanga tegishli bo'lsa"},
            },
            "required": ["category", "text"],
        },
    },
    {
        "name": "forget_about_student",
        "description": "O'quvchi kartasidagi faktni o'chiradi (o'quvchi so'rasa yoki fakt eskirgan/noto'g'ri bo'lsa). memory_id — kartadagi [#...] belgisi.",
        "input_schema": {
            "type": "object",
            "properties": {"memory_id": {"type": "string"}},
            "required": ["memory_id"],
        },
    },
    {
        "name": "start_lesson",
        "description": (
            "Shu suhbatda qadamma-qadam o'tiladigan yangi dars ochadi. 4-6 ta qadam rejala: odatda tushuntirish, "
            "misollar, 2-3 ta mashq, mini-test va xulosa. Mavzu va misollarni o'quvchi darajasi va qiziqishlariga moslashtir. "
            "Suhbatda tugallanmagan dars bo'lsa, u yopiladi."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": _subject_prop,
                "title": {"type": "string", "description": "Dars mavzusi, masalan: 'Past Simple: o'tgan hafta sonlari'"},
                "objective": {"type": "string", "description": "Dars oxirida o'quvchi nimani qila olishi kerak"},
                "steps": {
                    "type": "array",
                    "minItems": 3,
                    "maxItems": 8,
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "type": {"type": "string", "enum": ["explain", "example", "exercise", "quiz", "speaking", "review"]},
                        },
                        "required": ["title", "type"],
                    },
                },
            },
            "required": ["subject", "title", "objective", "steps"],
        },
    },
    {
        "name": "update_lesson_progress",
        "description": "Joriy darsning bir qadami bajarilganini belgilaydi (o'quvchi mashqqa javob bergach yoki tushuntirish tugagach).",
        "input_schema": {
            "type": "object",
            "properties": {
                "step_number": {"type": "integer", "minimum": 1, "description": "1 dan boshlanadi"},
                "result": {"type": "string", "enum": ["correct", "partly", "wrong", "done"]},
                "note": {"type": "string", "description": "Qisqa izoh, masalan qanday xato qildi"},
            },
            "required": ["step_number", "result"],
        },
    },
    {
        "name": "finish_lesson",
        "description": "Joriy darsni yakunlaydi, natijani statistikaga saqlaydi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Dars xulosasi: nima o'rganildi"},
                "score_percent": {"type": "number", "minimum": 0, "maximum": 100},
                "weak_topics": {"type": "array", "items": {"type": "string"}},
                "next_step": {"type": "string", "description": "Keyingi darsda nima qilish kerak"},
            },
            "required": ["summary", "score_percent", "next_step"],
        },
    },
    {
        "name": "create_study_plan",
        "description": (
            "Kunlik, haftalik yoki oylik o'quv rejasini tuzadi va saqlaydi (o'quvchi uni Dashboard'da ko'radi va belgilaydi). "
            "Bandlar o'quvchining darajasi, maqsadi, zaif mavzulari va kuniga ajrata oladigan vaqtiga mos bo'lsin. "
            "daily: 3-5 band (hammasi day=1). weekly: har kunga 2-3 band, day=1..7. "
            "monthly: har haftaga 3-5 band, week=1..4, mavzular haftadan-haftaga murakkablashsin. "
            "Shu davr va fan bo'yicha eski faol reja o'rniga yangisi qo'yiladi. Sanalarni server o'zi hisoblaydi."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": _subject_prop,
                "period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                "title": {"type": "string", "description": "masalan: 'IELTS uchun 1-oy: asoslar'"},
                "goal": {"type": "string"},
                "minutes_per_day": {"type": "integer", "minimum": 5, "maximum": 240},
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 40,
                    "items": {
                        "type": "object",
                        "properties": {
                            "day": {"type": "integer", "minimum": 1, "maximum": 7, "description": "daily/weekly uchun"},
                            "week": {"type": "integer", "minimum": 1, "maximum": 4, "description": "monthly uchun"},
                            "title": {"type": "string", "description": "Aniq vazifa: 'Past Simple: 10 ta gap yozish'"},
                            "type": {"type": "string", "enum": ["lesson", "vocabulary", "quiz", "flashcard", "speaking",
                                                                "video", "grammar", "reading", "writing", "math"]},
                            "minutes": {"type": "integer", "minimum": 5, "maximum": 120},
                            "note": {"type": "string"},
                        },
                        "required": ["title", "type", "minutes"],
                    },
                },
            },
            "required": ["subject", "period", "title", "minutes_per_day", "items"],
        },
    },
    {
        "name": "mark_plan_item",
        "description": "O'quv rejasidagi bandni bajarilgan (yoki bajarilmagan) deb belgilaydi. plan_id va item_id kartadan olinadi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "item_id": {"type": "string"},
                "done": {"type": "boolean"},
            },
            "required": ["plan_id", "item_id"],
        },
    },
    {
        "name": "escalate_to_admin",
        "description": "To'lov muammosi, texnik nosozlik yoki shikoyatni adminga murojaat sifatida yuboradi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["payment", "technical", "complaint", "other"]},
                "reason": {"type": "string", "description": "Muammoning qisqa, aniq tavsifi"},
            },
            "required": ["category", "reason"],
        },
    },
]


import re

MEMORY_LIMIT = 50
# Xotiraga tushmasligi kerak: telefon/karta raqamlari, email, havolalar
_PRIVATE_RE = re.compile(r"(\d[\d\s\-()]{6,}\d)|([\w.+-]+@[\w-]+\.\w+)|(https?://|www\.)", re.I)  # bitta o'quvchi uchun eng ko'p fakt soni


class ToolError(Exception):
    """Model ko'rishi kerak bo'lgan, tushunarli xato."""


def _subject(code):
    from apps.subjects.models import Subject

    subject = Subject.objects.filter(code=code).first()
    if not subject:
        available = list(Subject.objects.values_list("code", flat=True))
        raise ToolError(f"'{code}' fani platformada hali yo'q. Mavjud fanlar: {', '.join(available)}")
    return subject


def _cefr_level(subject, code):
    from apps.subjects.models import CEFRLevel

    if code not in CEFR_CODES:
        raise ToolError(f"Noto'g'ri daraja: {code}")
    level, _ = CEFRLevel.objects.get_or_create(
        subject=subject, code=code, defaults={"order": CEFR_CODES.index(code) + 1}
    )
    return level


class TutorToolbox:
    """Bitta so'rov uchun tool'lar. user va thread backend tomonidan beriladi."""

    def __init__(self, user, thread=None):
        self.user = user
        self.thread = thread

    def run(self, name, args):
        fn = getattr(self, name, None)
        if name.startswith("_") or not callable(fn) or name not in {t["name"] for t in TOOLS}:
            raise ToolError(f"Noma'lum tool: {name}")
        return fn(**args)

    # --- Daraja ---------------------------------------------------------------
    def get_user_level(self, subject):
        from apps.subjects.models import UserSubjectLevel

        subj = _subject(subject)
        row = UserSubjectLevel.objects.filter(user=self.user, subject=subj).select_related("current_level").first()
        level = row.current_level.code if row and row.current_level else None
        return {"subject": subj.code, "level": level, "determined": level is not None}

    def update_user_level(self, subject, level):
        from apps.subjects.models import UserSubjectLevel

        subj = _subject(subject)
        lvl = _cefr_level(subj, level)
        UserSubjectLevel.objects.update_or_create(
            user=self.user, subject=subj, defaults={"current_level": lvl}
        )
        return {"saved": True, "subject": subj.code, "level": lvl.code}

    # --- Dars rejasi ----------------------------------------------------------
    def create_lesson_plan(self, subject, goal="umumiy", weeks=4):
        from apps.learning_path.services import generate_personalized_path

        subj = _subject(subject)
        path = generate_personalized_path(self.user, subj)
        items = []
        for item in path.items.select_related("cefr_level", "math_topic").order_by("order"):
            title = item.cefr_level.code if item.cefr_level else (str(item.math_topic) if item.math_topic else "")
            items.append({"order": item.order, "step": title, "status": item.status})
        return {
            "plan_id": str(path.id),
            "subject": subj.code,
            "goal": goal,
            "weeks": weeks,
            "steps": items,
            "note": "Bosqichlar platformadagi 'Learning path' bo'limida ham ko'rinadi. "
                    "Har hafta uchun aniq mavzularni o'quvchi darajasiga qarab o'zing taqsimla.",
        }

    # --- Natijalar ------------------------------------------------------------
    def save_test_result(self, subject, kind, score_percent, weak_topics=None):
        from .models import AssessmentResult

        subj = _subject(subject)
        score = max(0.0, min(100.0, float(score_percent)))
        result = AssessmentResult.objects.create(
            user=self.user, subject=subj, kind=kind,
            score_percent=score, weak_topics=list(weak_topics or [])[:20],
        )
        return {"saved": True, "result_id": str(result.id), "score_percent": score}

    def get_statistics(self, subject=None):
        from apps.english_library.models import VocabularyProgress
        from apps.statistics.models import DailyActivity, SubjectStats
        from .models import AssessmentResult

        stats_qs = SubjectStats.objects.filter(user=self.user).select_related("subject")
        assess_qs = AssessmentResult.objects.filter(user=self.user)
        activity_qs = DailyActivity.objects.filter(user=self.user, date__gte=timezone.localdate() - timedelta(days=6))
        if subject:
            subj = _subject(subject)
            stats_qs = stats_qs.filter(subject=subj)
            assess_qs = assess_qs.filter(subject=subj)
            activity_qs = activity_qs.filter(subject=subj)

        per_subject = [
            {
                "subject": s.subject.code,
                "total_minutes": s.total_minutes,
                "sessions_completed": s.sessions_completed,
                "current_streak_days": s.current_streak_days,
                "total_points": s.total_points,
                "avg_grammar_score": s.avg_grammar_score,
            }
            for s in stats_qs
        ]
        by_kind = {
            row["kind"]: {"count": row["n"], "avg_percent": round(row["avg"] or 0, 1)}
            for row in assess_qs.values("kind").annotate(n=Count("id"), avg=Avg("score_percent"))
        }
        last = assess_qs.order_by("-created_at").first()
        return {
            "subjects": per_subject,
            "minutes_last_7_days": activity_qs.aggregate(m=Sum("minutes_spent"))["m"] or 0,
            "words_learned": VocabularyProgress.objects.filter(user=self.user, mastery__gte=100).count(),
            "words_in_progress": VocabularyProgress.objects.filter(user=self.user, mastery__gt=0, mastery__lt=100).count(),
            "tests": by_kind.get("test"),
            "placement_tests": by_kind.get("placement"),
            "speaking": by_kind.get("speaking"),
            "last_weak_topics": last.weak_topics if last else [],
            "note": "speaking.avg_percent — taxminiy ko'rsatkich, o'quvchiga aniq ball sifatida aytma.",
        }

    # --- Lug'at ---------------------------------------------------------------
    def get_vocabulary(self, subject, level, count=10):
        from apps.english_library.models import Vocabulary, VocabularyProgress

        if subject != "english":
            return {
                "available": False,
                "message": "Bu fan uchun platformada lug'at bazasi hali yo'q. "
                           "Darajaga mos so'zlarni o'zing tanlashing mumkin, lekin ularni bazadan olingan deb aytma.",
            }
        known = VocabularyProgress.objects.filter(user=self.user, mastery__gte=100).values("vocabulary_id")
        words = (
            Vocabulary.objects.filter(cefr__iexact=level)
            .exclude(id__in=known)
            .order_by("?")[: max(1, min(int(count), 20))]
        )
        return {
            "available": True,
            "level": level,
            "words": [{"word": w.headword, "part_of_speech": w.pos} for w in words],
            "note": "Bazada tarjima yo'q: tarjima va misolni o'zing ber.",
        }

    # --- O'quvchi xotirasi ----------------------------------------------------
    def remember_about_student(self, category, text, subject=None):
        from .models import LearnerMemory

        text = " ".join(str(text).split())[:300]
        if len(text) < 3:
            raise ToolError("Fakt juda qisqa")
        if _PRIVATE_RE.search(text):
            raise ToolError("Bu shaxsiy ma'lumotga o'xshaydi (telefon, email, havola yoki karta raqami). Saqlanmadi.")
        subj = _subject(subject) if subject else None
        existing = LearnerMemory.objects.filter(user=self.user, text__iexact=text).first()
        if existing:
            existing.category = category
            existing.save(update_fields=["category", "updated_at"])
            return {"saved": True, "memory_id": str(existing.id)[:8], "note": "allaqachon bor edi, yangilandi"}
        mem = LearnerMemory.objects.create(user=self.user, subject=subj, category=category, text=text)
        # Chegara: eng eski faktlarni o'chiramiz
        old_ids = list(
            LearnerMemory.objects.filter(user=self.user).order_by("-updated_at").values_list("id", flat=True)[MEMORY_LIMIT:]
        )
        if old_ids:
            LearnerMemory.objects.filter(id__in=old_ids).delete()
        return {"saved": True, "memory_id": str(mem.id)[:8]}

    def forget_about_student(self, memory_id):
        from .models import LearnerMemory

        key = str(memory_id).strip().lstrip("#").lower()
        if len(key) < 4:
            raise ToolError("memory_id noto'g'ri")
        for mem in LearnerMemory.objects.filter(user=self.user):
            if str(mem.id).startswith(key):
                text = mem.text
                mem.delete()
                return {"forgotten": True, "text": text}
        raise ToolError("Bunday fakt topilmadi")

    # --- Darslar --------------------------------------------------------------
    def _active_lesson(self):
        from .models import GeneratedLesson

        if not self.thread:
            raise ToolError("Dars faqat suhbat ichida o'tiladi")
        lesson = GeneratedLesson.objects.filter(thread=self.thread, is_completed=False, completed_at__isnull=True).first()
        if not lesson:
            raise ToolError("Bu suhbatda faol dars yo'q. Avval start_lesson ni chaqir.")
        return lesson

    def start_lesson(self, subject, title, objective, steps):
        from apps.subjects.models import UserSubjectLevel
        from .models import GeneratedLesson

        if not self.thread:
            raise ToolError("Dars faqat suhbat ichida o'tiladi")
        subj = _subject(subject)
        clean_steps = [
            {"title": str(st.get("title", ""))[:120], "type": st.get("type", "explain"),
             "done": False, "result": None, "note": ""}
            for st in (steps or [])[:8] if st.get("title")
        ]
        if len(clean_steps) < 3:
            raise ToolError("Darsda kamida 3 ta qadam bo'lishi kerak")
        # Tugallanmagan eski darsni yopamiz
        GeneratedLesson.objects.filter(thread=self.thread, completed_at__isnull=True, is_completed=False) \
            .update(completed_at=timezone.now(), summary="Yakunlanmay qoldi")
        row = UserSubjectLevel.objects.filter(user=self.user, subject=subj).select_related("current_level").first()
        lesson = GeneratedLesson.objects.create(
            user=self.user, subject=subj, cefr_level=row.current_level if row else None,
            title=str(title)[:200], objective=str(objective)[:1000], content_blocks=clean_steps,
            thread=self.thread, current_step=0,
        )
        if self.thread.subject_id is None:
            self.thread.subject = subj
            self.thread.save(update_fields=["subject", "updated_at"])
        return {"lesson_id": str(lesson.id)[:8], "title": lesson.title,
                "steps": [f"{i + 1}. {st['title']}" for i, st in enumerate(clean_steps)],
                "note": "Endi 1-qadamdan boshla. Har safar faqat bitta qadam."}

    def update_lesson_progress(self, step_number, result, note=""):
        lesson = self._active_lesson()
        steps = list(lesson.content_blocks or [])
        idx = int(step_number) - 1
        if not 0 <= idx < len(steps):
            raise ToolError(f"Qadam raqami 1 dan {len(steps)} gacha bo'lishi kerak")
        steps[idx] = {**steps[idx], "done": True, "result": result, "note": str(note)[:300]}
        lesson.content_blocks = steps
        nxt = next((i for i, st in enumerate(steps) if not st.get("done")), len(steps))
        lesson.current_step = nxt
        lesson.save(update_fields=["content_blocks", "current_step", "updated_at"])
        return {
            "saved": True,
            "done_steps": sum(1 for st in steps if st.get("done")),
            "total_steps": len(steps),
            "next_step": f"{nxt + 1}. {steps[nxt]['title']}" if nxt < len(steps) else "Barcha qadamlar bajarildi — finish_lesson chaqir",
        }

    def finish_lesson(self, summary, score_percent, next_step, weak_topics=None):
        from .models import AssessmentResult

        lesson = self._active_lesson()
        score = max(0.0, min(100.0, float(score_percent)))
        lesson.is_completed = True
        lesson.completed_at = timezone.now()
        lesson.summary = str(summary)[:2000]
        lesson.next_step = str(next_step)[:1000]
        lesson.score_percent = score
        lesson.current_step = len(lesson.content_blocks or [])
        lesson.save()
        AssessmentResult.objects.create(
            user=self.user, subject=lesson.subject, kind=AssessmentResult.Kind.LESSON,
            score_percent=score, weak_topics=list(weak_topics or [])[:20],
            details={"lesson_id": str(lesson.id), "title": lesson.title},
        )
        from apps.gamification.services import record_activity
        points = 10 + round(score / 10)
        record_activity(self.user, lesson.subject, points=points, sessions=1, source="ai_lesson")
        return {"finished": True, "title": lesson.title, "score_percent": score, "points": points}

    # --- O'quv rejalari -------------------------------------------------------
    def create_study_plan(self, subject, period, title, minutes_per_day, items, goal=""):
        from .models import StudyPlan
        from .plans import normalize_items, period_range, serialize_plan

        if period not in ("daily", "weekly", "monthly"):
            raise ToolError("period: daily, weekly yoki monthly")
        subj = _subject(subject)
        start = timezone.localdate()
        start, end = period_range(period, start)
        clean = normalize_items(period, start, items)
        if not clean:
            raise ToolError("Rejada kamida bitta band bo'lishi kerak")
        StudyPlan.objects.filter(user=self.user, subject=subj, period=period, is_active=True).update(is_active=False)
        plan = StudyPlan.objects.create(
            user=self.user, subject=subj, period=period, title=str(title)[:200], goal=str(goal)[:1000],
            minutes_per_day=max(5, min(240, int(minutes_per_day or 20))),
            start_date=start, end_date=end, items=clean,
        )
        data = serialize_plan(plan)
        return {"plan_id": data["id"][:8], "period": period, "start": data["start_date"], "end": data["end_date"],
                "items": len(clean), "note": "Reja Dashboard'dagi 'O'quv rejam' bo'limida ko'rinadi."}

    def mark_plan_item(self, plan_id, item_id, done=True):
        from .models import StudyPlan
        from .plans import plan_progress, set_item_done

        key = str(plan_id).strip().lstrip("#").lower()
        plan = next((p for p in StudyPlan.objects.filter(user=self.user, is_active=True) if str(p.id).startswith(key)), None)
        if plan is None or len(key) < 4:
            raise ToolError("Reja topilmadi")
        if set_item_done(plan, item_id, done) is None:
            raise ToolError("Band topilmadi")
        return {"saved": True, "progress": plan_progress(plan)}

    # --- Obuna va to'lov ------------------------------------------------------
    def get_subscription_status(self):
        from apps.payments.models import PaymentTransaction

        sub = getattr(self.user, "subscription", None)
        try:
            plan = sub.plan.name if sub else None
            active = sub.is_active if sub else False
            expires = sub.expires_at.isoformat() if sub and sub.expires_at else None
        except Exception:  # noqa: BLE001 — obuna yozuvi buzilgan bo'lsa ham javob beramiz
            plan, active, expires = None, False, None

        txs = PaymentTransaction.objects.filter(user=self.user).select_related("plan").order_by("-created_at")[:5]
        return {
            "is_premium": self.user.is_premium,
            "plan": plan,
            "subscription_active": active,
            "expires_at": expires,
            "recent_payments": [
                {
                    "plan": t.plan.name,
                    "provider": t.provider,
                    "amount_uzs": float(t.amount_uzs),
                    "status": t.status,
                    "created_at": t.created_at.isoformat(),
                    "paid_at": t.paid_at.isoformat() if t.paid_at else None,
                }
                for t in txs
            ],
        }

    def escalate_to_admin(self, category, reason):
        from .models import SupportTicket

        ticket = SupportTicket.objects.create(
            user=self.user, thread=self.thread, category=category, reason=reason[:2000]
        )
        # TODO: adminga Telegram/email xabar yuborish (masalan, Celery task orqali)
        logger.warning("Yangi murojaat %s (%s): %s", ticket.id, category, reason[:200])
        return {"ticket_id": str(ticket.id)[:8].upper(), "status": "sent_to_admin"}
