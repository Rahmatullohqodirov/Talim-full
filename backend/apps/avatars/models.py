from django.db import models
from common.models import BaseModel


class Avatar(BaseModel):
    name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=[("male", "Male"), ("female", "Female")])
    preview_image_url = models.URLField(blank=True)
    voice_model_id = models.CharField(max_length=100)
    lip_sync_model = models.CharField(max_length=50, default="musetalk")
    is_premium_only = models.BooleanField(default=False)

    def __str__(self):
        return self.name
