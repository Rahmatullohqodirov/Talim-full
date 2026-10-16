"""O'quvchi kartasi: Claude'ga har so'rovda beriladigan qisqa profil.

Kartada: ism, darajalar, eslab qolingan faktlar (qiziqish, uslub, xatolar...), oxirgi
natijalar, joriy va oxirgi darslar. Shu sababli yangi suhbatda ham AI Ustoz o'quvchini
"taniydi" va javoblarini uning xarakteriga moslaydi.

Karta keshlanmaydigan blokda yuboriladi (statik promptdan keyin), shuning uchun
o'zgarishi prompt keshini buzmaydi.
"""

LANG_NAMES = {"uz": "o'zbek", "ru": "rus", "en": "ingliz"}
STEP_MARK = {"correct": "✓", "partly": "~", "wrong": "✗", "done": "✓"}
MAX_MEMORIES_IN_CARD = 30


def _fmt_date(dt):
    return dt.strftime("%d.%m") if dt else ""


def build_learner_card(user, thread=None):
    from apps.subjects.models import UserSubjectLevel
    from .models import AssessmentResult, GeneratedLesson, LearnerMemory

    name = (user.first_name or user.username or "").strip()
    lines = [
        f"Ismi: {name or 'noma`lum'}",
        f"Interfeys tili: {LANG_NAMES.get(user.ui_language, user.ui_language)}",
        f"Premium: {'ha' if user.is_premium else 'yo`q'}",
    ]
    if thread is not None and thread.subject_id:
        lines.append(f"Shu suhbat fani: {thread.subject.name} (kod: {thread.subject.code})")
    else:
        lines.append("Shu suhbat uchun fan tanlanmagan")

    levels = [
        f"{r.subject.code}: {r.current_level.code}"
        for r in UserSubjectLevel.objects.filter(user=user, current_level__isnull=False)
        .select_related("subject", "current_level")
    ]
    lines.append("Darajalar: " + (", ".join(levels) if levels else "hali aniqlanmagan"))

    # --- Eslab qolingan faktlar ---
    memories = list(
        LearnerMemory.objects.filter(user=user).select_related("subject").order_by("-updated_at")[:MAX_MEMORIES_IN_CARD]
    )
    lines.append("")
    if memories:
        lines.append("ESLAB QOLINGAN FAKTLAR (forget_about_student uchun [#id]):")
        for m in memories:
            subj = f", {m.subject.code}" if m.subject_id else ""
            lines.append(f"- [#{str(m.id)[:8]}] ({m.get_category_display()}{subj}) {m.text}")
    else:
        lines.append("ESLAB QOLINGAN FAKTLAR: hali yo'q. Suhbat davomida o'quvchini tanib, muhimlarini saqla.")

    # --- O'quv rejalari ---
    from django.utils import timezone as _tz
    from .plans import active_plans, items_for_day, plan_progress

    plans = active_plans(user)
    if plans:
        today = _tz.localdate()
        lines.append("")
        lines.append(f"FAOL O'QUV REJALARI (bugun {today.isoformat()}):")
        for p in plans:
            prog = plan_progress(p)
            subj = p.subject.code if p.subject_id else "-"
            lines.append(f"- [#{str(p.id)[:8]}] {p.get_period_display()} ({subj}) \"{p.title}\" "
                         f"{p.start_date:%d.%m}–{p.end_date:%d.%m}, bajarildi {prog['done']}/{prog['total']}")
            todays = items_for_day(p, today)
            label = "shu hafta" if p.period == "monthly" else "bugun"
            for it in todays[:6]:
                lines.append(f"    {'✓' if it.get('done') else '·'} {label}: [{it['id']}] {it['title']} ({it['minutes']} daq)")
    else:
        lines.append("")
        lines.append("FAOL O'QUV REJASI: yo'q. Mos paytda kunlik/haftalik/oylik reja tuzishni taklif qilishing mumkin.")

    # --- Oxirgi natijalar ---
    results = list(AssessmentResult.objects.filter(user=user).select_related("subject").order_by("-created_at")[:4])
    if results:
        lines.append("")
        lines.append("OXIRGI NATIJALAR:")
        for r in results:
            weak = f"; zaif: {', '.join(r.weak_topics[:4])}" if r.weak_topics else ""
            score = "taxminiy talaffuz" if r.kind == "speaking" else f"{round(r.score_percent)}%"
            lines.append(f"- {_fmt_date(r.created_at)} {r.subject.code} {r.get_kind_display()}: {score}{weak}")

    # --- Joriy dars (shu suhbatda) ---
    active = None
    if thread is not None:
        active = GeneratedLesson.objects.filter(thread=thread, is_completed=False, completed_at__isnull=True).first()
    if active:
        steps = active.content_blocks or []
        lines.append("")
        lines.append(f"JORIY DARS: \"{active.title}\" — maqsad: {active.objective}")
        for i, st in enumerate(steps):
            mark = STEP_MARK.get(st.get("result"), "✓") if st.get("done") else ("→" if i == active.current_step else " ")
            note = f" ({st['note']})" if st.get("note") else ""
            lines.append(f"  {mark} {i + 1}. {st.get('title')}{note}")
        lines.append("Darsni joriy (→) qadamdan davom ettir.")

    # --- Oxirgi darslar ---
    recent = list(
        GeneratedLesson.objects.filter(user=user, thread__isnull=False)
        .exclude(id=active.id if active else None)
        .select_related("subject").order_by("-updated_at")[:3]
    )
    if recent:
        lines.append("")
        lines.append("OXIRGI DARSLAR:")
        for l in recent:
            if l.is_completed:
                score = f", {round(l.score_percent)}%" if l.score_percent is not None else ""
                nxt = f" Keyingi qadam: {l.next_step}" if l.next_step else ""
                lines.append(f"- {_fmt_date(l.updated_at)} {l.subject.code} \"{l.title}\" — tugallangan{score}.{nxt}")
            else:
                done = sum(1 for st in (l.content_blocks or []) if st.get("done"))
                lines.append(f"- {_fmt_date(l.updated_at)} {l.subject.code} \"{l.title}\" — tugallanmagan "
                             f"({done}/{len(l.content_blocks or [])} qadam)")
    return lines


def lesson_state(thread):
    """Frontend uchun joriy dars holati (yoki None)."""
    from .models import GeneratedLesson

    if thread is None:
        return None
    lesson = (
        GeneratedLesson.objects.filter(thread=thread, is_completed=False, completed_at__isnull=True).first()
        or GeneratedLesson.objects.filter(thread=thread).order_by("-updated_at").first()
    )
    if not lesson:
        return None
    return {
        "id": str(lesson.id),
        "title": lesson.title,
        "objective": lesson.objective,
        "steps": [
            {"title": st.get("title"), "type": st.get("type"), "done": bool(st.get("done")), "result": st.get("result")}
            for st in (lesson.content_blocks or [])
        ],
        "current_step": lesson.current_step,
        "is_completed": lesson.is_completed,
        "abandoned": bool(lesson.completed_at and not lesson.is_completed),
        "score_percent": lesson.score_percent,
        "summary": lesson.summary,
        "next_step": lesson.next_step,
    }
