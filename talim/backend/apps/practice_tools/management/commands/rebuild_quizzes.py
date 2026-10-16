"""Eski "CEFR darajasini top" quizlarini haqiqiy mashqlarga aylantiradi.

    python manage.py rebuild_quizzes            # so'z quizlari (offline ham ishlaydi) + grammatika (AI kerak)
    python manage.py rebuild_quizzes --no-ai    # tarjimasiz, faqat offline savollar
"""
from django.core.management.base import BaseCommand

from apps.practice_tools.models import Quiz
from apps.practice_tools.quiz_builder import kind_of, rebuild_grammar_quiz, rebuild_vocabulary_quiz


class Command(BaseCommand):
    help = "Meta-savolli (CEFR darajasini so'raydigan) quizlarni haqiqiy savollarga aylantiradi"

    def add_arguments(self, parser):
        parser.add_argument("--no-ai", action="store_true", help="AI'siz: tarjimalar to'ldirilmaydi, grammatika o'tkazib yuboriladi")

    def handle(self, *args, **opts):
        vocab = grammar = failed = 0
        for quiz in Quiz.objects.prefetch_related("questions"):
            kind = kind_of(quiz)
            if kind == "vocab":
                if rebuild_vocabulary_quiz(quiz, use_ai=not opts["no_ai"]):
                    vocab += 1
            elif kind == "grammar" and not opts["no_ai"]:
                if rebuild_grammar_quiz(quiz):
                    grammar += 1
                else:
                    failed += 1
        self.stdout.write(self.style.SUCCESS(f"So'z quizlari: {vocab}, grammatika: {grammar}"))
        if failed:
            self.stdout.write(self.style.WARNING(
                f"{failed} ta grammatika quizini tuzib bo'lmadi (AI kaliti yoki internetni tekshiring). Ular yashirin qoladi."))
