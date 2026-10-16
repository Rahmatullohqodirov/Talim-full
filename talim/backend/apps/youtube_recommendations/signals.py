from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import VideoRating, YoutubeVideo


@receiver([post_save, post_delete], sender=VideoRating)
def update_video_avg_rating(sender, instance, **kwargs):
    video = instance.video
    avg = VideoRating.objects.filter(video=video).aggregate(avg=Avg("stars"))["avg"] or 0
    video.avg_rating = round(avg, 2)
    video.save(update_fields=["avg_rating"])
