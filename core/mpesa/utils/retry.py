import asyncio
import math
import random
from typing import TypedDict, Callable, Awaitable

from .errors import MpesaError, MpesaNetworkError, MpesaRateLimitError

class RetryOptions(TypedDict, total=False):
    maxRetries: int
    initialDelayMs: int
    maxDelayMs: int
    backoffMultiplier: int
    retryableStatusCodes: list[int]
    onRetry: Callable[[Exception, int], None]


def _noop_on_retry(error: Exception, attempt: int) -> None:
    pass


DEFAULT_RETRY_OPTIONS: RetryOptions = {
    "maxRetries": 3,
    "initialDelayMs": 1000,
    "maxDelayMs": 10000,
    "backoffMultiplier": 2,
    "retryableStatusCodes": [408, 429, 500, 502, 503, 504],
    "onRetry": _noop_on_retry,
}



def isRetryableError(error: Exception, retryableStatusCodes: list[int]) -> bool:
    if isinstance(error, MpesaNetworkError):
       return getattr(error, "is_retryable", False)

    if isinstance(error, MpesaRateLimitError):
        return True

    if isinstance(error, MpesaError) and getattr(error, "status_code", None):
        return error["status_code"] in retryableStatusCodes

    if (
        getattr(error, "name", None) == "FetchError"
        or getattr(error, "code", None) in {"ECONNREFUSED", "ETIMEDOUT"}
    ):
        return True

    return False



def calculateDelay(
    attempt: int,
    options: RetryOptions,
    error: Exception | None = None,
) -> int:
    if isinstance(error, MpesaRateLimitError) and getattr(error, "retry_after", None):
        return error["retry_after"] * 1000

    delay = min(
        options["initialDelayMs"]
        * (options["backoffMultiplier"] ** attempt),
        options["maxDelayMs"]
    )


    jitter = delay * 0.2 * (random.random() - 0.5) * 2
    return math.floor(delay + jitter)

async def retryWithBackoff(
    fn: Callable[[], Awaitable],
    options: RetryOptions | None = None,
):
    opts: RetryOptions = {
        **DEFAULT_RETRY_OPTIONS,
        **(options or {}),
    }

    last_error: Exception | None = None

    for attempt in range(opts["maxRetries"] + 1):
        try:
            return await fn()
        except Exception as error:
            last_error = error

            if (
                not isRetryableError(error, opts["retryableStatusCodes"])
                or attempt == opts["maxRetries"]
            ):
                raise

            delay = calculateDelay(attempt, opts, error)
            opts["onRetry"](error, attempt + 1)

            await asyncio.sleep(delay / 1000)

    
    raise last_error
