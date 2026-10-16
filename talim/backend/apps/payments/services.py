"""Payme / Click integratsiyasi uchun servis qatlami.

Har provayder o'z webhook formatiga ega; bu yerda umumiy interfeys beriladi.
Haqiqiy shartnoma va imzo tekshiruvi (merchant key bilan HMAC) prod muhitda qo'shiladi.
"""
from django.conf import settings
from django.utils import timezone


def create_pending_transaction(user, plan, provider):
    from .models import PaymentTransaction
    return PaymentTransaction.objects.create(
        user=user, plan=plan, provider=provider, amount_uzs=plan.price_usd * settings.USD_TO_UZS_RATE,
    )


def mark_transaction_success(transaction, provider_transaction_id):
    """To'lovni muvaffaqiyatli deb belgilaydi va obunani uzaytiradi (amaldagi muddat ustiga qo'shiladi)."""
    from apps.accounts.models import UserSubscription

    if transaction.status == transaction.Status.SUCCESS:
        return transaction  # takroriy webhook — ikki marta uzaytirmaymiz
    transaction.provider_transaction_id = provider_transaction_id
    transaction.status = transaction.Status.SUCCESS
    transaction.paid_at = timezone.now()
    transaction.save()

    now = timezone.now()
    days = getattr(transaction.plan, "duration_days", 30) or 30
    sub = UserSubscription.objects.filter(user=transaction.user).first()
    start = sub.expires_at if sub and sub.expires_at and sub.expires_at > now else now
    UserSubscription.objects.update_or_create(
        user=transaction.user,
        defaults={"plan": transaction.plan, "expires_at": start + timezone.timedelta(days=days)},
    )
    transaction.user.is_premium = True
    transaction.user.save(update_fields=["is_premium"])
    return transaction


def revoke_for_transaction(transaction):
    """Bajarilgan to'lov bekor qilinsa (refund), shu to'lov bergan muddat olib tashlanadi."""
    from apps.accounts.models import UserSubscription

    sub = UserSubscription.objects.filter(user=transaction.user).first()
    if sub and sub.expires_at:
        sub.expires_at -= timezone.timedelta(days=getattr(transaction.plan, "duration_days", 30) or 30)
        sub.save(update_fields=["expires_at"])
    refresh_premium(transaction.user)


def refresh_premium(user):
    """Obuna muddati tugagan bo'lsa is_premium ni o'chiradi. Qaytaradi: obuna (yoki None)."""
    from apps.accounts.models import UserSubscription

    sub = UserSubscription.objects.filter(user=user).select_related("plan").first()
    if sub is None:
        return None  # obuna yozuvi yo'q: admin qo'lda bergan Premium'ga tegmaymiz
    active = sub.expires_at is None or sub.expires_at > timezone.now()
    if user.is_premium != active:
        user.is_premium = active
        user.save(update_fields=["is_premium"])
    return sub


def build_payme_checkout_url(transaction):
    """Payme merchant checkout linkini quradi (base64 params).
    Payme'ning haqiqiy webhook chaqiruvi /payments/payme/webhook/ manziliga keladi — buni
    Payme Business kabinetida "Callback URL" sifatida ko'rsatish kerak."""
    import base64
    back = f"{settings.FRONTEND_URL}/app/billing?paid={transaction.id}"
    params = (f"m={settings.PAYME_MERCHANT_ID};ac.transaction_id={transaction.id};"
              f"a={int(transaction.amount_uzs * 100)};c={back}")
    encoded = base64.b64encode(params.encode()).decode()
    return f"https://checkout.paycom.uz/{encoded}"


def build_click_checkout_url(transaction):
    """Click checkout havolasi. Click Merchant kabinetida Prepare/Complete URL'lari
    /payments/click/prepare/ va /payments/click/complete/ manzillariga ko'rsatilishi kerak."""
    return (
        f"https://my.click.uz/services/pay?service_id={settings.CLICK_SERVICE_ID}"
        f"&merchant_id={settings.CLICK_MERCHANT_ID}&amount={transaction.amount_uzs}"
        f"&transaction_param={transaction.id}"
        f"&return_url={settings.FRONTEND_URL}/app/billing?paid={transaction.id}"
    )
