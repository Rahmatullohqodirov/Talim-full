from rest_framework import serializers
from .models import Avatar


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avatar
        fields = ["id", "name", "gender", "preview_image_url", "is_premium_only"]
