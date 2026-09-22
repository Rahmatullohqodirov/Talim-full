"""Payme Merchant API (JSON-RPC 2.0) — https://developer.help.paycom.uz/
Kassa Payme serveridan quyidagi metodlarni chaqiradi:
CheckPerformTransaction, CreateTransaction, PerformTransaction, CancelTransaction, CheckTransaction.
Autentifikatsiya: Authorization: Basic base64("Paycom:<PAYME_KEY>")
"""
import base64
import time

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import PaymentTransaction
from .services import mark_transaction_success

# Payme xatolik kodlari (spetsifikatsiyadan)
ERR_TRANSACTION_NOT_FOUND = -31003
ERR_INVALID_AMOUNT = -31001
ERR_COULD_NOT_PERFORM = -31008
ERR_COULD_NOT_CANCEL = -31007
ERR_ACCOUNT_NOT_FOUND = -31050
ERR_AUTH_FAILED = -32504
ERR_METHOD_NOT_FOUND = -32601


def _rpc_error(request_id, code, message):
    return Response({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def _rpc_result(request_id, result):
    return Response({"jsonrpc": "2.0", "id": request_id, "result": result})


def _to_tiyin(amount_uzs):
    return int(amount_uzs * 100)


@method_decorator(csrf_exempt, name="dispatch")
class PaymeWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        expected = "Basic " + base64.b64encode(f"Paycom:{settings.PAYME_KEY}".encode()).decode()
        if not settings.PAYME_KEY or request.headers.get("Authorization") != expected:
            return _rpc_error(request.data.get("id"), ERR_AUTH_FAILED, "Authorization ma'lumotlari noto'g'ri")

        method = request.data.get("method")
        params = request.data.get("params", {})
        req_id = request.data.get("id")
        handler = {
            "CheckPerformTransaction": self.check_perform,
            "CreateTransaction": self.create_transaction,
            "PerformTransaction": self.perform_transaction,
            "CancelTransaction": self.cancel_transaction,
            "CheckTransaction": self.check_transaction,
        }.get(method)
        if not handler:
            return _rpc_error(req_id, ERR_METHOD_NOT_FOUND, "Method topilmadi")
        return handler(req_id, params)

    def _get_txn(self, params):
        txn_id = params.get("account", {}).get("transaction_id")
        return PaymentTransaction.objects.filter(id=txn_id, provider=PaymentTransaction.Provider.PAYME).select_related("plan").first()

    def check_perform(self, req_id, params):
        txn = self._get_txn(params)
        if not txn:
            return _rpc_error(req_id, ERR_ACCOUNT_NOT_FOUND, "Tranzaksiya (account) topilmadi")
        if _to_tiyin(txn.amount_uzs) != int(params.get("amount", -1)):
            return _rpc_error(req_id, ERR_INVALID_AMOUNT, "Summa mos kelmadi")
        return _rpc_result(req_id, {"allow": True})

    def create_transaction(self, req_id, params):
        txn = self._get_txn(params)
        if not txn:
            return _rpc_error(req_id, ERR_ACCOUNT_NOT_FOUND, "Tranzaksiya (account) topilmadi")
        if _to_tiyin(txn.amount_uzs) != int(params.get("amount", -1)):
            return _rpc_error(req_id, ERR_INVALID_AMOUNT, "Summa mos kelmadi")

        payme_id = params["id"]
        # Boshqa Payme tranzaksiyasi shu buyurtmani band qilib turgan bo'lsa
        if txn.provider_transaction_id and txn.provider_transaction_id != payme_id and txn.payme_state == 1:
            return _rpc_error(req_id, ERR_COULD_NOT_PERFORM, "Boshqa tranzaksiya jarayonda")

        if not txn.provider_transaction_id:
            txn.provider_transaction_id = payme_id
            txn.payme_state = 1
            txn.payme_create_time_ms = params.get("time", int(time.time() * 1000))
            txn.save(update_fields=["provider_transaction_id", "payme_state", "payme_create_time_ms"])

        return _rpc_result(req_id, {
            "create_time": txn.payme_create_time_ms,
            "transaction": str(txn.id),
            "state": txn.payme_state,
        })

    def perform_transaction(self, req_id, params):
        payme_id = params["id"]
        txn = PaymentTransaction.objects.filter(provider_transaction_id=payme_id, provider=PaymentTransaction.Provider.PAYME).first()
        if not txn:
            return _rpc_error(req_id, ERR_TRANSACTION_NOT_FOUND, "Tranzaksiya topilmadi")
        if txn.payme_state == 1:
            mark_transaction_success(txn, payme_id)
            txn.payme_state = 2
            txn.payme_perform_time_ms = int(time.time() * 1000)
            txn.save(update_fields=["payme_state", "payme_perform_time_ms"])
        elif txn.payme_state != 2:
            return _rpc_error(req_id, ERR_COULD_NOT_PERFORM, "Tranzaksiyani bajarib bo'lmaydi")
        return _rpc_result(req_id, {"transaction": str(txn.id), "perform_time": txn.payme_perform_time_ms, "state": 2})

    def cancel_transaction(self, req_id, params):
        payme_id = params["id"]
        txn = PaymentTransaction.objects.filter(provider_transaction_id=payme_id, provider=PaymentTransaction.Provider.PAYME).first()
        if not txn:
            return _rpc_error(req_id, ERR_TRANSACTION_NOT_FOUND, "Tranzaksiya topilmadi")
        txn.payme_state = -1 if txn.payme_state == 1 else -2
        txn.payme_cancel_time_ms = int(time.time() * 1000)
        txn.payme_cancel_reason = params.get("reason")
        txn.status = PaymentTransaction.Status.CANCELLED
        txn.save(update_fields=["payme_state", "payme_cancel_time_ms", "payme_cancel_reason", "status"])
        return _rpc_result(req_id, {"transaction": str(txn.id), "cancel_time": txn.payme_cancel_time_ms, "state": txn.payme_state})

    def check_transaction(self, req_id, params):
        payme_id = params["id"]
        txn = PaymentTransaction.objects.filter(provider_transaction_id=payme_id, provider=PaymentTransaction.Provider.PAYME).first()
        if not txn:
            return _rpc_error(req_id, ERR_TRANSACTION_NOT_FOUND, "Tranzaksiya topilmadi")
        return _rpc_result(req_id, {
            "create_time": txn.payme_create_time_ms,
            "perform_time": txn.payme_perform_time_ms or 0,
            "cancel_time": txn.payme_cancel_time_ms or 0,
            "transaction": str(txn.id),
            "state": txn.payme_state,
            "reason": txn.payme_cancel_reason,
        })
