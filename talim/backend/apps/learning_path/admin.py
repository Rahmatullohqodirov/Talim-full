from django.contrib import admin
from .models import LearningPath, LearningPathItem

admin.site.register(LearningPath)
admin.site.register(LearningPathItem)
