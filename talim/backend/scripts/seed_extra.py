"""ai_teacher, avatars, gamification, accounts modellariga qo'shimcha real ma'lumot.
python manage.py shell -c "exec(open('scripts/seed_extra.py', encoding='utf-8').read())"
"""
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import SubscriptionPlan
from apps.avatars.models import Avatar
from apps.gamification.models import LeaderboardEntry
from apps.ai_teacher.models import GeneratedLesson, AIChatThread, AIChatMessage
from apps.subjects.models import Subject, CEFRLevel

User = get_user_model()


def seed_plans():
    plans = [
        {"name": "Free", "price_usd": 0, "voice_cloning_enabled": False, "max_sessions_per_day": 3},
        {"name": "Premium", "price_usd": 9.99, "voice_cloning_enabled": True, "max_sessions_per_day": None},
    ]
    for data in plans:
        plan, created = SubscriptionPlan.objects.get_or_create(name=data["name"], defaults=data)
        if created:
            print(f"SubscriptionPlan: {plan.name}")


def seed_avatars():
    avatars = [
        {"name": "Emma", "gender": "female", "voice_model_id": "emma-en-us", "lip_sync_model": "musetalk", "is_premium_only": False},
        {"name": "Alex", "gender": "male", "voice_model_id": "alex-en-gb", "lip_sync_model": "musetalk", "is_premium_only": False},
        {"name": "Sofia", "gender": "female", "voice_model_id": "sofia-en-us-premium", "lip_sync_model": "musetalk", "is_premium_only": True},
        {"name": "Daniel", "gender": "male", "voice_model_id": "daniel-en-au-premium", "lip_sync_model": "musetalk", "is_premium_only": True},
    ]
    for data in avatars:
        avatar, created = Avatar.objects.get_or_create(name=data["name"], defaults=data)
        if created:
            print(f"Avatar: {avatar.name}")


def seed_leaderboard():
    english = Subject.objects.filter(code="english").first()
    users_data = [
        ("aziza_karimova", "aziza@example.com", 480),
        ("javlon_tosh", "javlon@example.com", 410),
        ("dilnoza_yusupova", "dilnoza@example.com", 365),
        ("sardor_alimov", "sardor@example.com", 290),
        ("nodira_rashidova", "nodira@example.com", 210),
    ]
    week_start = timezone.now().date() - timezone.timedelta(days=timezone.now().weekday())
    for rank, (username, email, points) in enumerate(users_data, start=1):
        user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
        LeaderboardEntry.objects.update_or_create(
            user=user, scope=LeaderboardEntry.Scope.GLOBAL_ANON, week_start=week_start,
            defaults={"total_points": points, "rank": rank},
        )
        print(f"LeaderboardEntry: {username} — {points} ball, {rank}-o'rin")


def seed_ai_teacher():
    english = Subject.objects.filter(code="english").first()
    b1 = CEFRLevel.objects.filter(subject=english, code="B1").first() if english else None
    demo_user, _ = User.objects.get_or_create(username="demo_student", defaults={"email": "demo_student@supertutor.ai"})

    if english:
        lesson, created = GeneratedLesson.objects.get_or_create(
            user=demo_user, subject=english, title="Present Perfect: hayotiy tajriba haqida gapirish",
            defaults={
                "cefr_level": b1,
                "objective": "O'quvchi Present Perfect zamonidan hayotiy tajribalarni tasvirlashda foydalana oladi.",
                "content_blocks": [
                    {"type": "grammar", "data": {"rule": "have/has + V3", "example": "I have visited Samarqand twice."}},
                    {"type": "vocab", "data": {"words": ["experience", "achievement", "journey", "opportunity"]}},
                    {"type": "exercise", "data": {"prompt": "Complete: She ___ (never/try) sushi before.", "answer": "has never tried"}},
                ],
                "generated_by_model": "groq-llama-3.3-70b",
            },
        )
        if created:
            print(f"GeneratedLesson: {lesson.title}")

    thread, created = AIChatThread.objects.get_or_create(
        user=demo_user, subject=english, defaults={"title": "Ingliz tili bo'yicha savollar"},
    )
    if created:
        AIChatMessage.objects.create(thread=thread, role=AIChatMessage.Role.USER,
                                      content="Present Perfect va Past Simple farqi nimada?")
        AIChatMessage.objects.create(
            thread=thread, role=AIChatMessage.Role.ASSISTANT,
            content="Past Simple aniq o'tgan vaqtda tugagan harakat uchun (masalan: 'I visited Samarkand in 2022'), "
                    "Present Perfect esa vaqt aniq ko'rsatilmagan, hozirgi vaqtga bog'liq tajriba/natija uchun "
                    "ishlatiladi (masalan: 'I have visited Samarkand'). Savolingiz bo'lsa davom eting!",
        )
        print(f"AIChatThread: {thread.title}")


seed_plans()
seed_avatars()
seed_leaderboard()
seed_ai_teacher()
print("accounts/avatars/gamification/ai_teacher uchun real ma'lumot qo'shildi.")
