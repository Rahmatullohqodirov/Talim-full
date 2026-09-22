from django.db import models
from common.models import BaseModel


class PaymentTransaction(BaseModel):
    """Payme / Click orqali to'lov tranzaksiyalari."""
    class Provider(models.TextChoices):
        PAYME = "payme", "Payme"
        CLICK = "click", "Click"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="payment_transactions")
    plan = models.ForeignKey("accounts.SubscriptionPlan", on_delete=models.PROTECT, related_name="transactions")
    provider = models.CharField(max_length=10, choices=Provider.choices)
    provider_transaction_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    amount_uzs = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    # Payme JSON-RPC holati: 1=created, 2=performed, -1=cancelled(created), -2=cancelled(performed)
    payme_state = models.SmallIntegerField(null=True, blank=True)
    payme_create_time_ms = models.BigIntegerField(null=True, blank=True)
    payme_perform_time_ms = models.BigIntegerField(null=True, blank=True)
    payme_cancel_time_ms = models.BigIntegerField(null=True, blank=True)
    payme_cancel_reason = models.SmallIntegerField(null=True, blank=True)
    # Click ikki bosqichli oqim: prepare -> merchant_prepare_id, keyin complete
    click_prepare_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status"])]

    def __str__(self):
        return f"{self.provider}:{self.provider_transaction_id or self.id}"


class Invoice(BaseModel):
    """Har muvaffaqiyatli tranzaksiya uchun chek/hisob-faktura."""
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name="invoice")
    invoice_number = models.CharField(max_length=32, unique=True)
    pdf_url = models.URLField(blank=True)
