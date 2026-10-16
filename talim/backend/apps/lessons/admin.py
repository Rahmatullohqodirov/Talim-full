from django.contrib import admin

from .models import Lesson, LessonExercise, LessonWord, Story, StoryQuestion


class LessonWordInline(admin.TabularInline):
    model = LessonWord
    extra = 0


class LessonExerciseInline(admin.TabularInline):
    model = LessonExercise
    extra = 0


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "subject", "cefr_level", "order", "is_published"]
    list_filter = ["subject", "cefr_level", "is_published"]
    inlines = [LessonWordInline, LessonExerciseInline]


class StoryQuestionInline(admin.TabularInline):
    model = StoryQuestion
    extra = 0


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ["title", "subject", "cefr_level", "order", "is_published"]
    list_filter = ["subject", "cefr_level", "is_published"]
    inlines = [StoryQuestionInline]
