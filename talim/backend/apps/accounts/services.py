"""Accounts xizmatlari: email tasdiqlash kodi va Google/Facebook orqali kirish.

Google/Facebook orqali kirish ishlashi uchun quyidagilar SIZDAN talab qilinadi (men bu yerdan
sizning o'rningizga ro'yxatdan o'ta olmayman):
  1. Google: https://console.cloud.google.com -> OAuth consent screen + Web Client ID yarating,
     uni frontend/.env ga VITE_GOOGLE_CLIENT_ID sifatida, backend/.env ga GOOGLE_CLIENT_ID
     sifatida qo'ying.
  2. Facebook: https://developers.facebook.com -> yangi ilova yarating, App ID'ni
     frontend/.env ga VITE_FACEBOOK_APP_ID, App Secret'ni backend/.env ga
     FACEBOOK_APP_SECRET sifatida qo'ying.
Kalitlar qo'yilmaguncha bu tugmalar "Google/Facebook hali sozlanmagan" xabarini chiqaradi —
lekin ilovaning qolgan qismini buzmaydi.
"""
import random

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


def generate_and_send_verification_code(user) -> None:
    """6 xonali tasodifiy kod yaratadi, User'ga saqlaydi va pochtaga yuboradi.

    EMAIL_HOST sozlanmagan bo'lsa (dev muhit), kod Django konsoliga (server logiga)
    chiqariladi — shu orqali ham ro'yxatdan o'tishni sinab ko'rish mumkin.
    """
    code = f"{random.randint(0, 999999):06d}"
    user.email_verification_code = code
    user.email_verification_sent_at = timezone.now()
    user.save(update_fields=["email_verification_code", "email_verification_sent_at"])

    send_mail(
        subject="Talim — emailingizni tasdiqlang",
        message=(
            f"Assalomu alaykum, {user.username}!\n\n"
            f"Ro'yxatdan o'tishni yakunlash uchun ushbu kodni kiriting: {code}\n\n"
            "Kod 30 daqiqa amal qiladi. Agar bu so'rovni siz yubormagan bo'lsangiz, xabarni e'tiborsiz qoldiring."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,  # SMTP sozlanmagan bo'lsa ham ro'yxatdan o'tish jarayoni to'xtab qolmasin
    )


def verify_code(user, code: str) -> tuple[bool, str]:
    """Kodni tekshiradi. Muvaffaqiyatli bo'lsa hisobni faollashtiradi."""
    if not user.email_verification_code:
        return False, "Avval tasdiqlash kodi so'ralmagan."
    if user.email_verified:
        return True, "Email allaqachon tasdiqlangan."
    if user.email_verification_sent_at and (timezone.now() - user.email_verification_sent_at).total_seconds() > 1800:
        return False, "Kod muddati tugagan. Yangi kod so'rang."
    if code != user.email_verification_code:
        return False, "Kod noto'g'ri."

    user.email_verified = True
    user.is_active = True
    user.email_verification_code = ""
    user.save(update_fields=["email_verified", "is_active", "email_verification_code"])
    return True, "Email tasdiqlandi."


def verify_google_id_token(id_token: str) -> dict | None:
    """Google ID tokenini tekshiradi va {email, name} qaytaradi (yoki None agar noto'g'ri bo'lsa).

    Google'ning o'z 'tokeninfo' endpointidan foydalanadi — alohida Google kutubxonasi shart emas.
    """
    import requests

    if not settings.GOOGLE_CLIENT_ID:
        return None
    try:
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token}, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.exceptions.RequestException, ValueError):
        return None

    if data.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        return None
    if data.get("aud") != settings.GOOGLE_CLIENT_ID:
        return None  # boshqa ilova uchun chiqarilgan token — xavfsizlik uchun rad etamiz
    if not data.get("email_verified") in (True, "true"):
        return None
    return {"email": data.get("email"), "name": data.get("name", ""),
            "first_name": data.get("given_name", ""), "last_name": data.get("family_name", "")}


def verify_facebook_access_token(access_token: str) -> dict | None:
    """Facebook access tokenini tekshiradi va {email, name} qaytaradi."""
    import requests

    if not settings.FACEBOOK_APP_ID or not settings.FACEBOOK_APP_SECRET:
        return None
    try:
        app_token = f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
        debug = requests.get(
            "https://graph.facebook.com/debug_token",
            params={"input_token": access_token, "access_token": app_token},
            timeout=10,
        ).json()
        data = debug.get("data", {})
        # Token aynan bizning ilovamiz uchun berilganini tekshiramiz (boshqa ilova tokeni bilan kirib bo'lmasin)
        if not data.get("is_valid") or str(data.get("app_id")) != str(settings.FACEBOOK_APP_ID):
            return None
        profile = requests.get(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email", "access_token": access_token},
            timeout=10,
        ).json()
    except (requests.exceptions.RequestException, ValueError):
        return None

    if not profile.get("email"):
        return None
    return {"email": profile["email"], "name": profile.get("name", "")}


def unique_username(base: str) -> str:
    """Email yoki ismdan bo'sh bo'lmagan, band qilinmagan username yasaydi."""
    import re
    from django.contrib.auth import get_user_model

    User = get_user_model()
    base = re.sub(r"[^a-zA-Z0-9_.]", "", base.split("@")[0])[:24] or "user"
    candidate, n = base, 1
    while User.objects.filter(username__iexact=candidate).exists():
        n += 1
        candidate = f"{base}{n}"
    return candidate
