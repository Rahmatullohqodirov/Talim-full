from celery import shared_task


@shared_task
def analyze_transcript_speech(transcript_id: str):
    from apps.session.models import Transcript
    from .services import run_speech_analysis

    transcript = Transcript.objects.get(id=transcript_id)
    analysis = run_speech_analysis(transcript)
    transcript.pronunciation_score = analysis.pronunciation_score
    transcript.grammar_score = transcript.grammar_score  # grammar alohida NLP orqali baholanadi
    transcript.save(update_fields=["pronunciation_score"])
