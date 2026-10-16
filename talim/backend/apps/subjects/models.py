from django.db import models
from common.models import BaseModel


class Subject(BaseModel):
    class Kind(models.TextChoices):
        LANGUAGE = "language", "Language"
        MATH = "math", "Math"

    code = models.SlugField(unique=True)   # english, russian, german, turkish, math
    name = models.CharField(max_length=50)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    is_active_in_mvp = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CEFRLevel(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="levels")
    code = models.CharField(max_length=4)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["order"]
        unique_together = ("subject", "code")

    def __str__(self):
        return f"{self.subject.code}:{self.code}"


class UserSubjectLevel(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="subject_levels")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    current_level = models.ForeignKey(CEFRLevel, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("user", "subject")
