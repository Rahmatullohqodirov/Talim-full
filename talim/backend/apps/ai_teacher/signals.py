from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.session.models import Transcript


@receiver(post_save, sender=Transcript)
def run_speech_analysis_on_transcript(sender, instance, created, **kwargs):
    """Foydalanuvchi repliкasi yozilganda STT + talaffuz/aksent tahlilini ishga tushiradi."""
    if created and instance.speaker == Transcript.Speaker.USER and instance.audio_url:
        from .tasks import analyze_transcript_speech
        analyze_transcript_speech.delay(str(instance.id))
