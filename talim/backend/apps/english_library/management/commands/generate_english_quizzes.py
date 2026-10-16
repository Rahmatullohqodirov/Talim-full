import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.english_library.models import Vocabulary, Grammar
from apps.practice_tools.models import Quiz, QuizQuestion
from apps.subjects.models import Subject


class Command(BaseCommand):
    help = "OpenLanguageProfiles English quizlarini bo'limlarga ajratib yaratadi."

    LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]

    # Har bir bo'limda nechta savol bo'ladi
    QUESTIONS_PER_SECTION = 20

    BATCH_SIZE = 500

    def handle(self, *args, **options):
        english = Subject.objects.filter(code="english").first()

        if not english:
            self.stdout.write(
                self.style.ERROR("English fani topilmadi.")
            )
            return

        with transaction.atomic():

            # Oldingi generator yaratgan quizlarni o'chiramiz
            old_quizzes = Quiz.objects.filter(
                subject=english
            ).filter(
                title__contains="OpenLanguageProfiles"
            )

            old_quizzes_count = old_quizzes.count()

            old_quizzes.delete()

            # Eski CEFR-J grammar quizlarini ham o'chiramiz
            old_grammar_quizzes = Quiz.objects.filter(
                subject=english
            ).filter(
                title__contains="CEFR-J"
            )

            old_grammar_count = old_grammar_quizzes.count()

            old_grammar_quizzes.delete()

            self.stdout.write(
                self.style.WARNING(
                    f"Eski {old_quizzes_count + old_grammar_count} ta quiz o'chirildi."
                )
            )

            total_created = 0

            # =========================
            # VOCABULARY
            # =========================

            for level in self.LEVELS:

                created = self.create_vocabulary_sections(
                    english,
                    level,
                )

                total_created += created

            # =========================
            # GRAMMAR
            # =========================

            grammar_created = self.create_grammar_sections(
                english
            )

            total_created += grammar_created

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTAYYOR!"
                f"\nJami {total_created} ta QuizQuestion yaratildi."
            )
        )

    # ==========================================================
    # VOCABULARY
    # ==========================================================

    def create_vocabulary_sections(self, subject, level):

        words = list(
            Vocabulary.objects
            .filter(cefr__iexact=level)
            .exclude(headword="")
            .values(
                "id",
                "headword",
                "pos",
            )
        )

        if not words:
            self.stdout.write(
                self.style.WARNING(
                    f"{level}: vocabulary topilmadi."
                )
            )
            return 0

        random.shuffle(words)

        total_words = len(words)

        total_sections = (
            total_words + self.QUESTIONS_PER_SECTION - 1
        ) // self.QUESTIONS_PER_SECTION

        total_created = 0

        for section_number in range(total_sections):

            start = (
                section_number
                * self.QUESTIONS_PER_SECTION
            )

            end = start + self.QUESTIONS_PER_SECTION

            section_words = words[start:end]

            title = (
                f"{level} Vocabulary — "
                f"Bo'lim {section_number + 1}"
            )

            quiz = Quiz.objects.create(
                subject=subject,
                title=title,
                cefr_level=None,
            )

            questions = []

            for word in section_words:

                headword = word["headword"]
                pos = word["pos"]

                # Boshqa CEFR darajalaridan 3 ta variant
                other_levels = [
                    x
                    for x in self.LEVELS
                    if x != level
                ]

                # Savol:
                # So'z qaysi CEFR darajasiga tegishli?
                choices = random.sample(
                    other_levels,
                    3,
                )

                correct_index = random.randint(
                    0,
                    3,
                )

                choices.insert(
                    correct_index,
                    level,
                )

                pos_text = ""

                if pos:
                    pos_text = f" ({pos})"

                text = (
                    f"Which CEFR level does the word "
                    f"'{headword}'{pos_text} belong to?"
                )

                questions.append(
                    QuizQuestion(
                        quiz=quiz,
                        text=text,
                        choices=choices,
                        correct_index=correct_index,
                    )
                )

            # Tez yozish
            for start_batch in range(
                0,
                len(questions),
                self.BATCH_SIZE,
            ):

                batch = questions[
                    start_batch:
                    start_batch + self.BATCH_SIZE
                ]

                QuizQuestion.objects.bulk_create(
                    batch
                )

            created_count = len(questions)

            total_created += created_count

            self.stdout.write(
                self.style.SUCCESS(
                    f"{title}: "
                    f"{created_count} ta savol"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{level}: jami {total_words} ta vocabulary, "
                f"{total_sections} ta bo'lim"
            )
        )

        return total_created

    # ==========================================================
    # GRAMMAR
    # ==========================================================

    def create_grammar_sections(self, subject):

        grammar_items = list(
            Grammar.objects
            .exclude(grammatical_item="")
            .values(
                "id",
                "grammatical_item",
                "cefr_level",
            )
        )

        if not grammar_items:
            return 0

        grammar_levels = sorted(
            set(
                item["cefr_level"]
                for item in grammar_items
                if item["cefr_level"]
            )
        )

        total_created = 0

        for level in grammar_levels:

            level_items = [
                item
                for item in grammar_items
                if item["cefr_level"] == level
            ]

            if not level_items:
                continue

            random.shuffle(level_items)

            total_items = len(level_items)

            total_sections = (
                total_items
                + self.QUESTIONS_PER_SECTION
                - 1
            ) // self.QUESTIONS_PER_SECTION

            for section_number in range(total_sections):

                start = (
                    section_number
                    * self.QUESTIONS_PER_SECTION
                )

                end = (
                    start
                    + self.QUESTIONS_PER_SECTION
                )

                section_items = level_items[
                    start:end
                ]

                title = (
                    f"{level} Grammar — "
                    f"Bo'lim {section_number + 1}"
                )

                quiz = Quiz.objects.create(
                    subject=subject,
                    title=title,
                    cefr_level=None,
                )

                questions = []

                other_levels = [
                    x
                    for x in grammar_levels
                    if x != level
                ]

                for item in section_items:

                    if len(other_levels) < 3:
                        continue

                    choices = random.sample(
                        other_levels,
                        3,
                    )

                    correct_index = random.randint(
                        0,
                        3,
                    )

                    choices.insert(
                        correct_index,
                        level,
                    )

                    text = (
                        "What is the CEFR-J level of "
                        "this grammatical item?\n\n"
                        f"{item['grammatical_item']}"
                    )

                    questions.append(
                        QuizQuestion(
                            quiz=quiz,
                            text=text,
                            choices=choices,
                            correct_index=correct_index,
                        )
                    )

                for start_batch in range(
                    0,
                    len(questions),
                    self.BATCH_SIZE,
                ):

                    batch = questions[
                        start_batch:
                        start_batch + self.BATCH_SIZE
                    ]

                    QuizQuestion.objects.bulk_create(
                        batch
                    )

                created_count = len(questions)

                total_created += created_count

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{title}: "
                        f"{created_count} ta savol"
                    )
                )

        return total_created