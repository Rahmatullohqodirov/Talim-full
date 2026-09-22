from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PaymentTransaction
from .serializers import (
    PaymentTransactionSerializer, AdminPaymentTransactionSerializer, AdminPaymentTransactionUpdateSerializer,
)
from .services import (
    create_pending_transaction, mark_transaction_success,
    build_payme_checkout_url, build_click_checkout_url,
)

class PaymentTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head"]
    throttle_scope = "payment"  # bitta foydalanuvchi to'lov endpointini spam qilmasligi uchun

    def get_queryset(self):
        return PaymentTransaction.objects.filter(user=self.request.user).select_related("plan")

    def create(self, request, *args, **kwargs):
        """POST /payments/transactions/  {plan: id, provider: 'payme'|'click'} -> checkout_url"""
        from django.conf import settings
        from apps.accounts.models import SubscriptionPlan
        try:
            plan = SubscriptionPlan.objects.get(id=request.data.get("plan"))
        except (SubscriptionPlan.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Ko'rsatilgan reja (plan) topilmadi. Avval SubscriptionPlan yaratilganini tekshiring."}, status=status.HTTP_400_BAD_REQUEST)
        provider = request.data["provider"]
        txn = create_pending_transaction(request.user, plan, provider)

        merchant_configured = (
            settings.PAYME_MERCHANT_ID if provider == "payme" else settings.CLICK_MERCHANT_ID
        )
        if not merchant_configured:
            # Haqiqiy Payme/Click merchant ID sozlanmagan — demo rejim: to'lovni darhol muvaffaqiyatli deb belgilaymiz.
            mark_transaction_success(txn, provider_transaction_id="mock-demo")
            return Response(
                {**PaymentTransactionSerializer(txn).data, "checkout_url": None, "mock": True},
                status=status.HTTP_201_CREATED,
            )

        checkout_url = build_payme_checkout_url(txn) if provider == "payme" else build_click_checkout_url(txn)
        return Response({**PaymentTransactionSerializer(txn).data, "checkout_url": checkout_url, "mock": False}, status=status.HTTP_201_CREATED)


class AdminPaymentTransactionViewSet(viewsets.ModelViewSet):
    """GET/PATCH/DELETE /payments/admin/transactions/ — admin uchun tranzaksiyalarni boshqarish.

    PATCH — holatni qo'lda o'zgartirish (masalan pending -> success, refund uchun -> cancelled).
    DELETE — faqat pending/failed/cancelled yozuvlarni o'chirish mumkin; success tranzaksiya
    moliyaviy tarix sifatida saqlanadi va o'chirilmaydi.
    """
    queryset = PaymentTransaction.objects.select_related("user", "plan").order_by("-created_at")
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "patch", "delete", "head"]
    filterset_fields = ["status", "provider"]

    def get_serializer_class(self):
        return AdminPaymentTransactionUpdateSerializer if self.request.method == "PATCH" else AdminPaymentTransactionSerializer

    def partial_update(self, request, *args, **kwargs):
        txn = self.get_object()
        serializer = AdminPaymentTransactionUpdateSerializer(txn, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminPaymentTransactionSerializer(txn).data)

    def destroy(self, request, *args, **kwargs):
        txn = self.get_object()
        if txn.status == PaymentTransaction.Status.SUCCESS:
            return Response(
                {"detail": "Muvaffaqiyatli to'lovni o'chirib bo'lmaydi. Avval holatini o'zgartiring."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)
