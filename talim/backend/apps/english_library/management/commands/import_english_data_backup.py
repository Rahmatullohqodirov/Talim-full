import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.english_library.models import Vocabulary, Grammar


class Command(BaseCommand):
    help = "Import CEFR-J English vocabulary and grammar data"

    def handle(self, *args, **options):
        base_dir = Path("data/english/source")

        vocabulary_file = base_dir / "cefrj-vocabulary-profile-1.5.csv"
        grammar_file = base_dir / "cefrj-grammar-profile-20180315.csv"
        c1c2_file = base_dir / "octanove-vocabulary-profile-c1c2-1.0.csv"

        with transaction.atomic():
            vocabulary_count = self.import_vocabulary(vocabulary_file)
            c1c2_count = self.import_c1c2(c1c2_file)
            grammar_count = self.import_grammar(grammar_file)

        self.stdout.write(
            self.style.SUCCESS(
                f"Import tugadi: "
                f"Vocabulary={vocabulary_count}, "
                f"C1/C2={c1c2_count}, "
                f"Grammar={grammar_count}"
            )
        )

    def import_vocabulary(self, file_path):
        count = 0

        with file_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                headword = (row.get("headword") or "").strip()

                if not headword:
                    continue

                Vocabulary.objects.update_or_create(
                    headword=headword,
                    pos=(row.get("pos") or "").strip(),
                    defaults={
                        "cefr": (row.get("CEFR") or "").strip(),
                        "core_inventory_1": (
                            row.get("CoreInventory 1") or ""
                        ).strip(),
                        "core_inventory_2": (
                            row.get("CoreInventory 2") or ""
                        ).strip(),
                        "threshold": (
                            row.get("Threshold") or ""
                        ).strip(),
                    },
                )

                count += 1

        return count

    def import_c1c2(self, file_path):
        count = 0

        with file_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                headword = (row.get("headword") or "").strip()

                if not headword:
                    continue

                Vocabulary.objects.update_or_create(
                    headword=headword,
                    pos=(row.get("pos") or "").strip(),
                    defaults={
                        "cefr": (row.get("CEFR") or "").strip(),
                    },
                )

                count += 1

        return count

    def import_grammar(self, file_path):
        count = 0

        with file_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                grammatical_item = (
                    row.get("Grammatical Item") or ""
                ).strip()

                if not grammatical_item:
                    continue

                Grammar.objects.update_or_create(
                    code=(row.get("ID") or "").strip(),
                    shorthand_code=(
                        row.get("Shorthand Code") or ""
                    ).strip(),
                    defaults={
                        "grammatical_item": grammatical_item,
                        "sentence_type": (
                            row.get("Sentence Type") or ""
                        ).strip(),
                        "cefr_level": (
                            row.get("CEFR-J Level") or ""
                        ).strip(),
                        "freq_disp": (
                            row.get("FREQ*DISP") or ""
                        ).strip(),
                        "core_inventory": (
                            row.get("Core Inventory") or ""
                        ).strip(),
                        "egp": (row.get("EGP") or "").strip(),
                        "gselo": (row.get("GSELO") or "").strip(),
                        "notes": (row.get("Notes") or "").strip(),
                    },
                )

                count += 1

        return count