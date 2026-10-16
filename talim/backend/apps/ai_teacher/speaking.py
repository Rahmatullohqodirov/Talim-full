"""AI Ustoz — Speaking rejimi.

Zanjir: audio -> STT (faster-whisper) -> Claude (<speak> + <feedback>) -> TTS (edge-tts)

O'rnatish (ixtiyoriy):  pip install -r requirements/speaking.txt
O'rnatilmagan bo'lsa SpeakingUnavailable chiqadi, view 501 qaytaradi va frontend
brauzerning o'z ovoz tanish funksiyasiga o'tadi.

Talaffuz bali haqida: Whisper so'z ishonchliligi (probability) talaffuzdan ko'ra audio
sifati va shovqinni ko'proq aks ettiradi. Shuning uchun ball faqat ichki statistika uchun
saqlanadi, o'quvchiga esa "mashq qilish kerak bo'lgan so'zlar" ko'rinishida beriladi.
Aniq baholash uchun keyinchalik Azure Pronunciation Assessment kabi xizmat ulang.
"""
import asyncio
import base64
import json
import logging
import re
import threading

from django.conf import settings
from django.db.models import Avg

from .agent import ClaudeUnavailable, build_system, get_client, history_to_messages
from .prompts import SPEAKING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# fan: (Whisper kodi, TTS ovozi, tilning nomi, brauzer BCP-47 kodi)
LANGS = {
    "english": ("en", "en-US-JennyNeural", "ingliz tili", "en-US"),
    "german": ("de", "de-DE-KatjaNeural", "nemis tili", "de-DE"),
    "russian": ("ru", "ru-RU-SvetlanaNeural", "rus tili", "ru-RU"),
    "turkish": ("tr", "tr-TR-EmelNeural", "turk tili", "tr-TR"),
    "uzbek": ("uz", "uz-UZ-MadinaNeural", "o'zbek tili", "uz-UZ"),
}

WEAK_THRESHOLD = 0.60
EXPLAIN_LANG = {"uz": "o'zbek tili", "ru": "rus tili", "en": "ingliz tili"}


class SpeakingUnavailable(Exception):
    """faster-whisper o'rnatilmagan yoki model yuklanmadi."""


class EmptyAudio(Exception):
    """Audioda nutq topilmadi."""


_stt_model = None
_stt_lock = threading.Lock()


def _get_stt_model():
    global _stt_model
    if _stt_model is None:
        with _stt_lock:
            if _stt_model is None:
                try:
                    from faster_whisper import WhisperModel
                except ImportError as e:
                    raise SpeakingUnavailable("faster-whisper o'rnatilmagan") from e
                try:
                    _stt_model = WhisperModel(settings.WHISPER_MODEL_SIZE, compute_type="int8")
                except Exception as e:  # noqa: BLE001 — model yuklanmadi (internet yo'q, disk, CPU...)
                    logger.exception("Whisper modelini yuklab bo'lmadi")
                    raise SpeakingUnavailable(f"Whisper modeli yuklanmadi: {e}") from e
    return _stt_model


def transcribe_auto(audio_path, allowed=("uz", "ru", "en", "tr", "de")):
    """Tilni o'zi aniqlaydi (ovozli suhbat rejimi uchun). Qaytaradi: (matn, til_kodi)."""
    model = _get_stt_model()
    segments, info = model.transcribe(audio_path, language=None, vad_filter=True)
    lang = info.language if info.language in allowed else None
    if lang is None:
        # Aniqlangan til ruxsat etilganlardan bo'lmasa, o'zbekcha deb qayta tanish
        segments, info = model.transcribe(audio_path, language="uz", vad_filter=True)
        lang = "uz"
    text = " ".join(seg.text.strip() for seg in segments).strip()
    return text, lang


def transcribe(audio_path, lang_code):
    segments, _ = _get_stt_model().transcribe(
        audio_path, language=lang_code, word_timestamps=True, vad_filter=True
    )
    words = []
    for seg in segments:
        for w in seg.words or []:
            token = w.word.strip()
            if token:
                words.append({"word": token, "confidence": round(w.probability, 2)})
    return words


def pronunciation_summary(words):
    if not words:
        return {"score": 0, "weak_words": []}
    score = round(sum(w["confidence"] for w in words) / len(words) * 100)
    weak = []
    for w in words:
        clean = re.sub(r"[^\w'-]", "", w["word"])
        if w["confidence"] < WEAK_THRESHOLD and clean and clean.lower() not in {x.lower() for x in weak}:
            weak.append(clean)
    return {"score": score, "weak_words": weak[:8]}


