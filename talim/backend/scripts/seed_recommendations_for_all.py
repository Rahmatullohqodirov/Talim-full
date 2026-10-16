"""Barcha mavjud foydalanuvchilarga YoutubeVideo asosida RecommendedVideo yaratadi.
python manage.py shell -c "exec(open('scripts/seed_recommendations_for_all.py', encoding='utf-8').read())"
"""
from django.contrib.auth import get_user_model
from apps.youtube_recommendations.models import YoutubeVideo, RecommendedVideo

User = get_user_model()

videos = list(YoutubeVideo.objects.all()[:3])
if not videos:
    print("YoutubeVideo topilmadi — avval seed_more.py ni ishga tushiring.")
else:
    count = 0
    for user in User.objects.all():
        for rank, video in enumerate(videos, start=1):
            _, created = RecommendedVideo.objects.get_or_create(
                user=user, video=video,
                defaults={"reason": RecommendedVideo.Reason.LEVEL_MATCH, "rank": rank},
            )
            if created:
                count += 1
    print(f"{count} ta RecommendedVideo yaratildi (barcha foydalanuvchilar uchun).")
