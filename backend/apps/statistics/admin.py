from django.contrib import admin
from .models import SubjectStats, DailyActivity, WeeklyReport

admin.site.register(SubjectStats)
admin.site.register(DailyActivity)
admin.site.register(WeeklyReport)
