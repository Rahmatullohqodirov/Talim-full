from django.contrib import admin
from .models import SpeechAnalysis, GeneratedLesson, AIChatThread, AIChatMessage, AssessmentResult, SupportTicket, LearnerMemory

admin.site.register(SpeechAnalysis)
admin.site.register(GeneratedLesson)
admin.site.register(AIChatThread)
admin.site.register(AIChatMessage)


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ("user", "subject", "kind", "score_percent", "created_at")
    list_filter = ("kind", "subject")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "status", "created_at")
    list_filter = ("category", "status")
    list_editable = ("status",)
    search_fields = ("reason", "user__username", "user__email")


@admin.register(LearnerMemory)
class LearnerMemoryAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "subject", "text", "updated_at")
    list_filter = ("category",)
    search_fields = ("text", "user__username")
