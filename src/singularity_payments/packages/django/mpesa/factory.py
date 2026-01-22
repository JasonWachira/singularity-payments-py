from singularity_payments.core.mpesa.client.mpesa_client import MpesaClient
from singularity_payments.core.mpesa.utils.callback import MpesaCallbackHandler
from .urls import mpesa_urls


def create_mpesa(config, options=None):
    options = options or {}
    callback_options = options.get("callbackOptions", {})

    client = MpesaClient(config, options)

    handler = MpesaCallbackHandler(
        on_success=callback_options.get("onSuccess"),
        on_failure=callback_options.get("onFailure"),
        on_b2c_result=callback_options.get("onB2CResult"),
        on_b2b_result=callback_options.get("onB2BResult"),
        on_account_balance=callback_options.get("onAccountBalance"),
        on_transaction_status=callback_options.get("onTransactionStatus"),
        on_reversal=callback_options.get("onReversal"),
        validate_ip=True,
    )

    return {
        "client": client,
        "handler": handler,
        "urls": mpesa_urls(),
    }
