from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LearningSession

@receiver(post_save, sender=LearningSession)
def update_stats_on_completion(sender, instance, created, **kwargs):
    """Sessiya COMPLETED bo'lganda statistics va YouTube tavsiyalarini yangilaydi."""
    if instance.status == LearningSession.Status.COMPLETED:
        try:
            from apps.statistics.tasks import recompute_subject_stats
            recompute_subject_stats.apply(args=[str(instance.user_id), str(instance.subject_id)])
        except Exception:
            pass
        try:
            from apps.youtube_recommendations.tasks import generate_video_recommendations
            generate_video_recommendations.apply(args=[str(instance.user_id), str(instance.id)])
        except Exception:
            pass
