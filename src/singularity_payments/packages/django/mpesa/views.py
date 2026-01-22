import json
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
from dotenv import load_dotenv

from singularity_payments.core.mpesa.client.mpesa_client import MpesaClient
from singularity_payments.core.mpesa.utils.callback import MpesaCallbackHandler

load_dotenv()
# M-PESA config
config = {
    "consumerKey": os.environ["MPESA_CONSUMER_KEY"],
    "consumerSecret": os.environ["MPESA_CONSUMER_SECRET"],
    "passkey": os.environ["MPESA_PASSKEY"],
    "shortcode": os.environ["MPESA_SHORTCODE"],
    "environment": os.environ.get("MPESA_ENVIRONMENT", "sandbox"),
    "callbackUrl": os.environ["MPESA_CALLBACK_URL"],
}

callback_options = {
    "onSuccess": lambda data: print("STK Payment success:", data),
    "onFailure": lambda data: print("STK Payment failed:", data),
}


# Factories
def get_mpesa_client():
    return MpesaClient(config, callback_options)


def get_mpesa_handler():
    return MpesaCallbackHandler(
        on_success=callback_options.get("onSuccess"),
        on_failure=callback_options.get("onFailure"),
        validate_ip=True,
    )


# -----------------------------
# CLIENT API ENDPOINTS
# -----------------------------
@require_POST
@csrf_exempt
async def stk_push(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()
    result = await client.stkPush(payload)
    return JsonResponse(result, safe=False)


@require_POST
@csrf_exempt
async def stk_query(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()

    result = await client.stkQuery(payload)
    return JsonResponse(result, safe=False)


@require_POST
@csrf_exempt
async def b2c(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()
    result = await client.b2c(payload)
    return JsonResponse(result, safe=False)


@require_POST
@csrf_exempt
async def b2b(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()
    result = await client.b2b(payload)
    return JsonResponse(result, safe=False)


@require_POST
@csrf_exempt
async def balance(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()
    result = await client.accountBalance(payload)
    return JsonResponse(result, safe=False)


@require_POST
@csrf_exempt
async def transaction_status(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()
    result = await client.transactionStatus(payload)
    return JsonResponse(result, safe=False)


@require_POST
@csrf_exempt
async def reversal(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()
    result = await client.reversal(payload)
    return JsonResponse(result, safe=False)


@require_POST
@csrf_exempt
async def register_c2b(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()
    result = await client.registerC2BUrl(payload)
    return JsonResponse(result, safe=False)


@require_POST
@csrf_exempt
async def generate_qr(request, client=None, handler=None):
    payload = json.loads(request.body)
    client = client or get_mpesa_client()
    result = await client.generateDynamicQR(payload)
    return JsonResponse(result, safe=False)


# -----------------------------
# WEBHOOK ENDPOINTS
# -----------------------------
@require_POST
@csrf_exempt
async def stk_callback(request, client=None, handler=None):
    handler = handler or get_mpesa_handler()
    payload = json.loads(request.body)
    ip_address = request.META.get("REMOTE_ADDR")
    await handler.handle_callback(payload, ip_address)
    return JsonResponse(handler.create_callback_response())


@require_POST
@csrf_exempt
async def c2b_validation(request, client=None, handler=None):
    handler = handler or get_mpesa_handler()
    payload = json.loads(request.body)
    is_valid = await handler.handle_c2b_validation(payload)
    return JsonResponse(handler.create_callback_response(success=is_valid))


@require_POST
@csrf_exempt
async def c2b_confirmation(request, client=None, handler=None):
    handler = handler or get_mpesa_handler()
    payload = json.loads(request.body)
    await handler.handle_c2b_confirmation(payload)
    return JsonResponse(handler.create_callback_response())


@require_POST
@csrf_exempt
async def b2c_result(request, client=None, handler=None):
    handler = handler or get_mpesa_handler()
    payload = json.loads(request.body)
    parsed = handler.parse_b2c_callback(payload)
    if handler.on_b2c_result:
        result = handler.on_b2c_result(parsed)
        if asyncio.iscoroutine(result):
            await result
    return JsonResponse(handler.create_callback_response())


@require_POST
@csrf_exempt
async def b2b_result(request, client=None, handler=None):
    handler = handler or get_mpesa_handler()
    payload = json.loads(request.body)
    parsed = handler.parse_b2b_callback(payload)
    if handler.on_b2b_result:
        result = handler.on_b2b_result(parsed)
        if asyncio.iscoroutine(result):
            await result
    return JsonResponse(handler.create_callback_response())


@require_POST
@csrf_exempt
async def account_balance_result(request, client=None, handler=None):
    handler = handler or get_mpesa_handler()
    payload = json.loads(request.body)
    parsed = handler.parse_account_balance_callback(payload)
    if handler.on_account_balance:
        result = handler.on_account_balance(parsed)
        if asyncio.iscoroutine(result):
            await result
    return JsonResponse(handler.create_callback_response())


@require_POST
@csrf_exempt
async def transaction_status_result(request, client=None, handler=None):
    handler = handler or get_mpesa_handler()
    payload = json.loads(request.body)
    parsed = handler.parse_transaction_status_callback(payload)
    if handler.on_transaction_status:
        result = handler.on_transaction_status(parsed)
        if asyncio.iscoroutine(result):
            await result
    return JsonResponse(handler.create_callback_response())


@require_POST
@csrf_exempt
async def reversal_result(request, client=None, handler=None):
    handler = handler or get_mpesa_handler()
    payload = json.loads(request.body)
    parsed = handler.parse_reversal_callback(payload)
    if handler.on_reversal:
        result = handler.on_reversal(parsed)
        if asyncio.iscoroutine(result):
            await result
    return JsonResponse(handler.create_callback_response())
