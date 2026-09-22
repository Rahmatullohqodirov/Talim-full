from rest_framework import serializers
from .models import YoutubeVideo, RecommendedVideo, SavedVideo, WatchHistory, VideoRating


class YoutubeVideoSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    embed_url = serializers.SerializerMethodField()

    class Meta:
        model = YoutubeVideo
        fields = [
            "id",
            "youtube_id",
            "embed_url",
            "title",
            "channel_title",
            "thumbnail_url",
            "duration_seconds",
            "language",
            "difficulty",
            "avg_rating",
            "view_count",
            "subject",
            "subject_name",
            "topic_tags",
        ]
        read_only_fields = ["avg_rating", "view_count", "embed_url"]

    def get_embed_url(self, obj):
        if not obj.youtube_id:
            return None

        return f"https://www.youtube.com/embed/{obj.youtube_id}"

class RecommendedVideoSerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer(read_only=True)

    class Meta:
        model = RecommendedVideo
        fields = ["id", "video", "reason", "rank", "was_clicked", "created_at"]


class SavedVideoSerializer(serializers.ModelSerializer):
    video = YoutubeVideoSerializer(read_only=True)
    video_id = serializers.PrimaryKeyRelatedField(queryset=YoutubeVideo.objects.all(), source="video", write_only=True)

    class Meta:
        model = SavedVideo
        fields = ["id", "video", "video_id", "created_at"]


class WatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchHistory
        fields = ["id", "video", "watched_seconds", "completed", "watched_at"]
        read_only_fields = ["id", "watched_at"]


class VideoRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoRating
        fields = ["id", "video", "stars"]
