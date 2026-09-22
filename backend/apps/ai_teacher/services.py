"""AI Teacher xizmatlari: Speech Recognition, Pronunciation/Accent tahlili, Lesson Generator, AI Chat.

Tashqi provayderlar:
 - STT: Whisper (self-hosted) yoki xizmat ko'rsatuvchi API
 - Pronunciation/Accent: forced-alignment + phoneme scoring modeli
 - Lesson/Chat: xAI Grok (/v1/responses), zaxira sifatida Groq (Llama)
"""
from django.conf import settings
import requests
def transcribe_audio(audio_url: str) -> dict:
    """Whisper orqali audio -> matn. Qaytaradi: {"text": str, "confidence": float}."""
    # TODO: real Whisper/STT xizmatiga ulash (self-hosted yoki API)
    return {"text": "", "confidence": 0.0}


def analyze_pronunciation_and_accent(audio_url: str, expected_text: str) -> dict:
    """Talaffuz balli, aksent turi va fonema darajasidagi xatolarni qaytaradi."""
    # TODO: forced-alignment modeliga ulash
    return {
        "pronunciation_score": 0.0,
        "accent_similarity": 0.0,
        "detected_accent": "unknown",
        "phoneme_errors": [],
    }


def run_speech_analysis(transcript):
    """Transcript yaratilgach chaqiriladi (signal orqali) — SpeechAnalysis yozuvini to'ldiradi."""
    from .models import SpeechAnalysis

    stt_result = transcribe_audio(transcript.audio_url)
    scoring = analyze_pronunciation_and_accent(transcript.audio_url, transcript.text)
    return SpeechAnalysis.objects.update_or_create(
        transcript=transcript,
        defaults={
            "recognized_text": stt_result["text"],
            "confidence": stt_result["confidence"],
            **scoring,
        },
    )[0]


OFFLINE_FALLBACK_REPLY = (
    "Hozircha internet aloqasi yo'q (yoki AI xizmati javob bermadi), shuning uchun offline rejimda "
    "javob beryapman: davom eting, savolingizni internet tiklangach yana yuborsangiz to'liq AI javobini olasiz."
)


def _extract_responses_text(data: dict) -> str:
    """xAI (va OpenAI-uslubidagi) /v1/responses javobidan matnni ajratib oladi."""
    if data.get("output_text"):
        return data["output_text"]
    texts = []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") in ("output_text", "text"):
                    texts.append(c.get("text", ""))
    return "\n".join(t for t in texts if t).strip()


def _call_xai(prompt: str, system: str = "") -> str | None:
    """xAI Grok /v1/responses orqali chaqiradi. Muvaffaqiyatsiz bo'lsa None qaytaradi
    (shunda call_ai keyingi provayderga — Groq'ga — o'tadi)."""
    import requests

    if not settings.XAI_API_KEY:
        return None

    url = "https://api.x.ai/v1/responses"
    headers = {
        "Authorization": f"Bearer {settings.XAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": settings.XAI_MODEL, "input": prompt}
    if system:
        payload["instructions"] = system

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return None

    if resp.status_code == 429:
        return "AI so'rovlar chegarasiga yetdi. Bir necha daqiqadan so'ng qayta urinib ko'ring."
    if resp.status_code in (401, 403):
        return None  # noto'g'ri/eskirgan API kalit — Groq'ga tushamiz
    try:
        resp.raise_for_status()
        data = resp.json()
        text = _extract_responses_text(data)
        return text or None
    except (requests.exceptions.HTTPError, ValueError, KeyError):
        return None


def _call_groq(prompt: str, system: str = "") -> str:
    import requests

    if not settings.GROQ_API_KEY:
        print("❌ GROQ_API_KEY mavjud emas")
        return OFFLINE_FALLBACK_REPLY

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = []

    if system:
        messages.append({
            "role": "system",
            "content": system
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
    }

    try:
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20,
        )

        print("🔴 GROQ STATUS:", resp.status_code)
        print("🔴 GROQ RESPONSE:", resp.text)

    except Exception as e:
        print("❌ GROQ CONNECTION ERROR:", repr(e))
        return OFFLINE_FALLBACK_REPLY

    if resp.status_code == 429:
        return "AI so'rovlar chegarasiga yetdi."

    if resp.status_code == 401:
        return "GROQ API KEY noto'g'ri yoki ishlamayapti."

    if resp.status_code == 404:
        return "Groq model yoki API endpoint topilmadi."

    try:
        resp.raise_for_status()
        data = resp.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("❌ GROQ PARSE ERROR:", repr(e))
        return OFFLINE_FALLBACK_REPLY

def call_ai(prompt: str, system: str = "") -> str:
    """AI chaqiruvi (lesson generation va AI chat uchun umumiy).

    Provayder tartibi: 1) xAI Grok (XAI_API_KEY bo'lsa) → 2) Groq (GROQ_API_KEY bo'lsa,
    Grok javob bermasa yoki kaliti yo'q bo'lsa) → 3) offline fallback javob.
    Hech qanday holatda xatoga chiqarmaydi — ilova internet bilan ham, internetsiz ham ishlayveradi.
    """
    xai_reply = _call_xai(prompt, system=system)
    if xai_reply is not None:
        return xai_reply
    return _call_groq(prompt, system=system)


def _extract_json(raw: str) -> dict:
    """Gemini javobi ko'pincha ```json ... ``` bilan o'ralgan bo'ladi — shu qobiqni tozalab JSON qilib o'qiydi."""
    import json
    import re

    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def generate_lesson(user, subject, cefr_level=None):
    """Lesson Generator: foydalanuvchi darajasiga mos dars tuzadi (vocab/grammar/exercise bloklari)."""
    from .models import GeneratedLesson
    import json

    system = (
        "Sen tajribali til/matematika o'qituvchisisan. Foydalanuvchi darajasiga mos, "
        "JSON formatida struktura qaytar: {title, objective, content_blocks: [{type, data}]}."
    )
    prompt = f"Fan: {subject.name}, daraja: {cefr_level.code if cefr_level else 'boshlang\'ich'}. Yangi dars tuzib ber."
    raw = call_ai(prompt, system=system)
    try:
        parsed = _extract_json(raw)
    except (ValueError, TypeError):
        parsed = {"title": f"{subject.name} darsi", "objective": "", "content_blocks": []}

    return GeneratedLesson.objects.create(
        user=user, subject=subject, cefr_level=cefr_level,
        title=parsed.get("title", f"{subject.name} darsi"),
        objective=parsed.get("objective", ""),
        content_blocks=parsed.get("content_blocks", []),
    )


def chat_with_ai(thread, user_message: str) -> "AIChatMessage":
    """AI Chat: xabar tarixini kontekst sifatida yuborib, Claude javobini saqlaydi."""
    from .models import AIChatMessage

    AIChatMessage.objects.create(thread=thread, role=AIChatMessage.Role.USER, content=user_message)
    history = thread.messages.order_by("created_at").values("role", "content")
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    reply_text = call_ai(prompt, system="Sen SuperTutor AI repetitorisan. Qisqa, aniq va rag'batlantiruvchi javob ber.")
    return AIChatMessage.objects.create(thread=thread, role=AIChatMessage.Role.ASSISTANT, content=reply_text)
