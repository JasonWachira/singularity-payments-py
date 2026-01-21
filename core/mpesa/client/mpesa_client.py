from typing import TypedDict, NotRequired, Optional
import asyncio
import aiohttp
import re
import math

from ..types.config import MpesaConfig
from ..utils.auth import MpesaAuth
from ..utils.callback import (
    MpesaCallbackHandler,
    ParsedCallbackData,
    ParsedC2BCallback,
    CallbackHandlerOptions,
)
from ..types.mpesa import *
from ..utils.errors import (
    MpesaValidationError,
    MpesaTimeoutError,
    MpesaNetworkError,
    parse_mpesa_api_error,
)
from ..utils.retry import retryWithBackoff, RetryOptions
from ..utils.ratelimiter import RateLimiter, RedisLike, RedisRateLimiter


class RateLimitOption(TypedDict, total=False):
    enabled: bool
    maxRequests: int
    windowMs: int
    redis: RedisLike


class MpesaClientOptions(TypedDict, total=False):
    callbackOptions: CallbackHandlerOptions
    retryOptions: RetryOptions
    rateLimitOptions: RateLimitOption
    requestTimeout: int


class MpesaClient:
    def __init__(self, config: MpesaConfig, options: Optional[MpesaClientOptions] = None):
        self.config = config
        self.auth = MpesaAuth(config)
        self.options = options or {}

        self.callbackHandler = MpesaCallbackHandler(
            self.options.get("callbackOptions")
        )

        self.retryOptions = self.options.get("retryOptions")
        self.REQUEST_TIMEOUT = self.options.get("requestTimeout", 30000)

        self.ratelimiter: RateLimiter | RedisRateLimiter | None = None

        rate_opts = self.options.get("rateLimitOptions")
        if rate_opts and rate_opts.get("enabled", True):
            limiter_config = {
                "maxRequests": rate_opts.get("maxRequests", 100),
                "windowMs": rate_opts.get("windowMs", 60000),
            }

            if rate_opts.get("redis"):
                self.ratelimiter = RedisRateLimiter(rate_opts["redis"], limiter_config)
            else:
                self.ratelimiter = RateLimiter(limiter_config)

        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT / 1000)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def makeRequest(
            self,
            endpoint: str,
            payload: dict,
            ratelimitKey: str | None = None,
    ):
        async def _request():
            if self.ratelimiter and ratelimitKey:
                await self.ratelimiter.checkLimit(ratelimitKey)

            token = await self.auth.getAccessToken()
            base_url = self.auth.getBaseUrl()
            url = f"{base_url}{endpoint}"

            session = await self._get_session()

            try:
                async with session.post(
                        url,
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json",
                        },
                ) as response:

                    if not 200 <= response.status < 300:
                        try:
                            error_body = await response.json()
                        except Exception:
                            error_body = {}
                            raise parse_mpesa_api_error(response.status, error_body)

                    return await response.json()

            except asyncio.TimeoutError:
                raise MpesaTimeoutError(f"Request timed out for {endpoint}")

            except Exception as error:
                if hasattr(error, "statusCode"):
                    raise
                raise MpesaNetworkError(
                    f"Network error on {endpoint}: {error}",
                    True,
                    error,
                )

        return await retryWithBackoff(_request, self.retryOptions)

    def validateAndFormatPhone(self, phone: str) -> str:
        formatted = re.sub(r"[\s\-+]", "", phone)

        if formatted.startswith("0"):
            formatted = "254" + formatted[1:]
        elif not formatted.startswith("254"):
            formatted = "254" + formatted

        if not re.match(r"^254[17]\d{8}$", formatted):
            raise MpesaValidationError(f"Invalid phone number format: {phone}")

        return formatted

    async def stkPush(self, request: STKPushRequest) -> STKPushResponse:
        if request["amount"] < 1:
            raise MpesaValidationError("Amount must be at least 1")

        if not request.get("accountReference") or len(request["accountReference"]) > 13:
            raise MpesaValidationError("Account reference must be ≤ 13 characters")

        if not request.get("transactionDesc"):
            raise MpesaValidationError("Transaction description required")

        phone = self.validateAndFormatPhone(request["phoneNumber"])

        payload = {
            "BusinessShortCode": self.config["shortcode"],
            "Password": self.auth.getPassword(),
            "Timestamp": self.auth.getTimestamp(),
            "TransactionType": "CustomerPayBillOnline",
            "Amount": math.floor(request["amount"]),
            "PartyA": phone,
            "PartyB": self.config["shortcode"],
            "PhoneNumber": phone,
            "CallBackURL": request.get("callbackUrl") or self.config["callbackUrl"],
            "AccountReference": request["accountReference"],
            "TransactionDesc": request["transactionDesc"],
        }

        return await self.makeRequest(
            "/mpesa/stkpush/v1/processrequest",
            payload,
            f"stk:{phone}",
        )

    async def stkQuery(self, request: TransactionStatusRequest) -> TransactionStatusResponse:
        if not request.get("CheckoutRequestID"):
            raise MpesaValidationError("CheckoutRequestID required")

        payload = {
            "BusinessShortCode": self.config["shortcode"],
            "Password": self.auth.getPassword(),
            "Timestamp": self.auth.getTimestamp(),
            "CheckoutRequestID": request["CheckoutRequestID"],
        }

        return await self.makeRequest(
            "/mpesa/stkpushquery/v1/query",
            payload,
            f"query:{request['CheckoutRequestID']}",
        )

    async def registerC2BUrl(self, request: C2BRegisterRequest) -> C2BRegisterResponse:
        if not request.get("confirmationURL") or not request.get("validationURL"):
            raise MpesaValidationError("Both confirmation and validation URLs required")

        payload = {
            "ShortCode": request["shortCode"],
            "ResponseType": request["responseType"],
            "ConfirmationURL": request["confirmationURL"],
            "ValidationURL": request["validationURL"],
        }

        return await self.makeRequest(
            "/mpesa/c2b/v1/registerurl",
            payload,
            "c2b:register",
        )

    async def b2c(self, request: B2CRequest) -> B2CResponse:
        if request["amount"] < 10:
            raise MpesaValidationError("B2C amount must be ≥ 10")

        if not request.get("remarks") or len(request["remarks"]) > 100:
            raise MpesaValidationError("Remarks must be 1–100 characters")

        phone = self.validateAndFormatPhone(request["phoneNumber"])

        payload = {
            "InitiatorName": self.config["initiatorName"],
            "SecurityCredential": self.config["securityCredential"],
            "CommandID": request["commandID"],
            "Amount": math.floor(request["amount"]),
            "PartyA": self.config["shortcode"],
            "PartyB": phone,
            "Remarks": request["remarks"],
            "QueueTimeOutURL": request.get("timeoutUrl") or self.config["timeoutUrl"],
            "ResultURL": request.get("resultUrl") or self.config["resultUrl"],
            "Occasion": request.get("occasion") or "",
        }

        return await self.makeRequest(
            "/mpesa/b2c/v1/paymentrequest",
            payload,
            f"b2c:{phone}",
        )

    async def b2b(self, request: B2BRequest) -> B2BResponse:
        if request["amount"] < 1:
            raise MpesaValidationError("Amount must be ≥ 1")

        if not request.get("remarks") or len(request["remarks"]) > 100:
            raise MpesaValidationError("Remarks must be 1–100 characters")

        if not request.get("accountReference") or len(request["accountReference"]) > 13:
            raise MpesaValidationError("Account reference must be ≤ 13 characters")

        payload = {
            "Initiator": self.config["initiatorName"],
            "SecurityCredential": self.config["securityCredential"],
            "CommandID": request["commandID"],
            "Amount": math.floor(request["amount"]),
            "PartyA": self.config["shortcode"],
            "PartyB": request["partyB"],
            "SenderIdentifierType": request["senderIdentifierType"],
            "ReceiverIdentifierType": request["receiverIdentifierType"],
            "Remarks": request["remarks"],
            "AccountReference": request["accountReference"],
            "QueueTimeOutURL": request.get("timeoutUrl") or self.config["timeoutUrl"],
            "ResultURL": request.get("resultUrl") or self.config["resultUrl"],
        }

        return await self.makeRequest(
            "/mpesa/b2b/v1/paymentrequest",
            payload,
            f"b2b:{request['partyB']}",
        )

    async def accountBalance(
            self, request: Optional[AccountBalanceRequest] = None
    ) -> AccountBalanceResponse:
        request = request or {}

        payload = {
            "Initiator": self.config["initiatorName"],
            "SecurityCredential": self.config["securityCredential"],
            "CommandID": "AccountBalance",
            "PartyA": request.get("partyA") or self.config["shortcode"],
            "IdentifierType": request.get("identifierType") or "4",
            "Remarks": request.get("remarks") or "Account balance query",
            "QueueTimeOutURL": request.get("timeoutUrl") or self.config["timeoutUrl"],
            "ResultURL": request.get("resultUrl") or self.config["resultUrl"],
        }

        return await self.makeRequest(
            "/mpesa/accountbalance/v1/query",
            payload,
            "balance",
        )

    async def transactionStatus(
            self, request: GeneralTransactionStatusRequest
    ) -> GeneralTransactionStatusResponse:
        if not request.get("transactionID"):
            raise MpesaValidationError("Transaction ID required")

        payload = {
            "Initiator": self.config["initiatorName"],
            "SecurityCredential": self.config["securityCredential"],
            "CommandID": "TransactionStatusQuery",
            "TransactionID": request["transactionID"],
            "PartyA": request.get("partyA") or self.config["shortcode"],
            "IdentifierType": request.get("identifierType") or "4",
            "Remarks": request.get("remarks") or "Transaction status query",
            "Occasion": request.get("occasion") or "",
            "QueueTimeOutURL": request.get("timeoutUrl") or self.config["timeoutUrl"],
            "ResultURL": request.get("resultUrl") or self.config["resultUrl"],
        }

        return await self.makeRequest(
            "/mpesa/transactionstatus/v1/query",
            payload,
            f"status:{request['transactionID']}",
        )

    async def reversal(self, request: ReversalRequest) -> ReversalResponse:
        if not request.get("transactionID"):
            raise MpesaValidationError("Transaction ID required")

        if request["amount"] < 1:
            raise MpesaValidationError("Amount must be ≥ 1")

        payload = {
            "Initiator": self.config["initiatorName"],
            "SecurityCredential": self.config["securityCredential"],
            "CommandID": "TransactionReversal",
            "TransactionID": request["transactionID"],
            "Amount": math.floor(request["amount"]),
            "ReceiverParty": request.get("receiverParty") or self.config["shortcode"],
            "ReceiverIdentifierType": request.get("receiverIdentifierType") or "11",
            "Remarks": request.get("remarks") or "Transaction reversal",
            "Occasion": request.get("occasion") or "",
            "QueueTimeOutURL": request.get("timeoutUrl") or self.config["timeoutUrl"],
            "ResultURL": request.get("resultUrl") or self.config["resultUrl"],
        }

        return await self.makeRequest(
            "/mpesa/reversal/v1/request",
            payload,
            f"reversal:{request['transactionID']}",
        )

    async def generateDynamicQR(
            self, request: DynamicQRRequest
    ) -> DynamicQRResponse:
        if not request.get("merchantName") or len(request["merchantName"]) > 26:
            raise MpesaValidationError("Merchant name must be ≤ 26 characters")

        if not request.get("refNo") or len(request["refNo"]) > 12:
            raise MpesaValidationError("Reference number must be ≤ 12 characters")

        if request["amount"] < 1:
            raise MpesaValidationError("Amount must be ≥ 1")

        payload = {
            "MerchantName": request["merchantName"],
            "RefNo": request["refNo"],
            "Amount": math.floor(request["amount"]),
            "TrxCode": request["transactionType"],
            "CPI": request["creditPartyIdentifier"],
            "Size": request["size"],
        }

        return await self.makeRequest(
            "/mpesa/qrcode/v1/generate",
            payload,
            f"qr:{request['refNo']}",
        )

    def getCallbackHandler(self) -> MpesaCallbackHandler:
        return self.callbackHandler

    async def handleStkCallback(self, callback: STKCallback, ipAddress: str | None = None):
        try:
            await self.callbackHandler.handle_callback(callback, ipAddress)
            return self.callbackHandler.create_callback_response(True)
        except Exception:
            return self.callbackHandler.create_callback_response(False, "Internal Error")

    async def handleC2BValidation(self, callback: C2BCallback):
        try:
            is_valid = await self.callbackHandler.handle_c2b_validation(callback)
            return self.callbackHandler.create_callback_response(
                is_valid, "Accepted" if is_valid else "Rejected"
            )
        except Exception:
            return self.callbackHandler.create_callback_response(False, "Validation Failed")

    async def handleC2BConfirmation(self, callback: C2BCallback):
        try:
            await self.callbackHandler.handle_c2b_confirmation(callback)
            return self.callbackHandler.create_callback_response(True)
        except Exception as e:
            print(f"C2B confirmation error: {e}")
            return self.callbackHandler.create_callback_response(False, "Processing Failed")

    def parseSTKCallback(self, callback: STKCallback) -> ParsedCallbackData:
        return self.callbackHandler.parse_callback(callback)

    def parseC2BCallback(self, callback: C2BCallback) -> ParsedC2BCallback:
        return self.callbackHandler.parse_c2b_callback(callback)

    async def handleB2CCallback(self, callback: B2CCallback):
        try:
            parsed = self.callbackHandler.parse_b2c_callback(callback)
            if self.callbackHandler.on_b2c_result:
                await self.callbackHandler.on_b2c_result(parsed)
            return self.callbackHandler.create_callback_response(parsed.is_success)
        except Exception as e:
            print(f"B2C callback error: {e}")
            return self.callbackHandler.create_callback_response(False, "Processing Failed")

    async def handleAccountBalanceCallback(self, callback: AccountBalanceCallback):
        try:
            parsed = self.callbackHandler.parse_account_balance_callback(callback)
            if self.callbackHandler.on_account_balance:
                await self.callbackHandler.on_account_balance(parsed)
            return self.callbackHandler.create_callback_response(parsed.is_success)
        except Exception as e:
            print(f"Account balance callback error: {e}")
            return self.callbackHandler.create_callback_response(False, "Processing Failed")

    async def handleTransactionStatusCallback(self, callback: TransactionStatusCallback):
        try:
            parsed = self.callbackHandler.parse_transaction_status_callback(callback)
            if self.callbackHandler.on_transaction_status:
                await self.callbackHandler.on_transaction_status(parsed)
            return self.callbackHandler.create_callback_response(parsed.is_success)
        except Exception as e:
            print(f"Transaction status callback error: {e}")
            return self.callbackHandler.create_callback_response(False, "Processing Failed")

    async def handleReversalCallback(self, callback: ReversalCallback):
        try:
            parsed = self.callbackHandler.parse_reversal_callback(callback)
            if self.callbackHandler.on_reversal:
                await self.callbackHandler.on_reversal(parsed)
            return self.callbackHandler.create_callback_response(parsed.is_success)
        except Exception as e:
            print(f"Reversal callback error: {e}")
            return self.callbackHandler.create_callback_response(False, "Processing Failed")

    async def destroy(self):
        if self._session and not self._session.closed:
            await self._session.close()

        if isinstance(self.ratelimiter, RateLimiter):
            self.ratelimiter.destroy()
