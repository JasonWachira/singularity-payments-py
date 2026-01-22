from django.urls import path
from . import views
import asyncio
from .views import get_mpesa_handler, get_mpesa_client
from .wrap_view import wrap_view


def mpesa_urls():
    return [
        # CLIENT API ENDPOINTS
        path("stk-push/", wrap_view(views.stk_push, client_factory=get_mpesa_client)),
        path("stk-query/", wrap_view(views.stk_query, client_factory=get_mpesa_client)),
        path("b2c/", wrap_view(views.b2c, client_factory=get_mpesa_client)),
        path("b2b/", wrap_view(views.b2b, client_factory=get_mpesa_client)),
        path("balance/", wrap_view(views.balance, client_factory=get_mpesa_client)),
        path("transaction-status/", wrap_view(views.transaction_status, client_factory=get_mpesa_client)),
        path("reversal/", wrap_view(views.reversal, client_factory=get_mpesa_client)),
        path("register-c2b/", wrap_view(views.register_c2b, client_factory=get_mpesa_client)),
        path("generate-qr/", wrap_view(views.generate_qr, client_factory=get_mpesa_client)),

        # WEBHOOK ENDPOINTS
        path("callback/", wrap_view(views.stk_callback, handler_factory=get_mpesa_handler)),
        path("stk-callback/", wrap_view(views.stk_callback, handler_factory=get_mpesa_handler)),
        path("c2b-validation/", wrap_view(views.c2b_validation, handler_factory=get_mpesa_handler)),
        path("validation/", wrap_view(views.c2b_validation, handler_factory=get_mpesa_handler)),
        path("c2b-confirmation/", wrap_view(views.c2b_confirmation, handler_factory=get_mpesa_handler)),
        path("confirmation/", wrap_view(views.c2b_confirmation, handler_factory=get_mpesa_handler)),
        path("b2c-result/", wrap_view(views.b2c_result, handler_factory=get_mpesa_handler)),
        path("b2c-timeout/", wrap_view(views.b2c_result, handler_factory=get_mpesa_handler)),
        path("b2b-result/", wrap_view(views.b2b_result, handler_factory=get_mpesa_handler)),
        path("b2b-timeout/", wrap_view(views.b2b_result, handler_factory=get_mpesa_handler)),
        path("balance-result/", wrap_view(views.account_balance_result, handler_factory=get_mpesa_handler)),
        path("balance-timeout/", wrap_view(views.account_balance_result, handler_factory=get_mpesa_handler)),
        path("reversal-result/", wrap_view(views.reversal_result, handler_factory=get_mpesa_handler)),
        path("reversal-timeout/", wrap_view(views.reversal_result, handler_factory=get_mpesa_handler)),
        path("status-result/", wrap_view(views.transaction_status_result, handler_factory=get_mpesa_handler)),
        path("status-timeout/", wrap_view(views.transaction_status_result, handler_factory=get_mpesa_handler)),
    ]
