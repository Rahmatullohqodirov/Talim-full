from celery import shared_task


@shared_task
def generate_video_recommendations(user_id: str, session_id: str):
    """Sessiya COMPLETED bo'lganda chaqiriladi — AI + YouTube API orqali 3-5 ta video tavsiya qiladi."""
    from django.contrib.auth import get_user_model
    from apps.session.models import LearningSession
    from .services import recommend_videos_for_session

    User = get_user_model()
    user = User.objects.get(id=user_id)
    session = LearningSession.objects.select_related("subject").get(id=session_id)
    recommend_videos_for_session(user, session)
