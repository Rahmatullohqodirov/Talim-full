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
    from apps.accounts.models import UserSubscription
    transaction.provider_transaction_id = provider_transaction_id
    transaction.status = transaction.Status.SUCCESS
    transaction.paid_at = timezone.now()
    transaction.save()

    UserSubscription.objects.update_or_create(
        user=transaction.user,
        defaults={"plan": transaction.plan, "expires_at": timezone.now() + timezone.timedelta(days=30)},
    )
    transaction.user.is_premium = True
    transaction.user.save(update_fields=["is_premium"])
    return transaction


def build_payme_checkout_url(transaction):
    """Payme merchant checkout linkini quradi (base64 params).
    Payme'ning haqiqiy webhook chaqiruvi /payments/payme/webhook/ manziliga keladi — buni
    Payme Business kabinetida "Callback URL" sifatida ko'rsatish kerak."""
    import base64
    params = f"m={settings.PAYME_MERCHANT_ID};ac.transaction_id={transaction.id};a={int(transaction.amount_uzs * 100)}"
    encoded = base64.b64encode(params.encode()).decode()
    return f"https://checkout.paycom.uz/{encoded}"


def build_click_checkout_url(transaction):
    """Click checkout havolasi. Click Merchant kabinetida Prepare/Complete URL'lari
    /payments/click/prepare/ va /payments/click/complete/ manzillariga ko'rsatilishi kerak."""
    return (
        f"https://my.click.uz/services/pay?service_id={settings.CLICK_SERVICE_ID}"
        f"&merchant_id={settings.CLICK_MERCHANT_ID}&amount={transaction.amount_uzs}"
        f"&transaction_param={transaction.id}"
    )
