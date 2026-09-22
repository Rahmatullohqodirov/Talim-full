from django.contrib import admin
from .models import LearningSession, Transcript, VoiceCloningRequest

admin.site.register(LearningSession)
admin.site.register(Transcript)
admin.site.register(VoiceCloningRequest)
