"""Eski yozuvlardagi HTML belgilarni (&#39; &amp;) oddiy matnga aylantiradi."""
import html

from django.db import migrations


def forwards(apps, schema_editor):
    YoutubeVideo = apps.get_model("youtube_recommendations", "YoutubeVideo")
    for v in YoutubeVideo.objects.all():
        title, channel = html.unescape(v.title), html.unescape(v.channel_title)
        if title != v.title or channel != v.channel_title:
            v.title, v.channel_title = title[:255], channel[:150]
            v.save(update_fields=["title", "channel_title"])


class Migration(migrations.Migration):
    dependencies = [("youtube_recommendations", "0001_initial")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
