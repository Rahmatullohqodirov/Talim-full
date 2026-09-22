from django.contrib import admin
from .models import SpeechAnalysis, GeneratedLesson, AIChatThread, AIChatMessage

admin.site.register(SpeechAnalysis)
admin.site.register(GeneratedLesson)
admin.site.register(AIChatThread)
admin.site.register(AIChatMessage)
