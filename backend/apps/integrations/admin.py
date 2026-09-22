from django.contrib import admin
from .models import ExternalCourse, SavedExternalCourse

admin.site.register(ExternalCourse)
admin.site.register(SavedExternalCourse)