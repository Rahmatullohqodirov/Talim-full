from django.contrib import admin

from .models import Vocabulary, VocabularyProgress, Grammar


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = (
        "headword",
        "pos",
        "cefr",
        "core_inventory_1",
        "core_inventory_2",
        "threshold",
    )

    list_filter = (
        "cefr",
        "pos",
    )

    search_fields = (
        "headword",
    )

    ordering = (
        "cefr",
        "headword",
    )


@admin.register(Grammar)
class GrammarAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "shorthand_code",
        "grammatical_item",
        "sentence_type",
        "cefr_level",
    )

    list_filter = (
        "cefr_level",
        "sentence_type",
    )

    search_fields = (
        "grammatical_item",
        "code",
        "shorthand_code",
    )

    ordering = (
        "cefr_level",
        "grammatical_item",
    )


@admin.register(VocabularyProgress)
class VocabularyProgressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "vocabulary",
        "mastery",
        "correct_answers",
        "wrong_answers",
        "last_reviewed",
    )

    list_filter = (
        "mastery",
    )

    search_fields = (
        "user__username",
        "vocabulary__headword",
    )

    ordering = (
        "-updated_at",
    )