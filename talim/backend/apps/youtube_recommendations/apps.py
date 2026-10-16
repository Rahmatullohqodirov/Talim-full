from django.apps import AppConfig


class YoutubeRecommendationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.youtube_recommendations"

    def ready(self):
        from . import signals  # noqa
