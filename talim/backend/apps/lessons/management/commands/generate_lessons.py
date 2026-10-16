"""Boshlang'ich darslar va hikoyalar kutubxonasini AI bilan to'ldiradi.

    python manage.py generate_lessons                      # english A1+A2, darslar va hikoyalar
    python manage.py generate_lessons --subject english --level A1
    python manage.py generate_lessons --stories-only
"""
from django.core.management.base import BaseCommand

from apps.subjects.models import CEFRLevel, Subject


class Command(BaseCommand):
    help = "AI yordamida boshlang'ich darslar (grammatika+lug'at+mashqlar) va hikoyalar kutubxonasini yaratadi"

    def add_arguments(self, parser):
        parser.add_argument("--subject", default="english")
        parser.add_argument("--level", default=None, help="Faqat shu daraja (masalan A1)")
        parser.add_argument("--lessons-only", action="store_true")
        parser.add_argument("--stories-only", action="store_true")

    def handle(self, *args, **opts):
        from ... import services

        subject = Subject.objects.filter(code=opts["subject"]).first()
        if not subject:
            self.stderr.write(self.style.ERROR(f"Fan topilmadi: {opts['subject']}"))
            return
        levels = CEFRLevel.objects.filter(subject=subject)
        if opts["level"]:
            levels = levels.filter(code=opts["level"].upper())
        levels = list(levels.order_by("order"))
        if not levels:
            self.stderr.write(self.style.ERROR("Daraja topilmadi."))
            return

        for level in levels:
            if level.code not in services.TOPICS_BY_LEVEL and not opts["stories_only"]:
                continue
            if not opts["stories_only"]:
                n = services.generate_lessons_for_level(subject, level)
                self.stdout.write(self.style.SUCCESS(f"{level.code}: {n} ta dars yaratildi"))
            if not opts["lessons_only"] and level.code in services.STORY_TOPICS_BY_LEVEL:
                n = services.generate_stories_for_level(subject, level)
                self.stdout.write(self.style.SUCCESS(f"{level.code}: {n} ta hikoya yaratildi"))
