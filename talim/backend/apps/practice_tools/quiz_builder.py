"""Avtomatik yaratilgan "meta" quizlarni haqiqiy mashqlarga aylantirish.

Eski generator har bir savolni "Which CEFR level does the word 'X' belong to?" yoki
"What is the CEFR-J level of this grammatical item?" ko'rinishida yaratgan. Bular til o'rgatmaydi.

- So'z quizlari: shu so'zlar asosida tarjima / inglizchasini topish / to'g'ri yozilish savollari.
  AI bo'lsa tarjimalar to'ldiriladi; bo'lmasa ham imlo va so'z turkumi savollari offline tuziladi.
- Grammatika quizlari: AI orqali har bir grammatik birlik uchun haqiqiy test savoli tuziladi.
"""
import json
import logging
import random
import re

from django.db import transaction

logger = logging.getLogger(__name__)

VOCAB_META = "Which CEFR level does the word"
GRAMMAR_META = "What is the CEFR-J level"
POS_UZ = {
    "noun": "ot", "verb": "fe'l", "adjective": "sifat", "adverb": "ravish", "preposition": "predlog",
    "pronoun": "olmosh", "determiner": "aniqlovchi", "conjunction": "bog'lovchi", "number": "son",
}


def kind_of(quiz):
    first = quiz.questions.order_by("created_at").first() if hasattr(quiz, "questions") else None
    if not first:
        return None
    if first.text.startswith(VOCAB_META):
        return "vocab"
    if first.text.startswith(GRAMMAR_META):
        return "grammar"
    return None


def _misspell(word, rng):
    """Ishonarli imlo xatolari: harfni tushirish, ikkilantirish, qo'shni harflarni almashtirish, unlini almashtirish."""
    out, tries = set(), 0
    vowels = "aeiou"
    while len(out) < 3 and tries < 40:
        tries += 1
        w = list(word)
        i = rng.randrange(1, len(w) - 1) if len(w) > 2 else 0
        op = rng.choice(["drop", "double", "swap", "vowel"])
        if op == "drop":
            del w[i]
        elif op == "double":
            w.insert(i, w[i])
        elif op == "swap" and i + 1 < len(w):
            w[i], w[i + 1] = w[i + 1], w[i]
        elif op == "vowel":
            idx = [k for k, ch in enumerate(w) if ch in vowels]
            if not idx:
                continue
            k = rng.choice(idx)
            w[k] = rng.choice([v for v in vowels if v != w[k]])
        cand = "".join(w)
        if cand != word:
            out.add(cand)
    return list(out)


