from django.db import models
from common.models import BaseModel


class MathTopic(BaseModel):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="subtopics")

    def __str__(self):
        return self.name


class MathProblem(BaseModel):
    class Difficulty(models.IntegerChoices):
        EASY = 1, "Easy"
        MEDIUM = 2, "Medium"
        HARD = 3, "Hard"

    topic = models.ForeignKey(MathTopic, on_delete=models.CASCADE, related_name="problems")
    statement = models.TextField()
    solution_steps = models.JSONField(default=list)
    graph_data = models.JSONField(null=True, blank=True)
    difficulty = models.PositiveSmallIntegerField(choices=Difficulty.choices, default=Difficulty.EASY)

    class Meta:
        indexes = [models.Index(fields=["topic", "difficulty"])]


class MathAttempt(BaseModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="math_attempts")
    problem = models.ForeignKey(MathProblem, on_delete=models.CASCADE, related_name="attempts")
    session = models.ForeignKey("session.LearningSession", null=True, on_delete=models.SET_NULL)
    is_correct = models.BooleanField()
    user_answer = models.TextField(blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "problem"])]
