from django.db import models
from common.models import BaseModel


class ExternalCourse(BaseModel):
    """Kelajakdagi integratsiyalar: LinkedIn Learning, Coursera, Khan Academy, Google Books.
    Hozircha admin tomonidan kuratsiya qilingan havolalar sifatida saqlanadi; keyinchalik
    har bir provayder uchun rasmiy partner API ulanganda shu jadval avtomatik to'ldiriladi."""

    class Source(models.TextChoices):
        LINKEDIN_LEARNING = "linkedin_learning", "LinkedIn Learning"
        COURSERA = "coursera", "Coursera"
        KHAN_ACADEMY = "khan_academy", "Khan Academy"
        GOOGLE_BOOKS = "google_books", "Google Books"

    source = models.CharField(max_length=20, choices=Source.choices)
    subject = models.ForeignKey("subjects.Subject", null=True, blank=True, on_delete=models.SET_NULL, related_name="external_courses")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField()
    thumbnail_url = models.URLField(blank=True)
    level = models.CharField(max_length=20, blank=True)  # masalan: "Beginner", "B1", "Intermediate"
    is_premium_only = models.BooleanField(default=False)

    class Meta:
        ordering = ["source", "title"]
        indexes = [models.Index(fields=["source", "subject"])]

    def __str__(self):
        return f"{self.get_source_display()}: {self.title}"


class SavedExternalCourse(BaseModel):
    """Foydalanuvchi saqlagan tashqi kurslar (Sevimlilar)."""
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="saved_external_courses")
    course = models.ForeignKey(ExternalCourse, on_delete=models.CASCADE, related_name="saved_by")

    class Meta:
        unique_together = ("user", "course")
