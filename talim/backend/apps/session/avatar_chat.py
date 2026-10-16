"""Avatar bilan rolli suhbat: vaziyat (scenario) + o'quvchi darajasi + avatar ovozi.

AI Ustozdan farqi: avatar dars o'tmaydi, balki suhbatdosh rolini o'ynaydi (ofitsiant, mehmonxona
xodimi, intervyu oluvchi...). Xatolar suhbat oqimini buzmasligi uchun alohida izohda beriladi.
"""
import base64
import logging
import re

logger = logging.getLogger(__name__)

SCENARIOS = {
    "free": ("Erkin suhbat", "a friendly conversation partner chatting about everyday life, hobbies and plans"),
    "cafe": ("Kafeda", "a waiter in a cafe taking the student's order and chatting politely"),
    "travel": ("Aeroportda", "an airport check-in agent helping the student with their flight and luggage"),
    "hotel": ("Mehmonxonada", "a hotel receptionist checking the student in and answering questions"),
    "shop": ("Do'konda", "a shop assistant helping the student choose and buy clothes"),
    "interview": ("Ish suhbati", "a friendly HR manager conducting a job interview with the student"),
    "doctor": ("Shifokorda", "a family doctor asking the student about how they feel"),
    "ielts": ("IELTS Speaking", "an IELTS speaking examiner asking Part 1 and Part 2 questions"),
}

LANGS = {
    "english": ("English", {"american": ("en-US", {"male": "en-US-GuyNeural", "female": "en-US-JennyNeural"}),
                            "british": ("en-GB", {"male": "en-GB-RyanNeural", "female": "en-GB-SoniaNeural"})}),
    "german": ("German", {"default": ("de-DE", {"male": "de-DE-ConradNeural", "female": "de-DE-KatjaNeural"})}),
    "russian": ("Russian", {"default": ("ru-RU", {"male": "ru-RU-DmitryNeural", "female": "ru-RU-SvetlanaNeural"})}),
    "turkish": ("Turkish", {"default": ("tr-TR", {"male": "tr-TR-AhmetNeural", "female": "tr-TR-EmelNeural"})}),
}


def voice_for(subject_code, accent, gender):
    _, variants = LANGS.get(subject_code, LANGS["english"])
    lang, voices = variants.get(accent) or next(iter(variants.values()))
    return lang, voices.get(gender or "female", next(iter(voices.values())))


def build_system(session, accent, level, explain_lang):
    lang_name, _ = LANGS.get(session.subject.code, LANGS["english"])
    _, role = SCENARIOS.get(session.scenario or "free", SCENARIOS["free"])
    name = session.avatar.name if session.avatar_id else "Alex"
    accent_rule = ""
    if session.subject.code == "english":
        accent_rule = ("Use British spelling and vocabulary (colour, flat, queue). " if accent == "british"
                       else "Use American spelling and vocabulary (color, apartment, line). ")
    return (
        f"You are {name}, an AI conversation partner on the OPTIMA Ta'lim language platform. "
        f"Role-play: you are {role}. Stay in this role and speak ONLY {lang_name}. {accent_rule}"
        f"The student's level is {level or 'A2'} (CEFR): use vocabulary and grammar at that level, short sentences, "
        "1-3 sentences per reply, and always end with a question that keeps the conversation going. "
        "Be warm and encouraging. Never discuss topics unrelated to learning; never produce unsafe content.\n\n"
        "Reply in exactly two parts:\n"
        "<speak>your in-role reply (spoken aloud, no emojis, no lists)</speak>\n"
        f"<feedback>if the student's last message had mistakes, list at most 2 corrections in {explain_lang}: "
        "'wrong → correct (short reason)'. If there were no mistakes, leave this empty.</feedback>"
    )


def split_reply(raw):
    speak = re.search(r"<speak>(.*?)</speak>", raw or "", re.S)
    fb = re.search(r"<feedback>(.*?)</feedback>", raw or "", re.S)
    text = speak.group(1).strip() if speak else re.sub(r"</?\w+>", "", raw or "").strip()
    return text, (fb.group(1).strip() if fb else "")


def generate_reply(session, accent):
    """AI javobi: Claude (tool'larsiz) -> xAI -> Groq. Qaytaradi (matn, izoh)."""
    from apps.ai_teacher.agent import ClaudeUnavailable, get_client
    from apps.ai_teacher.services import OFFLINE_FALLBACK_REPLY, _call_groq, _call_xai
    from apps.subjects.models import UserSubjectLevel
    from django.conf import settings

    user = session.user
    row = UserSubjectLevel.objects.filter(user=user, subject=session.subject).select_related("current_level").first()
    level = row.current_level.code if row and row.current_level else None
    explain = {"ru": "Russian", "en": "English"}.get(getattr(user, "ui_language", "uz"), "Uzbek (Latin script)")
    system = build_system(session, accent, level, explain)

    turns = list(session.turns.order_by("created_at").values("speaker", "text"))[-16:]
    messages = []
    for t in turns:
        role = "user" if t["speaker"] == "user" else "assistant"
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += "\n" + t["text"]
        else:
            messages.append({"role": role, "content": t["text"]})
    while messages and messages[0]["role"] != "user":
        messages.pop(0)

    raw = None
    try:
        import anthropic
        resp = get_client().messages.create(model=settings.ANTHROPIC_MODEL, max_tokens=400,
                                            system=system, messages=messages)
        raw = "".join(b.text for b in resp.content if b.type == "text")
    except Exception as e:  # noqa: BLE001 — ClaudeUnavailable yoki API xatosi: zaxiraga o'tamiz
        if not isinstance(e, ClaudeUnavailable):
            logger.warning("Avatar: Claude xatosi: %s", e)
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        raw = _call_xai(prompt, system=system) or _call_groq(prompt, system=system)
        if raw == OFFLINE_FALLBACK_REPLY:
            return raw, ""
    return split_reply(raw)


def synthesize_reply(session, accent, text):
    from apps.ai_teacher.speaking import synthesize

    gender = session.avatar.gender if session.avatar_id else "female"
    lang, voice = voice_for(session.subject.code, accent, gender)
    audio = synthesize(text, voice)
    return lang, (base64.b64encode(audio).decode() if audio else None)
