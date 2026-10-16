from rest_framework.routers import DefaultRouter
from django.urls import include, path
from .views import PaymentTransactionViewSet, AdminPaymentTransactionViewSet, SubscriptionStatusView, AdminPlanViewSet
from .payme_api import PaymeWebhookView
from .click_api import ClickPrepareView, ClickCompleteView

router = DefaultRouter()
router.register("transactions", PaymentTransactionViewSet, basename="payment-transaction")
router.register("admin/transactions", AdminPaymentTransactionViewSet, basename="admin-payment-transaction")
router.register("admin/plans", AdminPlanViewSet, basename="admin-plan")

urlpatterns = [
    path("status/", SubscriptionStatusView.as_view(), name="subscription-status"),
    path("", include(router.urls)),
    path("payme/webhook/", PaymeWebhookView.as_view(), name="payme-webhook"),
    path("click/prepare/", ClickPrepareView.as_view(), name="click-prepare"),
    path("click/complete/", ClickCompleteView.as_view(), name="click-complete"),
]
