from django.contrib import admin
from .models import MathTopic, MathProblem, MathAttempt

admin.site.register(MathTopic)
admin.site.register(MathProblem)
admin.site.register(MathAttempt)