def _split_reply(raw):
    speak = re.search(r"<speak>(.*?)</speak>", raw, re.S)
    feedback = re.search(r"<feedback>(.*?)</feedback>", raw, re.S)
    speak_text = speak.group(1).strip() if speak else re.sub(r"<feedback>.*?</feedback>", "", raw, flags=re.S).strip()
    return speak_text, (feedback.group(1).strip() if feedback else "")


def _explain_language(user, subject_code):
    lang = getattr(user, "ui_language", "uz") or "uz"
    if subject_code == "uzbek" and lang == "uz":
        return "rus tili"  # chet ellik o'zbek tilini o'rganmoqda — tushuntirish uning tilida
    return EXPLAIN_LANG.get(lang, "o'zbek tili")


def coach_reply(user, thread, subject, level, words, summary):
    import anthropic

    _, _, lang_name, _ = LANGS[subject.code]
    transcript = " ".join(w["word"] for w in words)
    turn = (
        f"O'quvchi aytdi: {transcript}\n"
        f"So'z aniqligi: {json.dumps(words, ensure_ascii=False)}\n"
        f"Aniqligi past so'zlar: {', '.join(summary['weak_words']) or 'yo`q'}"
    )
    rows = list(thread.messages.order_by("created_at").values("role", "content"))
    messages = history_to_messages(rows, settings.AI_TUTOR_HISTORY_LIMIT)
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] += "\n\n" + turn
    else:
        messages.append({"role": "user", "content": turn})

    from .learner import build_learner_card

    system = build_system(SPEAKING_SYSTEM_PROMPT, [
        f"O'rganilayotgan til: {lang_name}",
        f"O'quvchi darajasi: {level or 'aniqlanmagan (A2 deb hisobla)'}",
        f"Tushuntirish tili (<feedback> uchun): {_explain_language(user, subject.code)}",
        "",
        *build_learner_card(user, thread),
    ])
    try:
        response = get_client().messages.create(
            model=settings.ANTHROPIC_MODEL, max_tokens=800, system=system, messages=messages
        )
        raw = "".join(b.text for b in response.content if b.type == "text")
    except (anthropic.APIError, ClaudeUnavailable):
        # Zaxira: xAI -> Groq (tool'lar kerak emas, faqat matn)
        from .services import OFFLINE_FALLBACK_REPLY, _call_groq, _call_xai
        sys_text = "\n\n".join(b["text"] for b in system)
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        raw = _call_xai(prompt, system=sys_text) or _call_groq(prompt, system=sys_text)
        if not raw or raw == OFFLINE_FALLBACK_REPLY:
            raise ClaudeUnavailable("AI provayderlari javob bermadi")
    return _split_reply(raw)


async def _tts_bytes(text, voice):
    import edge_tts

    chunks = []
    async for chunk in edge_tts.Communicate(text, voice).stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    return b"".join(chunks)


def synthesize(text, voice):
    """MP3 baytlarini qaytaradi yoki None (edge-tts yo'q / ishlamadi — frontend brauzer ovoziga o'tadi).

    Har doim alohida thread'da ishlaydi, shuning uchun WSGI ham, ASGI ham (ishlab turgan event loop) xavfsiz.
    """
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        return None
    box = {}

    def worker():
        try:
            box["audio"] = asyncio.run(_tts_bytes(text, voice))
        except Exception as e:  # noqa: BLE001 — norasmiy endpoint, istalgan vaqtda ishlamay qolishi mumkin
            logger.warning("edge-tts xatosi: %s", e)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=30)
    return box.get("audio") or None


def _save_result(user, subject, summary, transcript):
    from apps.statistics.models import SubjectStats
    from .models import AssessmentResult

    AssessmentResult.objects.create(
        user=user, subject=subject, kind=AssessmentResult.Kind.SPEAKING,
        score_percent=summary["score"], weak_topics=summary["weak_words"],
        details={"transcript": transcript[:1000], "method": "whisper_confidence_estimate"},
    )
    avg = AssessmentResult.objects.filter(
        user=user, subject=subject, kind=AssessmentResult.Kind.SPEAKING
    ).aggregate(a=Avg("score_percent"))["a"]
    stats, _ = SubjectStats.objects.get_or_create(user=user, subject=subject)
    stats.avg_pronunciation_score = round(avg or 0, 1)
    stats.save(update_fields=["avg_pronunciation_score", "updated_at"])
    from apps.gamification.services import record_activity
    record_activity(user, subject, points=3, source="speaking")


