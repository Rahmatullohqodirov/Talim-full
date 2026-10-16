"""Matematik javobni tekshirish.

Avvalgi versiya yechimning oxirgi qatorini ("x = 4", "S = a^2 = 16 sm^2") to'g'ridan-to'g'ri o'quvchi
javobi ("4") bilan solishtirardi va deyarli har doim "noto'g'ri" derdi. Endi:
  - har bir masalada alohida `answers` saqlanadi (["4"] yoki ["2", "3"]);
  - o'quvchi javobi moslashuvchan o'qiladi: "4", "x=4", "x = 2 yoki x = 3", "3; 2", "78,5", "2/3", "0.67", "√16", "25%";
  - sonlar kichik yaxlitlash farqi bilan solishtiriladi.
"""
import re

UNIT_RE = re.compile(r"(sm\^?2|sm²|sm|mm|km|kg|m\^?2|so'm|so‘m|sum|%|daraja|°)", re.I)
SPLIT_RE = re.compile(r"\s*(?:;|,(?!\d)|\byoki\b|\bva\b|\bor\b|\band\b)\s*", re.I)


def _to_number(token):
    import sympy
    from sympy.parsing.sympy_parser import (
        convert_xor, implicit_multiplication_application, parse_expr, standard_transformations,
    )
    t = token.strip().lower()
    if not t:
        return None
    t = re.sub(r"√\s*(\d+(?:\.\d+)?)", r"sqrt(\1)", t)
    t = t.replace("π", "pi").replace("√", "sqrt").replace("²", "^2").replace("³", "^3").replace("×", "*").replace("÷", "/")
    t = re.sub(r"(\d),(\d)", r"\1.\2", t)          # 78,5 -> 78.5
    t = re.sub(r"^[a-z]\w*(\([^)]*\))?\s*=", "", t)  # "x = 4", "f(3) = 5"
    t = UNIT_RE.sub("", t).strip()
    if not t or re.search(r"[a-oq-z]{3,}", t.replace("sqrt", "").replace("pi", "")):
        return None
    try:
        val = parse_expr(t, transformations=standard_transformations + (implicit_multiplication_application, convert_xor))
        if val.free_symbols:
            return None
        return float(sympy.N(val))
    except Exception:  # noqa: BLE001
        return None


def parse_values(text):
    vals = []
    for part in SPLIT_RE.split(str(text or "")):
        n = _to_number(part)
        if n is not None:
            vals.append(n)
    return vals


def extract_answers(statement, steps):
    """Yechim qadamlaridan to'g'ri javob(lar)ni chiqaradi (ma'lumotlar migratsiyasi va admin uchun)."""
    if not steps:
        return []
    # "f(0) va f(5) ni toping" kabi: har bir qadam alohida javob
    func_vals = [re.match(r"^\s*\w\([^)]*\)\s*=\s*([-\d./,]+)\s*$", s) for s in steps]
    if " va " in statement and all(func_vals) and len(func_vals) > 1:
        return [m.group(1) for m in func_vals]
    last = str(steps[-1])
    parts = re.split(r"\s+(?:yoki|or)\s+", last)
    out = []
    for p in parts:
        tail = p.split("=")[-1] if "=" in p else p.split(":")[-1]
        tail = UNIT_RE.sub("", tail).strip()
        if _to_number(tail) is not None:
            out.append(tail)
    return out


def _close(a, b):
    return abs(a - b) <= max(0.01, 0.001 * abs(b))


def check_answer(problem, user_answer):
    """True / False, yoki None — masalaning sonli javobi yo'q (isbot): o'quvchi o'zini baholaydi."""
    expected = [n for n in (_to_number(a) for a in (problem.answers or [])) if n is not None]
    if not expected:
        return None
    if _matches(parse_values(user_answer), expected):
        return True
    # "2,3" — o'nli kasr emas, ikki javob bo'lishi mumkin
    if len(expected) > 1 and "," in str(user_answer):
        return _matches(parse_values(str(user_answer).replace(",", ";")), expected)
    return False


def _matches(given, expected):
    if not given or len(given) != len(expected):
        return False
    remaining = list(expected)
    for g in given:
        match = next((e for e in remaining if _close(g, e)), None)
        if match is None:
            return False
        remaining.remove(match)
    return True


def check_answer_with_sympy(problem, user_answer: str) -> bool:
    """Eski nom (orqaga moslik uchun)."""
    return bool(check_answer(problem, user_answer))
