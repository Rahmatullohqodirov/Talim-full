"""Standalone seed script — Django shell orqali ishga tushiriladi:
python manage.py shell -c "exec(open('scripts/seed_data.py', encoding='utf-8').read())"
"""
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.subjects.models import Subject, CEFRLevel
from apps.avatars.models import Avatar
from apps.accounts.models import SubscriptionPlan
from apps.math_practice.models import MathTopic, MathProblem, MathAttempt
from apps.practice_tools.models import Quiz, QuizQuestion, QuizAttempt, Flashcard, FlashcardReview
from apps.gamification.models import LeaderboardEntry
from apps.payments.models import PaymentTransaction
from apps.session.models import LearningSession
from apps.learning_path.models import LearningPath, LearningPathItem

User = get_user_model()


def seed_subjects():
    subjects_data = [
        {"code": "english", "name": "Ingliz tili", "kind": Subject.Kind.LANGUAGE, "is_active_in_mvp": True},
        {"code": "math", "name": "Matematika", "kind": Subject.Kind.MATH, "is_active_in_mvp": True},
        {"code": "russian", "name": "Rus tili", "kind": Subject.Kind.LANGUAGE, "is_active_in_mvp": False},
        {"code": "german", "name": "Nemis tili", "kind": Subject.Kind.LANGUAGE, "is_active_in_mvp": False},
        {"code": "turkish", "name": "Turk tili", "kind": Subject.Kind.LANGUAGE, "is_active_in_mvp": False},
    ]
    for data in subjects_data:
        subject, created = Subject.objects.get_or_create(code=data["code"], defaults=data)
        if created:
            print(f"Subject: {subject.name}")
        if subject.kind == Subject.Kind.LANGUAGE:
            for i, level in enumerate(["A1", "A2", "B1", "B2", "C1", "C2"], start=1):
                CEFRLevel.objects.get_or_create(subject=subject, code=level, defaults={"order": i})


def seed_avatars():
    avatars_data = [
        {"name": "Emma", "gender": "female", "voice_model_id": "emma-default", "is_premium_only": False},
        {"name": "Alex", "gender": "male", "voice_model_id": "alex-default", "is_premium_only": False},
        {"name": "Sofia", "gender": "female", "voice_model_id": "sofia-premium", "is_premium_only": True},
    ]
    for data in avatars_data:
        avatar, created = Avatar.objects.get_or_create(name=data["name"], defaults=data)
        if created:
            print(f"Avatar: {avatar.name}")


def seed_plans():
    plans_data = [
        {"name": "Free", "price_usd": 0, "voice_cloning_enabled": False, "max_sessions_per_day": 3},
        {"name": "Premium", "price_usd": 9.99, "voice_cloning_enabled": True, "max_sessions_per_day": None},
    ]
    for data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(name=data["name"], defaults=data)
        if created:
            print(f"Plan: {plan.name}")


def seed_math():
    topics_data = ["Algebra", "Geometriya", "Funksiyalar", "Tenglamalar"]
    topics = {}
    for name in topics_data:
        topic, created = MathTopic.objects.get_or_create(name=name)
        topics[name] = topic
        if created:
            print(f"MathTopic: {topic.name}")

    problems_data = [
        {"topic": "Algebra", "statement": "2x + 5 = 15. x ni toping.", "difficulty": MathProblem.Difficulty.EASY,
         "solution_steps": ["2x = 10", "x = 5"]},
        {"topic": "Geometriya", "statement": "Tomoni 4 sm bo'lgan kvadratning yuzini toping.",
         "difficulty": MathProblem.Difficulty.EASY, "solution_steps": ["S = a^2 = 16 sm^2"]},
        {"topic": "Funksiyalar", "statement": "f(x) = x^2 - 4. f(3) ni toping.",
         "difficulty": MathProblem.Difficulty.MEDIUM, "solution_steps": ["f(3) = 9 - 4 = 5"]},
        {"topic": "Tenglamalar", "statement": "x^2 - 5x + 6 = 0 tenglamani yeching.",
         "difficulty": MathProblem.Difficulty.HARD, "solution_steps": ["(x-2)(x-3) = 0", "x = 2 yoki x = 3"]},
    ]
    for data in problems_data:
        topic = topics[data["topic"]]
        MathProblem.objects.get_or_create(
            topic=topic, statement=data["statement"],
            defaults={"difficulty": data["difficulty"], "solution_steps": data["solution_steps"]},
        )


