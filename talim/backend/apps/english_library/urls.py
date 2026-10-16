from django.urls import path

from .views import (
    AddToLearningView, DictionaryView, VocabularyAnswerView, VocabularyKnownView, VocabularyLevelsView, VocabularySessionView,
    VocabularyTestView, VocabularyWordsView,
)

urlpatterns = [
    path("vocabulary/levels/", VocabularyLevelsView.as_view(), name="vocabulary-levels"),
    path("vocabulary/session/", VocabularySessionView.as_view(), name="vocabulary-session"),
    path("vocabulary/", VocabularyWordsView.as_view(), name="vocabulary-words"),
    path("vocabulary/<int:vocabulary_id>/test/", VocabularyTestView.as_view(), name="vocabulary-test"),
    path("vocabulary/<int:vocabulary_id>/answer/", VocabularyAnswerView.as_view(), name="vocabulary-answer"),
    path("vocabulary/<int:vocabulary_id>/known/", VocabularyKnownView.as_view(), name="vocabulary-known"),
    path("vocabulary/<int:vocabulary_id>/learn/", AddToLearningView.as_view(), name="vocabulary-learn"),
    path("dictionary/", DictionaryView.as_view(), name="dictionary"),
]
