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
        import html as _html
        video, _ = YoutubeVideo.objects.update_or_create(
            youtube_id=vid,
            defaults={
                "title": _html.unescape(snippet["title"])[:255],
                "channel_title": _html.unescape(snippet.get("channelTitle", ""))[:150],
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

# ---------------------------------------------------------------------------
# Erkin qidiruv (Video bo'limidagi qidiruv maydoni uchun)
# ---------------------------------------------------------------------------
import re as _re

YOUTUBE_VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"
SEARCH_CACHE_SECONDS = 6 * 3600


class YoutubeSearchError(Exception):
    def __init__(self, message, code="error"):
        super().__init__(message)
        self.code = code


def parse_duration(iso):
    """'PT1H2M10S' -> 3730 soniya."""
    m = _re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def youtube_search(query, max_results=12, duration=None, language="en"):
    """YouTube'dan qidiradi va natijani YoutubeVideo jadvaliga saqlaydi. Natija 6 soat keshlanadi.

    duration: None | "short" (<4 daq) | "medium" (4-20) | "long" (>20)
    """
    import requests
    from django.core.cache import cache

    if not settings.YOUTUBE_API_KEY:
        raise YoutubeSearchError("YouTube API kaliti sozlanmagan", code="no_key")

    import hashlib
    key = "yt-search:" + hashlib.md5(f"{language}|{duration}|{max_results}|{query.strip().lower()}".encode()).hexdigest()
    cached = cache.get(key)
    if cached is not None:
        return cached

    params = {
        "part": "snippet", "q": query, "type": "video", "maxResults": max_results,
        "safeSearch": "strict", "videoEmbeddable": "true", "relevanceLanguage": language,
        "key": settings.YOUTUBE_API_KEY,
    }
    if duration in ("short", "medium", "long"):
        params["videoDuration"] = duration
    try:
        resp = requests.get(YOUTUBE_SEARCH_ENDPOINT, params=params, timeout=8)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        raise YoutubeSearchError("YouTube bilan aloqa yo'q", code="network") from e
    if resp.status_code == 403:
        raise YoutubeSearchError("YouTube kunlik so'rov limiti tugadi yoki kalit noto'g'ri", code="quota")
    if resp.status_code != 200:
        raise YoutubeSearchError(f"YouTube xatosi ({resp.status_code})", code="error")

    items = [it for it in resp.json().get("items", []) if it.get("id", {}).get("videoId")]
    ids = [it["id"]["videoId"] for it in items]
    details = {}
    if ids:
        try:
            dr = requests.get(YOUTUBE_VIDEOS_ENDPOINT, params={
                "part": "contentDetails,statistics", "id": ",".join(ids), "key": settings.YOUTUBE_API_KEY,
            }, timeout=8)
            if dr.status_code == 200:
                details = {d["id"]: d for d in dr.json().get("items", [])}
        except requests.exceptions.RequestException:
            pass

    from .models import YoutubeVideo
    import html
    results = []
    for it in items:
        vid = it["id"]["videoId"]
        sn = it["snippet"]
        thumbs = sn.get("thumbnails", {})
        thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
        d = details.get(vid, {})
        defaults = {
            "title": html.unescape(sn.get("title", ""))[:255],
            "channel_title": html.unescape(sn.get("channelTitle", ""))[:150],
            "thumbnail_url": thumb,
            "duration_seconds": parse_duration(d.get("contentDetails", {}).get("duration")),
            "language": (sn.get("defaultAudioLanguage") or language or "en")[:8],
        }
        try:
            defaults["view_count"] = min(int(d.get("statistics", {}).get("viewCount", 0)), 2_147_483_647)
        except (TypeError, ValueError):
            pass
        video, _ = YoutubeVideo.objects.update_or_create(youtube_id=vid, defaults=defaults)
        results.append(video)

    from .serializers import YoutubeVideoSerializer
    data = YoutubeVideoSerializer(results, many=True).data
    data = [dict(row, published_at=items[i]["snippet"].get("publishedAt")) for i, row in enumerate(data)]
    cache.set(key, data, SEARCH_CACHE_SECONDS)
    return data


def search_suggestions(user):
    """O'quvchi darajasi va zaif mavzulariga qarab tayyor qidiruv so'rovlari."""
    from apps.ai_teacher.models import AssessmentResult
    from apps.subjects.models import UserSubjectLevel

    row = UserSubjectLevel.objects.filter(user=user, subject__code="english").select_related("current_level").first()
    level = row.current_level.code if row and row.current_level else None
    out = []
    for r in AssessmentResult.objects.filter(user=user).exclude(kind="speaking").order_by("-created_at")[:5]:
        for t in r.weak_topics[:2]:
            q = f"{t} English grammar explained"
            if q not in out:
                out.append(q)
    base = {
        None: ["English for beginners", "Present Simple explained", "English listening practice"],
        "A1": ["English for beginners A1", "Present Simple explained", "Basic English conversation"],
        "A2": ["Past Simple explained", "English listening practice A2", "Everyday English phrases"],
        "B1": ["Present Perfect explained", "English listening B1", "IELTS speaking part 1"],
        "B2": ["Conditionals in English", "IELTS writing task 2", "Advanced English vocabulary"],
        "C1": ["Advanced English idioms", "IELTS band 8 speaking", "English phrasal verbs advanced"],
        "C2": ["English debate practice", "Academic English vocabulary", "IELTS band 9 essay"],
    }.get(level, [])
    for q in base:
        if q not in out:
            out.append(q)
    return {"level": level, "queries": out[:6]}
