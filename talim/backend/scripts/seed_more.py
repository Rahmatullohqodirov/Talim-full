"""learning_path, math_practice, payments, practice_tools, session, statistics, subjects, youtube_recommendations uchun real ma'lumot.
python manage.py shell -c "exec(open('scripts/seed_more.py', encoding='utf-8').read())"
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.subjects.models import Subject, CEFRLevel
from apps.avatars.models import Avatar
from apps.accounts.models import SubscriptionPlan
from apps.math_practice.models import MathTopic, MathProblem, MathAttempt
from apps.practice_tools.models import Quiz, QuizQuestion, QuizAttempt, Flashcard, FlashcardReview
from apps.payments.models import PaymentTransaction, Invoice
from apps.session.models import LearningSession, Transcript, VoiceCloningRequest
from apps.statistics.models import SubjectStats, DailyActivity, WeeklyReport
from apps.learning_path.models import LearningPath, LearningPathItem
from apps.youtube_recommendations.models import YoutubeVideo, RecommendedVideo, SavedVideo, WatchHistory, VideoRating

User = get_user_model()


def get_or_create_subject(code, name, kind, active=False):
    subject, _ = Subject.objects.get_or_create(code=code, defaults={"name": name, "kind": kind, "is_active_in_mvp": active})
    return subject


def seed_subjects_and_levels():
    english = get_or_create_subject("english", "Ingliz tili", Subject.Kind.LANGUAGE, True)
    math = get_or_create_subject("math", "Matematika", Subject.Kind.MATH, True)
    get_or_create_subject("russian", "Rus tili", Subject.Kind.LANGUAGE, True)
    get_or_create_subject("german", "Nemis tili", Subject.Kind.LANGUAGE, True)
    get_or_create_subject("turkish", "Turk tili", Subject.Kind.LANGUAGE, True)
    for i, code in enumerate(["A1", "A2", "B1", "B2", "C1", "C2"], start=1):
        CEFRLevel.objects.get_or_create(subject=english, code=code, defaults={"order": i})
    print("Subjects va CEFR darajalari tayyor")
    return english, math


def seed_math(math_subject):
    algebra, _ = MathTopic.objects.get_or_create(name="Algebra")
    geometry, _ = MathTopic.objects.get_or_create(name="Geometriya")
    quad, _ = MathTopic.objects.get_or_create(name="Kvadrat tenglamalar", parent=algebra)

    problems = [
        {"topic": algebra, "statement": "3x - 7 = 14. x ni toping.", "difficulty": MathProblem.Difficulty.EASY,
         "solution_steps": ["3x = 21", "x = 7"]},
        {"topic": quad, "statement": "x^2 - 5x + 6 = 0 tenglamani yeching.", "difficulty": MathProblem.Difficulty.MEDIUM,
         "solution_steps": ["(x-2)(x-3) = 0", "x1 = 2, x2 = 3"]},
        {"topic": geometry, "statement": "Radiusi 7 sm bo'lgan doiraning yuzini toping (pi = 3.14).",
         "difficulty": MathProblem.Difficulty.MEDIUM, "solution_steps": ["S = pi*r^2 = 3.14*49 = 153.86 sm^2"]},
        {"topic": quad, "statement": "2x^2 - 8x = 0 tenglamani yeching.", "difficulty": MathProblem.Difficulty.HARD,
         "solution_steps": ["2x(x-4) = 0", "x1 = 0, x2 = 4"]},
    ]
    created_problems = []
    for data in problems:
        p, created = MathProblem.objects.get_or_create(
            topic=data["topic"], statement=data["statement"],
            defaults={"difficulty": data["difficulty"], "solution_steps": data["solution_steps"]},
        )
        created_problems.append(p)
    print(f"MathProblem: {len(created_problems)} ta masala tayyor")
    return created_problems


def seed_practice_tools(english):
    quiz, _ = Quiz.objects.get_or_create(subject=english, title="Present Perfect testi")
    if not quiz.questions.exists():
        QuizQuestion.objects.create(quiz=quiz, text="I ___ this movie before.",
                                     choices=["saw", "have seen", "see", "seeing"], correct_index=1)
        QuizQuestion.objects.create(quiz=quiz, text="___ you ever visited London?",
                                     choices=["Did", "Have", "Do", "Was"], correct_index=1)

    flashcards = [
        {"front_text": "achievement", "back_text": "yutuq"},
        {"front_text": "opportunity", "back_text": "imkoniyat"},
        {"front_text": "journey", "back_text": "sayohat"},
        {"front_text": "experience", "back_text": "tajriba"},
    ]
    for data in flashcards:
        Flashcard.objects.get_or_create(subject=english, front_text=data["front_text"], defaults=data)
    print("Quiz va Flashcard tayyor")
    return quiz


def seed_youtube(english):
    videos = [
        {"youtube_id": "dQw4w9WgXcQ_demo1", "title": "Present Perfect Tense Explained",
         "channel_title": "English with Lucy", "duration_seconds": 720, "difficulty": "intermediate",
         "avg_rating": 4.8, "view_count": 152000, "topic_tags": ["present perfect", "grammar"]},
        {"youtube_id": "dQw4w9WgXcQ_demo2", "title": "Kvadrat tenglamalarni yechish usullari",
         "channel_title": "Matematika Repetitor", "duration_seconds": 900, "difficulty": "beginner",
         "avg_rating": 4.6, "view_count": 87000, "topic_tags": ["kvadrat tenglama", "algebra"]},
        {"youtube_id": "dQw4w9WgXcQ_demo3", "title": "English Speaking Practice for Beginners",
         "channel_title": "Speak English With Vanessa", "duration_seconds": 600, "difficulty": "beginner",
         "avg_rating": 4.7, "view_count": 210000, "topic_tags": ["speaking", "pronunciation"]},
    ]
    created = []
    for data in videos:
        v, _ = YoutubeVideo.objects.get_or_create(youtube_id=data["youtube_id"], defaults={**data, "subject": english})
        created.append(v)
    print(f"YoutubeVideo: {len(created)} ta video tayyor")
    return created


def seed_user_flow(english, math, problems, quiz, videos):
    user, created = User.objects.get_or_create(username="demo_student", defaults={"email": "demo_student@supertutor.ai"})
    if created:
        user.set_password("demo12345")
        user.save()

    avatar = Avatar.objects.filter(name="Emma").first()
    plan = SubscriptionPlan.objects.filter(name="Free").first()

    session, created = LearningSession.objects.get_or_create(
        user=user, subject=english, avatar=avatar,
        defaults={"status": LearningSession.Status.COMPLETED, "ended_at": timezone.now(), "duration_seconds": 1140},
    )
    if created:
        Transcript.objects.create(session=session, speaker=Transcript.Speaker.USER,
                                   text="I have visited Samarkand last year.", pronunciation_score=78, grammar_score=65)
        Transcript.objects.create(session=session, speaker=Transcript.Speaker.AVATAR,
                                   text="Good try! Note: with a specific past time like 'last year', use Past Simple: 'I visited Samarkand last year.'")
    print("LearningSession + Transcript tayyor")

    if problems:
        MathAttempt.objects.get_or_create(
            user=user, problem=problems[0], session=session,
            defaults={"is_correct": True, "user_answer": "x = 7", "time_spent_seconds": 40},
        )
        MathAttempt.objects.get_or_create(
            user=user, problem=problems[1],
            defaults={"is_correct": False, "user_answer": "x = 1, x = 6", "time_spent_seconds": 95},
        )

    QuizAttempt.objects.get_or_create(user=user, quiz=quiz, defaults={"score_percent": 50.0})

    fc = Flashcard.objects.filter(subject=english).first()
    if fc:
        FlashcardReview.objects.get_or_create(
            user=user, flashcard=fc,
            defaults={"ease_factor": 2.3, "interval_days": 3, "repetitions": 2,
                      "next_review_at": timezone.now() + timedelta(days=3)},
        )

    if plan:
        txn, created = PaymentTransaction.objects.get_or_create(
            user=user, plan=plan,
            defaults={"provider": PaymentTransaction.Provider.PAYME, "amount_uzs": 0,
                      "status": PaymentTransaction.Status.SUCCESS, "paid_at": timezone.now()},
        )
        if created:
            Invoice.objects.get_or_create(transaction=txn, defaults={"invoice_number": f"INV-{txn.id.hex[:8].upper()}"})

    VoiceCloningRequest.objects.get_or_create(
        user=user, sample_audio_url="https://cdn.supertutor.ai/samples/demo_student_voice.mp3",
        defaults={"status": VoiceCloningRequest.Status.READY, "voice_model_id": "demo_student-clone-v1"},
    )

    SubjectStats.objects.update_or_create(
        user=user, subject=english,
        defaults={"total_minutes": 340, "sessions_completed": 12, "avg_session_minutes": 28.3,
                  "avg_pronunciation_score": 76.5, "avg_grammar_score": 68.2,
                  "current_streak_days": 5, "longest_streak_days": 9, "total_points": 480},
    )
    DailyActivity.objects.update_or_create(
        user=user, subject=english, date=timezone.now().date(),
        defaults={"minutes_spent": 25, "sessions_count": 1},
    )
    WeeklyReport.objects.update_or_create(
        user=user, week_start=timezone.now().date() - timedelta(days=timezone.now().weekday()),
        defaults={"total_minutes": 165, "growth_percent": 12.5, "weakest_topics": ["kvadrat tenglama", "past tense"]},
    )

    path, created = LearningPath.objects.get_or_create(user=user, subject=english, defaults={"is_active": True})
    if created:
        LearningPathItem.objects.create(path=path, order=1, status=LearningPathItem.Status.DONE)
        LearningPathItem.objects.create(path=path, order=2, status=LearningPathItem.Status.IN_PROGRESS)
        LearningPathItem.objects.create(path=path, order=3, status=LearningPathItem.Status.PENDING)

    if videos:
        RecommendedVideo.objects.get_or_create(
            user=user, video=videos[0], session=session,
            defaults={"reason": RecommendedVideo.Reason.POST_LESSON, "rank": 1},
        )
        SavedVideo.objects.get_or_create(user=user, video=videos[0])
        WatchHistory.objects.get_or_create(
            user=user, video=videos[0], defaults={"watched_seconds": 680, "completed": True},
        )
        VideoRating.objects.get_or_create(user=user, video=videos[0], defaults={"stars": 5})

    print("Foydalanuvchiga bog'liq barcha modellar to'ldirildi")


english, math = seed_subjects_and_levels()
problems = seed_math(math)
quiz = seed_practice_tools(english)
videos = seed_youtube(english)
seed_user_flow(english, math, problems, quiz, videos)
print("learning_path/math_practice/payments/practice_tools/session/statistics/subjects/youtube_recommendations uchun real ma'lumot qo'shildi.")