def speaking_turn(user, thread, audio_path):
    """Bitta speaking navbati. Natija xabarlari thread'ga saqlanadi."""
    from apps.subjects.models import UserSubjectLevel
    from .models import AIChatMessage

    subject = thread.subject
    if subject is None or subject.code not in LANGS:
        raise ValueError("Speaking rejimi faqat til fanlari uchun ishlaydi. Avval til fanini tanlang.")
    lang_code, voice, _, _ = LANGS[subject.code]

    words = transcribe(audio_path, lang_code)
    if not words:
        raise EmptyAudio()
    summary = pronunciation_summary(words)
    transcript = " ".join(w["word"] for w in words)

    row = UserSubjectLevel.objects.filter(user=user, subject=subject).select_related("current_level").first()
    level = row.current_level.code if row and row.current_level else None

    speak_text, feedback = coach_reply(user, thread, subject, level, words, summary)

    user_msg = AIChatMessage.objects.create(
        thread=thread, role=AIChatMessage.Role.USER, content=transcript,
        meta={"mode": "speaking", "weak_words": summary["weak_words"]},
    )
    reply_msg = AIChatMessage.objects.create(
        thread=thread, role=AIChatMessage.Role.ASSISTANT, content=speak_text,
        meta={"mode": "speaking", "feedback": feedback, "provider": "claude"},
    )
    if not thread.title:
        thread.title = f"Speaking: {transcript[:45]}"
    thread.save(update_fields=["title", "updated_at"])

    _save_result(user, subject, summary, transcript)

    audio = synthesize(speak_text, voice)
    return {
        "user_message": user_msg,
        "reply": reply_msg,
        "audio_base64": base64.b64encode(audio).decode() if audio else None,
        "audio_mime": "audio/mpeg" if audio else None,
        "weak_words": summary["weak_words"],
        "pronunciation_score": summary["score"],  # taxminiy, ichki statistika uchun
    }


def speech_lang(subject_code):
    """Frontend uchun brauzer ovoz kodi (TTS/STT fallback)."""
    return LANGS.get(subject_code, (None, None, None, "uz-UZ"))[3]


# ---------------------------------------------------------------------------
# Ovozli suhbat (o'zbek/rus/ingliz tilida erkin gaplashish, tool'lar bilan)
# ---------------------------------------------------------------------------
CHAT_VOICES = {
    "uz": "uz-UZ-MadinaNeural", "ru": "ru-RU-SvetlanaNeural", "en": "en-US-JennyNeural",
    "tr": "tr-TR-EmelNeural", "de": "de-DE-KatjaNeural",
}
BROWSER_LANGS = {"uz": "uz-UZ", "ru": "ru-RU", "en": "en-US", "tr": "tr-TR", "de": "de-DE"}


def speakable(text, limit=700):
    """Markdown belgilarini olib tashlaydi, ovoz uchun qisqartiradi."""
    t = re.sub(r"`([^`]*)`", r"\1", text or "")
    t = re.sub(r"[*_#>]+", "", t)
    t = re.sub(r"^\s*[-•]\s+", "", t, flags=re.M)
    t = re.sub(r"\n{2,}", ". ", t).replace("\n", " ")
    t = re.sub(r"\s{2,}", " ", t).strip()
    if len(t) > limit:
        cut = t[:limit]
        t = cut[: max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "), limit // 2) + 1]
    return t


def voice_chat_turn(user, thread, audio_path):
    """Ovozli suhbat: tanish (til avtomatik) -> AI Ustoz (tool'lar bilan) -> ovoz."""
    from .services import chat_with_ai

    text, lang = transcribe_auto(audio_path)
    if not text or len(text) < 2:
        raise EmptyAudio()
    reply = chat_with_ai(thread, text)
    # Ovozli xabar ekanini belgilaymiz
    user_msg = thread.messages.filter(role="user").order_by("-created_at").first()
    if user_msg:
        user_msg.meta = {**(user_msg.meta or {}), "mode": "voice", "lang": lang}
        user_msg.save(update_fields=["meta"])
    reply_lang = lang if lang in CHAT_VOICES else "uz"
    audio = synthesize(speakable(reply.content), CHAT_VOICES[reply_lang])
    return {
        "user_message": user_msg,
        "reply": reply,
        "lang": lang,
        "speech_lang": BROWSER_LANGS.get(reply_lang, "uz-UZ"),
        "audio_base64": base64.b64encode(audio).decode() if audio else None,
        "audio_mime": "audio/mpeg" if audio else None,
    }


def capabilities():
    """Serverdagi ovoz/AI imkoniyatlari (frontend qaysi yo'lni tanlashini biladi)."""
    import importlib.util

    return {
        "claude": bool(settings.ANTHROPIC_API_KEY),
        "fallback_ai": bool(getattr(settings, "XAI_API_KEY", "") or getattr(settings, "GROQ_API_KEY", "")),
        "speech_to_text": importlib.util.find_spec("faster_whisper") is not None,
        "text_to_speech": importlib.util.find_spec("edge_tts") is not None,
        "whisper_model": settings.WHISPER_MODEL_SIZE,
    }
