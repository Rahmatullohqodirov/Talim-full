"""AI Ustoz agenti: Claude + tool'lar sikli.

Asosiy farqlar (avvalgi optima_agent.py ga nisbatan):
- user_id modelga berilmaydi, tool'lar request.user ga bog'langan (TutorToolbox)
- tool aylanishlari soni cheklangan (AI_TUTOR_MAX_TOOL_ROUNDS)
- suhbat tarixidan faqat oxirgi N ta xabar yuboriladi
- system prompt va tool'lar keshlanadi (prompt caching), o'quvchi ma'lumoti keshdan keyin
"""
import json
import logging
from functools import lru_cache

from django.conf import settings

from .prompts import TUTOR_SYSTEM_PROMPT
from .tools import TOOLS, ToolError, TutorToolbox

logger = logging.getLogger(__name__)

class ClaudeUnavailable(Exception):
    """Claude sozlanmagan yoki javob bermadi — chaqiruvchi zaxira provayderga o'tadi."""


@lru_cache(maxsize=1)
def get_client():
    if not settings.ANTHROPIC_API_KEY:
        raise ClaudeUnavailable("ANTHROPIC_API_KEY sozlanmagan")
    import anthropic

    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY, max_retries=2, timeout=60)


def _cached_tools():
    tools = [dict(t) for t in TOOLS]
    tools[-1]["cache_control"] = {"type": "ephemeral"}
    return tools


def build_system(static_prompt, context_lines):
    """Statik qism keshlanadi, o'quvchiga xos qism alohida (keshlanmaydigan) blokda."""
    return [
        {"type": "text", "text": static_prompt, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": "O'QUVCHI KARTASI (faqat shu o'quvchi haqida, ichki ma'lumot):\n" + "\n".join(context_lines)},
    ]


def history_to_messages(rows, limit):
    """DB'dagi xabarlarni Claude formatiga o'tkazadi: oxirgi `limit` ta, user bilan boshlanadi,
    ketma-ket bir xil rollar birlashtiriladi (Claude navbatma-navbat rollarni talab qiladi)."""
    rows = list(rows)[-limit:]
    messages = []
    for r in rows:
        text = (r["content"] or "").strip()
        if not text:
            continue
        if messages and messages[-1]["role"] == r["role"]:
            messages[-1]["content"] += "\n\n" + text
        else:
            messages.append({"role": r["role"], "content": text})
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    return messages


def run_tutor(user, thread, messages):
    """Claude bilan tool siklini yuritadi. Qaytaradi: (javob_matni, ishlatilgan_tool'lar)."""
    import anthropic

    client = get_client()
    toolbox = TutorToolbox(user, thread)
    from .learner import build_learner_card

    system = build_system(TUTOR_SYSTEM_PROMPT, build_learner_card(user, thread))
    tools = _cached_tools()
    tools_used = []
    convo = list(messages)

    for _ in range(settings.AI_TUTOR_MAX_TOOL_ROUNDS):
        try:
            response = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1500,
                system=system,
                tools=tools,
                messages=convo,
            )
        except anthropic.APIError as e:
            logger.warning("Claude API xatosi: %s", e)
            raise ClaudeUnavailable(str(e)) from e

        text = "".join(b.text for b in response.content if b.type == "text").strip()
        if response.stop_reason != "tool_use":
            return text, tools_used

        # SDK obyektlarini oddiy dict'ga o'tkazamiz (JSON'ga saqlash mumkin bo'lishi uchun)
        convo.append({"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in response.content]})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tools_used.append(block.name)
            try:
                payload = toolbox.run(block.name, dict(block.input or {}))
                content, is_error = json.dumps(payload, ensure_ascii=False, default=str), False
            except ToolError as e:
                content, is_error = str(e), True
            except TypeError as e:  # model noto'g'ri argument yuborsa
                content, is_error = f"Noto'g'ri argumentlar: {e}", True
            except Exception:  # noqa: BLE001
                logger.exception("Tool %s xatosi", block.name)
                content, is_error = "Ichki xatolik, keyinroq qayta urinib ko'ring.", True
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": content, "is_error": is_error})
        convo.append({"role": "user", "content": results})

    logger.warning("AI Ustoz: tool aylanishlari chegarasiga yetildi (thread=%s)", getattr(thread, "id", None))
    return (
        "Kechirasiz, bu so'rovni hozir oxiriga yetkaza olmadim. Savolni biroz soddaroq qilib qayta yuboring.",
        tools_used,
    )


def simple_completion(prompt, system="", max_tokens=1500):
    """Tool'larsiz oddiy Claude chaqiruvi (lesson generator, matematika tushuntirishi, avatar uchun)."""
    import anthropic

    client = get_client()
    kwargs = {}
    if system:
        kwargs["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
    try:
        response = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
    except anthropic.APIError as e:
        logger.warning("Claude API xatosi: %s", e)
        raise ClaudeUnavailable(str(e)) from e
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        raise ClaudeUnavailable("bo'sh javob")
    return text
