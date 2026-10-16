from django.db import models
from common.models import BaseModel


class LearningPath(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="learning_paths")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-generated_at"]


class LearningPathItem(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"

    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name="items")
    order = models.PositiveSmallIntegerField()
    cefr_level = models.ForeignKey("subjects.CEFRLevel", null=True, blank=True, on_delete=models.SET_NULL)
    math_topic = models.ForeignKey("math_practice.MathTopic", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["order"]
        unique_together = ("path", "order")
