from django.contrib import admin
from .models import Subject, CEFRLevel, UserSubjectLevel

admin.site.register(Subject)
admin.site.register(CEFRLevel)
admin.site.register(UserSubjectLevel)
