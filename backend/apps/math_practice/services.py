import sympy
from sympy.parsing.sympy_parser import parse_expr


def check_answer_with_sympy(problem, user_answer: str) -> bool:
    """Masalaning oxirgi solution_steps qadamidagi javobni foydalanuvchi javobi bilan simvolik solishtiradi."""
    if not problem.solution_steps:
        return False
    try:
        expected = parse_expr(str(problem.solution_steps[-1]))
        given = parse_expr(user_answer)
        return sympy.simplify(expected - given) == 0
    except Exception:
        return user_answer.strip() == str(problem.solution_steps[-1]).strip()
