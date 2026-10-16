"""Ro'yxatdan o'tishni email orqali tasdiqlash.

Token uchun alohida jadval kerak emas — Django'ning `signing` moduli orqali
imzolangan, muddati o'zida yozilgan token yaratamiz (statik, bazaga yozilmaydi).
"""
from django.conf import settings
from django.core import signing
from django.core.mail import send_mail

VERIFY_SALT = "accounts.email-verification"
VERIFY_MAX_AGE = 60 * 60 * 24 * 3  # 3 kun


def make_verification_token(user) -> str:
    return signing.dumps({"user_id": str(user.id), "email": user.email}, salt=VERIFY_SALT)


def verify_token(token: str, max_age: int = VERIFY_MAX_AGE) -> dict | None:
    try:
        return signing.loads(token, salt=VERIFY_SALT, max_age=max_age)
    except signing.BadSignature:
        return None


def send_verification_email(user) -> None:
    token = make_verification_token(user)
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Talim — emailingizni tasdiqlang"
    message = (
        f"Assalomu alaykum, {user.username or user.email}!\n\n"
        f"Ro'yxatdan o'tishni yakunlash uchun quyidagi havolani bosing "
        f"(havola 3 kun amal qiladi):\n\n{link}\n\n"
        f"Agar bu so'rovni siz yubormagan bo'lsangiz, bu xabarni e'tiborsiz qoldiring."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