def seed_practice_tools():
    english = Subject.objects.filter(code="english").first()
    if not english:
        return
    quiz, created = Quiz.objects.get_or_create(subject=english, title="Present Simple asoslari")
    if created:
        QuizQuestion.objects.create(
            quiz=quiz, text="She ___ to school every day.",
            choices=["go", "goes", "going", "went"], correct_index=1,
        )
        QuizQuestion.objects.create(
            quiz=quiz, text="They ___ football on weekends.",
            choices=["plays", "playing", "play", "played"], correct_index=2,
        )

    flashcards_data = [
        {"front_text": "Hello", "back_text": "Salom"},
        {"front_text": "Thank you", "back_text": "Rahmat"},
        {"front_text": "Goodbye", "back_text": "Xayr"},
    ]
    for data in flashcards_data:
        Flashcard.objects.get_or_create(subject=english, front_text=data["front_text"], defaults=data)


def seed_demo_user():
    user, created = User.objects.get_or_create(
        username="demo_student",
        defaults={"email": "demo_student@supertutor.ai", "is_premium": False},
    )
    if created:
        user.set_password("demo12345")
        user.save()
        print(f"User: {user.username} (parol: demo12345)")
    return user


def seed_user_dependent(user):
    english = Subject.objects.filter(code="english").first()
    avatar = Avatar.objects.filter(name="Emma").first()

    session, created = LearningSession.objects.get_or_create(
        user=user, subject=english, avatar=avatar,
        defaults={"status": LearningSession.Status.COMPLETED, "ended_at": timezone.now(),
                  "duration_seconds": 1200},
    )
    if created:
        print("LearningSession: demo sessiya yaratildi")

    problem = MathProblem.objects.first()
    if problem:
        MathAttempt.objects.get_or_create(
            user=user, problem=problem,
            defaults={"is_correct": True, "user_answer": "x = 5", "time_spent_seconds": 45},
        )

    quiz = Quiz.objects.first()
    if quiz:
        QuizAttempt.objects.get_or_create(user=user, quiz=quiz, defaults={"score_percent": 100.0})

    flashcard = Flashcard.objects.first()
    if flashcard:
        FlashcardReview.objects.get_or_create(
            user=user, flashcard=flashcard,
            defaults={"ease_factor": 2.5, "interval_days": 1, "repetitions": 1,
                      "next_review_at": timezone.now() + timedelta(days=1)},
        )

    LeaderboardEntry.objects.get_or_create(
        user=user, scope=LeaderboardEntry.Scope.GLOBAL_ANON, week_start=timezone.now().date(),
        defaults={"total_points": 120, "rank": 1},
    )

    plan = SubscriptionPlan.objects.filter(name="Free").first()
    if plan:
        PaymentTransaction.objects.get_or_create(
            user=user, plan=plan,
            defaults={"provider": PaymentTransaction.Provider.PAYME, "amount_uzs": 0,
                      "status": PaymentTransaction.Status.SUCCESS, "paid_at": timezone.now()},
        )

    if english:
        path, created = LearningPath.objects.get_or_create(user=user, subject=english, defaults={"is_active": True})
        if created:
            LearningPathItem.objects.create(path=path, order=1, status=LearningPathItem.Status.DONE)
            LearningPathItem.objects.create(path=path, order=2, status=LearningPathItem.Status.IN_PROGRESS)


seed_subjects()
seed_avatars()
seed_plans()
seed_math()
seed_practice_tools()
_demo_user = seed_demo_user()
seed_user_dependent(_demo_user)
print("Barcha modellarga seed data muvaffaqiyatli qo'shildi.")
