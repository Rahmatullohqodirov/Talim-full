"""Click Merchant API — https://docs.click.uz/
Ikki bosqichli oqim: Prepare (action=0) -> Complete (action=1). Har biri MD5 imzo (sign_string) bilan tekshiriladi.
"""
import hashlib
import time

from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import PaymentTransaction
from .services import mark_transaction_success

ERROR_SUCCESS = 0
ERROR_SIGN_CHECK_FAILED = -1
ERROR_TRANSACTION_NOT_FOUND = -5
ERROR_ALREADY_PAID = -4
ERROR_INCORRECT_AMOUNT = -2
ERROR_USER_NOT_FOUND = -5


def _verify_prepare_sign(data):
    raw = (
        f"{data.get('click_trans_id')}{data.get('service_id')}{settings.CLICK_SECRET_KEY}"
        f"{data.get('merchant_trans_id')}{data.get('amount')}{data.get('action')}{data.get('sign_time')}"
    )
    return hashlib.md5(raw.encode()).hexdigest() == data.get("sign_string")


def _verify_complete_sign(data):
    raw = (
        f"{data.get('click_trans_id')}{data.get('service_id')}{settings.CLICK_SECRET_KEY}"
        f"{data.get('merchant_trans_id')}{data.get('merchant_prepare_id')}"
        f"{data.get('amount')}{data.get('action')}{data.get('sign_time')}"
    )
    return hashlib.md5(raw.encode()).hexdigest() == data.get("sign_string")


@method_decorator(csrf_exempt, name="dispatch")
class ClickPrepareView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data
        txn = PaymentTransaction.objects.filter(id=data.get("merchant_trans_id"), provider=PaymentTransaction.Provider.CLICK).first()
        base = {"click_trans_id": data.get("click_trans_id"), "merchant_trans_id": data.get("merchant_trans_id")}

        if not settings.CLICK_SECRET_KEY or not _verify_prepare_sign(data):
            return Response({**base, "error": ERROR_SIGN_CHECK_FAILED, "error_note": "SIGN CHECK FAILED"})
        if not txn:
            return Response({**base, "error": ERROR_TRANSACTION_NOT_FOUND, "error_note": "Transaction not found"})
        if float(data.get("amount", 0)) != float(txn.amount_uzs):
            return Response({**base, "error": ERROR_INCORRECT_AMOUNT, "error_note": "Incorrect amount"})
        if txn.status == PaymentTransaction.Status.SUCCESS:
            return Response({**base, "error": ERROR_ALREADY_PAID, "error_note": "Already paid"})

        txn.click_prepare_id = int(time.time() * 1000) % 2147483647
        txn.save(update_fields=["click_prepare_id"])
        return Response({**base, "merchant_prepare_id": txn.click_prepare_id, "error": ERROR_SUCCESS, "error_note": "Success"})


@method_decorator(csrf_exempt, name="dispatch")
class ClickCompleteView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data
        txn = PaymentTransaction.objects.filter(id=data.get("merchant_trans_id"), provider=PaymentTransaction.Provider.CLICK).first()
        base = {"click_trans_id": data.get("click_trans_id"), "merchant_trans_id": data.get("merchant_trans_id")}

        if not settings.CLICK_SECRET_KEY or not _verify_complete_sign(data):
            return Response({**base, "error": ERROR_SIGN_CHECK_FAILED, "error_note": "SIGN CHECK FAILED"})
        if not txn:
            return Response({**base, "error": ERROR_TRANSACTION_NOT_FOUND, "error_note": "Transaction not found"})

        error = int(data.get("error", 0))
        if error < 0:
            txn.status = PaymentTransaction.Status.FAILED
            txn.save(update_fields=["status"])
            return Response({**base, "error": ERROR_SUCCESS, "error_note": "Cancelled"})

        if txn.status != PaymentTransaction.Status.SUCCESS:
            mark_transaction_success(txn, str(data.get("click_trans_id")))
        return Response({**base, "merchant_confirm_id": txn.click_prepare_id, "error": ERROR_SUCCESS, "error_note": "Success"})
