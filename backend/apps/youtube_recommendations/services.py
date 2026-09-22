import logging
logger = logging.getLogger(__name__)
from django.conf import settings

YOUTUBE_SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"
MAX_RECOMMENDATIONS = 5


def determine_weak_topic(user, subject):
    """Foydalanuvchining shu fandagi eng past ballini beruvchi mavzuni topadi."""
    from apps.math_practice.models import MathAttempt
    from django.db.models import Avg, Count

    weakest = (
        MathAttempt.objects.filter(user=user, problem__topic__isnull=False)
        .values("problem__topic__name")
        .annotate(accuracy=Avg("is_correct"), attempts=Count("id"))
        .filter(attempts__gte=3)
        .order_by("accuracy")
        .first()
    )
    return weakest["problem__topic__name"] if weakest else None


def search_youtube(query: str, language: str = "en", max_results: int = MAX_RECOMMENDATIONS):
    """YouTube Data API v3 'search' chaqiruvi. API kaliti .env dagi YOUTUBE_API_KEY dan olinadi."""
    import requests

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "relevanceLanguage": language,
        "videoDuration": "medium",
        "key": settings.YOUTUBE_API_KEY,
        "safeSearch": "strict",
    }
    try:
        resp = requests.get(YOUTUBE_SEARCH_ENDPOINT, params=params, timeout=8)
        resp.raise_for_status()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError):
        return []  # internet/YouTube yo'q — offline: bo'sh natija, xato chiqarilmaydi
    return resp.json().get("items", [])


def upsert_videos_from_search(items, subject=None, difficulty="beginner"):
    from .models import YoutubeVideo

    videos = []
    for item in items:
        vid = item["id"]["videoId"]
        snippet = item["snippet"]
        video, _ = YoutubeVideo.objects.update_or_create(
            youtube_id=vid,
            defaults={
                "title": snippet["title"],
                "channel_title": snippet.get("channelTitle", ""),
                "thumbnail_url": snippet["thumbnails"]["high"]["url"],
                "language": snippet.get("defaultLanguage", "en"),
                "subject": subject,
                "difficulty": difficulty,
            },
        )
        videos.append(video)
    return videos



def recommend_videos_for_session(user, session):
    from .models import RecommendedVideo

    subject = session.subject
    weak_topic = determine_weak_topic(user, subject) if subject.kind == "math" else None
    
    # Til bo'yicha aqlli query
    lang = session.user.ui_language or "en"
    yt_lang = "uz" if lang == "uz" else lang  # yoki "en" ga fallback
    
    if weak_topic:
        query = f"{weak_topic} darslik"
    else:
        query = f"{subject.name} tutorial"  # ui_language ni queryga qo'shma

    logger.info(f"YouTube search: query={query!r}, lang={yt_lang}, user={user.id}")

    try:
        items = search_youtube(query, language=yt_lang)
        logger.info(f"YouTube returned {len(items)} items")
        videos = upsert_videos_from_search(items, subject=subject)
    except Exception as e:
        logger.exception(f"YouTube recommendation failed: {e}")
        videos = []