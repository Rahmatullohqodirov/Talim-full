from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizAttempt, Flashcard, FlashcardReview

admin.site.register(Quiz)
admin.site.register(QuizQuestion)
admin.site.register(QuizAttempt)
admin.site.register(Flashcard)
admin.site.register(FlashcardReview)
