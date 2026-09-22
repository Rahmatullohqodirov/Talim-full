from django.contrib import admin
from .models import YoutubeVideo, RecommendedVideo, SavedVideo, WatchHistory, VideoRating

admin.site.register(YoutubeVideo)
admin.site.register(RecommendedVideo)
admin.site.register(SavedVideo)
admin.site.register(WatchHistory)
admin.site.register(VideoRating)