@transaction.atomic
def rebuild_vocabulary_quiz(quiz, use_ai=True):
    from apps.english_library.models import Vocabulary
    from apps.english_library.services import ensure_translations

    questions = list(quiz.questions.order_by("created_at"))
    pairs = []
    for q in questions:
        m = re.search(r"word '(.+?)' \((.+?)\)", q.text)
        if not m:
            continue
        word = Vocabulary.objects.filter(headword=m.group(1), pos=m.group(2)).first() \
            or Vocabulary.objects.filter(headword=m.group(1)).first()
        if word:
            pairs.append((q, word))
    if not pairs:
        return False

    if use_ai:
        try:
            ensure_translations([w for _, w in pairs], limit=25)
        except Exception:  # noqa: BLE001 — AI ishlamasa offline savollar bilan davom etamiz
            logger.warning("Quiz uchun tarjima olinmadi", exc_info=True)

    level = pairs[0][1].cefr
    rng = random.Random(str(quiz.id))
    uz_pool = list(Vocabulary.objects.filter(cefr=level).exclude(uz="").values_list("uz", flat=True)[:400])
    head_pool = list(Vocabulary.objects.filter(cefr=level).exclude(headword__contains="/").values("headword", "pos")[:600])

    for n, (q, word) in enumerate(pairs):
        head = word.headword.split("/")[0].strip()
        others_uz = [u for u in uz_pool if u.lower() != (word.uz or "").lower()]
        if word.uz and len(others_uz) >= 3:
            if n % 3 == 2:
                same_pos = [h["headword"] for h in head_pool if h["pos"] == word.pos and h["headword"] != word.headword]
                pool = same_pos if len(same_pos) >= 3 else [h["headword"] for h in head_pool if h["headword"] != word.headword]
                choices = [head] + rng.sample(pool, 3)
                text = f"“{word.uz}” inglizcha qanday bo'ladi?"
            else:
                choices = [word.uz] + rng.sample(others_uz, 3)
                text = f"“{head}” so'zining ma'nosi qaysi?"
        elif head.isalpha() and len(head) >= 4:
            choices = [head] + _misspell(head.lower(), rng)
            if len(choices) < 4:
                continue
            text = "Qaysi so'z to'g'ri yozilgan?"
        elif word.pos in POS_UZ:
            others = [v for k, v in POS_UZ.items() if k != word.pos]
            choices = [POS_UZ[word.pos]] + rng.sample(others, 3)
            text = f"“{head}” qaysi so'z turkumiga kiradi?"
        else:
            continue
        correct = choices[0]
        rng.shuffle(choices)
        q.text, q.choices, q.correct_index = text, choices, choices.index(correct)
        q.save(update_fields=["text", "choices", "correct_index"])
    return True


GRAMMAR_SYSTEM = "Sen ingliz tili o'qituvchisisan va test tuzuvchisisan. Faqat JSON qaytar."


def rebuild_grammar_quiz(quiz):
    """AI bilan grammatika savollarini tuzadi. Muvaffaqiyatli bo'lsa quiz e'lon qilinadi."""
    from apps.english_library.services import _ai_json

    questions = list(quiz.questions.order_by("created_at"))
    items = []
    for q in questions:
        parts = q.text.split("\n\n", 1)
        items.append(parts[1].strip() if len(parts) > 1 else q.text)
    level = quiz.cefr_level.code if quiz.cefr_level_id else "A2"
    listing = "\n".join(f"{i + 1}. {it}" for i, it in enumerate(items))
    prompt = (
        f"Quyidagi har bir grammatik mavzu uchun {level} darajadagi o'quvchiga mos BITTA test savoli tuz. "
        "Savol inglizcha bo'lsin (masalan bo'sh joyni to'ldirish yoki to'g'ri gapni tanlash), 4 ta variant, "
        "faqat bittasi to'g'ri. Variantlar ishonarli bo'lsin.\n"
        'Format: [{"n": 1, "question": "...", "choices": ["...", "...", "...", "..."], "correct_index": 0}]\n\n'
        + listing
    )
    data = _ai_json(prompt)
    if not isinstance(data, list):
        return False
    by_n = {int(d.get("n", 0)): d for d in data if isinstance(d, dict)}
    done = 0
    with transaction.atomic():
        for i, q in enumerate(questions):
            d = by_n.get(i + 1)
            try:
                choices = [str(c)[:200] for c in d["choices"]][:4]
                ci = int(d["correct_index"])
                if len(choices) != 4 or not 0 <= ci < 4 or not d.get("question"):
                    raise ValueError
            except (TypeError, KeyError, ValueError):
                continue
            q.text, q.choices, q.correct_index = str(d["question"])[:500], choices, ci
            q.save(update_fields=["text", "choices", "correct_index"])
            done += 1
        if done == len(questions):
            quiz.is_published = True
            quiz.save(update_fields=["is_published"])
    return done == len(questions)


def ensure_quiz_ready(quiz):
    """Quiz ochilganda chaqiriladi: eski meta-savolli so'z quizini darhol qayta tuzadi."""
    if kind_of(quiz) == "vocab":
        rebuild_vocabulary_quiz(quiz)
        return True
    return False
