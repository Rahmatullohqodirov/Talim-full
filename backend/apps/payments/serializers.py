from rest_framework import serializers
from .models import PaymentTransaction, Invoice


class PaymentTransactionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = ["id", "plan", "plan_name", "provider", "amount_uzs", "status", "paid_at", "created_at"]
        read_only_fields = ["id", "amount_uzs", "status", "paid_at", "created_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ["invoice_number", "pdf_url"]


class AdminPaymentTransactionSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = ["id", "username", "plan_name", "provider", "amount_uzs", "status", "paid_at", "created_at"]


class AdminPaymentTransactionUpdateSerializer(serializers.ModelSerializer):
    """Admin panel orqali tranzaksiya holatini qo'lda o'zgartirish (masalan pending -> success)."""

    class Meta:
        model = PaymentTransaction
        fields = ["status"]
