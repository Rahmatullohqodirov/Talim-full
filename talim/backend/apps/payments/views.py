from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
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

        provider = request.data.get("provider")
        if provider not in ("payme", "click"):
            return Response({"detail": "To'lov usulini tanlang: Payme yoki Click."}, status=status.HTTP_400_BAD_REQUEST)
        plan = SubscriptionPlan.objects.filter(id=request.data.get("plan"), is_active=True).first() \
            if _is_uuid(request.data.get("plan")) else None
        if not plan:
            return Response({"detail": "Tarif topilmadi."}, status=status.HTTP_400_BAD_REQUEST)

        merchant_configured = bool(settings.PAYME_MERCHANT_ID if provider == "payme" else
                                   (settings.CLICK_MERCHANT_ID and settings.CLICK_SERVICE_ID))
        if not merchant_configured:
            if not settings.DEBUG:
                # MUHIM: productionda kalit yo'q bo'lsa, hech qachon "bepul premium" berilmaydi
                return Response({"detail": f"{provider.title()} orqali to'lov hozircha ishlamayapti. Boshqa usulni tanlang.",
                                 "code": "provider_not_configured"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            txn = create_pending_transaction(request.user, plan, provider)
            mark_transaction_success(txn, provider_transaction_id=f"demo-{txn.id}")
            return Response({**PaymentTransactionSerializer(txn).data, "checkout_url": None, "mock": True},
                            status=status.HTTP_201_CREATED)

        txn = create_pending_transaction(request.user, plan, provider)
        checkout_url = build_payme_checkout_url(txn) if provider == "payme" else build_click_checkout_url(txn)
        return Response({**PaymentTransactionSerializer(txn).data, "checkout_url": checkout_url, "mock": False},
                        status=status.HTTP_201_CREATED)


def _is_uuid(value):
    import uuid
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError):
        return False


class SubscriptionStatusView(APIView):
    """GET /payments/status/ — obuna holati, tariflar va qaysi to'lov usullari ishlayotgani."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.conf import settings
        from django.utils import timezone
        from apps.accounts.models import SubscriptionPlan
        from .services import refresh_premium

        sub = refresh_premium(request.user)
        request.user.refresh_from_db(fields=["is_premium"])
        active = request.user.is_premium
        rate = settings.USD_TO_UZS_RATE
        plans = []
        for p in SubscriptionPlan.objects.filter(is_active=True).order_by("price_usd"):
            features = list(p.features or [])
            if not features:
                if p.voice_cloning_enabled:
                    features.append("Ovozni klonlash")
                if p.max_sessions_per_day:
                    features.append(f"Kuniga {p.max_sessions_per_day} ta avatar suhbati")
                features.append("Premium avatarlar")
            plans.append({"id": str(p.id), "name": p.name, "price_usd": float(p.price_usd),
                          "price_uzs": int(p.price_usd * rate), "duration_days": p.duration_days, "features": features})
        return Response({
            "is_premium": request.user.is_premium,
            "active": active,
            "plan": sub.plan.name if sub else None,
            "expires_at": sub.expires_at.isoformat() if sub and sub.expires_at else None,
            "days_left": max(0, (sub.expires_at - timezone.now()).days) if active and sub and sub.expires_at else None,
            "plans": plans,
            "providers": {
                "payme": bool(settings.PAYME_MERCHANT_ID) or settings.DEBUG,
                "click": bool(settings.CLICK_MERCHANT_ID and settings.CLICK_SERVICE_ID) or settings.DEBUG,
            },
            "demo_mode": settings.DEBUG and not (settings.PAYME_MERCHANT_ID or settings.CLICK_MERCHANT_ID),
        })


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


class AdminPlanViewSet(viewsets.ModelViewSet):
    """GET/POST/PATCH/DELETE /payments/admin/plans/ — tariflarni boshqarish."""
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "post", "patch", "delete", "head"]

    def get_queryset(self):
        from apps.accounts.models import SubscriptionPlan
        return SubscriptionPlan.objects.order_by("price_usd")

    def get_serializer_class(self):
        from rest_framework import serializers as s
        from apps.accounts.models import SubscriptionPlan

        class PlanSerializer(s.ModelSerializer):
            subscribers = s.SerializerMethodField()

            class Meta:
                model = SubscriptionPlan
                fields = ["id", "name", "price_usd", "duration_days", "features", "is_active",
                          "voice_cloning_enabled", "max_sessions_per_day", "subscribers"]

            def get_subscribers(self, obj):
                return obj.subscribers.count()
        return PlanSerializer

    def destroy(self, request, *args, **kwargs):
        plan = self.get_object()
        if plan.transactions.exists() or plan.subscribers.exists():
            plan.is_active = False
            plan.save(update_fields=["is_active"])
            return Response({"detail": "Tarifda to'lovlar bor, shuning uchun o'chirilmadi — sotuvdan olindi."}, status=200)
        return super().destroy(request, *args, **kwargs)
