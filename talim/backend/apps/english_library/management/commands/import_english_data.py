
import csv
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.english_library.models import Vocabulary, Grammar


BATCH_SIZE = 500


class Command(BaseCommand):
    help = "CEFR-J English data ni Neon PostgreSQL ga tez import qilish"

    def handle(self, *args, **options):
        base_dir = Path("data/english/source")

        files = {
            "vocabulary": base_dir / "cefrj-vocabulary-profile-1.5.csv",
            "grammar": base_dir / "cefrj-grammar-profile-20180315.csv",
            "c1c2": base_dir / "octanove-vocabulary-profile-c1c2-1.0.csv",
        }

        for name, path in files.items():
            if not path.is_file():
                raise FileNotFoundError(f"CSV topilmadi: {path}")

        with transaction.atomic():
            vocab_count = self.import_vocabulary(files["vocabulary"])
            c1c2_count = self.import_c1c2(files["c1c2"])
            grammar_count = self.import_grammar(files["grammar"])

        self.stdout.write(self.style.SUCCESS(
            f"Import tugadi: Vocabulary={vocab_count}, "
            f"C1/C2={c1c2_count}, Grammar={grammar_count}"
        ))

    def import_vocabulary(self, file_path):
        return self.import_vocab_file(file_path, include_metadata=True)

    def import_c1c2(self, file_path):
        return self.import_vocab_file(file_path, include_metadata=False)

    def import_vocab_file(self, file_path, include_metadata):
        # Mavjud yozuvlarni headword + pos bo'yicha indekslaymiz.
        existing = {
            (v.headword, v.pos): v
            for v in Vocabulary.objects.all().only(
                "id", "headword", "pos", "cefr",
                "core_inventory_1", "core_inventory_2", "threshold"
            )
        }

        to_create = []
        to_update = []

        with file_path.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                headword = (row.get("headword") or "").strip()
                if not headword:
                    continue

                pos = (row.get("pos") or "").strip()
                key = (headword, pos)
                cefr = (row.get("CEFR") or "").strip()

                if key in existing:
                    obj = existing[key]
                    obj.cefr = cefr

                    if include_metadata:
                        obj.core_inventory_1 = (
                            row.get("CoreInventory 1") or ""
                        ).strip()
                        obj.core_inventory_2 = (
                            row.get("CoreInventory 2") or ""
                        ).strip()
                        obj.threshold = (
                            row.get("Threshold") or ""
                        ).strip()

                    to_update.append(obj)
                else:
                    obj = Vocabulary(
                        headword=headword,
                        pos=pos,
                        cefr=cefr,
                        core_inventory_1=(
                            (row.get("CoreInventory 1") or "").strip()
                            if include_metadata else ""
                        ),
                        core_inventory_2=(
                            (row.get("CoreInventory 2") or "").strip()
                            if include_metadata else ""
                        ),
                        threshold=(
                            (row.get("Threshold") or "").strip()
                            if include_metadata else ""
                        ),
                    )
                    to_create.append(obj)
                    existing[key] = obj

        if to_create:
            Vocabulary.objects.bulk_create(to_create, batch_size=BATCH_SIZE)

        if to_update:
            fields = ["cefr"]
            if include_metadata:
                fields += ["core_inventory_1", "core_inventory_2", "threshold"]

            # bulk_update uchun faqat bazada avval mavjud bo'lgan obyektlar
            existing_ids = {v.id for v in Vocabulary.objects.only("id")}
            update_existing = [v for v in to_update if v.id in existing_ids]

            if update_existing:
                Vocabulary.objects.bulk_update(
                    update_existing, fields, batch_size=BATCH_SIZE
                )

        self.stdout.write(
            f"{file_path.name}: {len(to_create)} yangi, "
            f"{len(to_update)} yangilanish"
        )
        return len(to_create) + len(to_update)

    def import_grammar(self, file_path):
        existing = {
            (g.code, g.shorthand_code): g
            for g in Grammar.objects.all()
        }

        to_create = []
        to_update = []

        with file_path.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                item = (row.get("Grammatical Item") or "").strip()
                if not item:
                    continue

                code = (row.get("ID") or "").strip()
                shorthand = (row.get("Shorthand Code") or "").strip()
                key = (code, shorthand)

                values = {
                    "grammatical_item": item,
                    "sentence_type": (row.get("Sentence Type") or "").strip(),
                    "cefr_level": (row.get("CEFR-J Level") or "").strip(),
                    "freq_disp": (row.get("FREQ*DISP") or "").strip(),
                    "core_inventory": (row.get("Core Inventory") or "").strip(),
                    "egp": (row.get("EGP") or "").strip(),
                    "gselo": (row.get("GSELO") or "").strip(),
                    "notes": (row.get("Notes") or "").strip(),
                }

                if key in existing:
                    obj = existing[key]
                    for field, value in values.items():
                        setattr(obj, field, value)
                    to_update.append(obj)
                else:
                    obj = Grammar(
                        code=code,
                        shorthand_code=shorthand,
                        **values,
                    )
                    to_create.append(obj)
                    existing[key] = obj

        if to_create:
            Grammar.objects.bulk_create(to_create, batch_size=BATCH_SIZE)

        if to_update:
            Grammar.objects.bulk_update(
                to_update,
                [
                    "grammatical_item", "sentence_type", "cefr_level",
                    "freq_disp", "core_inventory", "egp", "gselo", "notes"
                ],
                batch_size=BATCH_SIZE,
            )

        self.stdout.write(
            f"{file_path.name}: {len(to_create)} yangi, "
            f"{len(to_update)} yangilanish"
        )
        return len(to_create) + len(to_update)
