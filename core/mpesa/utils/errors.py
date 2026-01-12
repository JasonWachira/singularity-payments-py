from __future__ import annotations
from typing import Any, Optional


class MpesaError(Exception):
    """Base class for all Mpesa errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details


class MpesaAuthError(MpesaError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "AUTH_ERROR", 401, details)


class MpesaValidationError(MpesaError):
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class MpesaNetworkError(MpesaError):
    def __init__(self, message: str, is_retryable: bool = True, details: Optional[Any] = None):
        super().__init__(message, "NETWORK_ERROR", 503, details)
        self.is_retryable = is_retryable


class MpesaTimeoutError(MpesaError):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, "TIMEOUT_ERROR", 408, details)


class MpesaRateLimitError(MpesaError):
    """429 Too Many Requests."""

    def __init__(self, message: str, retry_after: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", 429, details)
        self.retry_after = retry_after


class MpesaApiError(MpesaError):
    def __init__(self, message: str, code: str, status_code: int, response_body: Optional[Any] = None):
        super().__init__(message, code, status_code, response_body)
        self.response_body = response_body


def parse_mpesa_api_error(status_code: int, response_body: dict[str, Any]) -> MpesaError:
    error_message = (
        response_body.get("errorMessage")
        or response_body.get("ResponseDescription")
        or response_body.get("message")
        or "Unknown API error"
    )

    error_code = response_body.get("errorCode") or response_body.get("ResponseCode") or "UNKNOWN_ERROR"

    if status_code == 401:
        return MpesaAuthError(error_message, response_body)
    if status_code == 403:
        return MpesaAuthError(error_message, response_body)
    if status_code == 400:
        return MpesaValidationError(error_message, response_body)
    if status_code == 429:
        retry_after = response_body.get("retryAfter")
        return MpesaRateLimitError(error_message, retry_after, response_body)
    if status_code >= 500:
        return MpesaNetworkError(error_message, True, response_body)

    return MpesaApiError(error_message, error_code, status_code, response_body)
