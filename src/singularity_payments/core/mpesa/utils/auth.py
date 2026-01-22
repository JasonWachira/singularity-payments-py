import asyncio
import base64
import time
from typing import TypedDict

import httpx

from ..types.config import MpesaConfig
from .errors import (
    MpesaAuthError,
    MpesaNetworkError,
    MpesaTimeoutError,
    parse_mpesa_api_error,
)
from .retry import retryWithBackoff

ENDPOINTS = {
    "sandbox": "https://sandbox.safaricom.co.ke",
    "production": "https://api.safaricom.co.ke",
}

class TokenResponse(TypedDict):
    access_token: str
    expires_in: str

class MpesaAuth:
    REQUEST_TIMEOUT = 30.0  

    def __init__(self, config: MpesaConfig):
        self.config = config
        self._token: str | None = None
        self._token_expiry: float = 0.0

    

    async def getAccessToken(self) -> str:
        if self._token and time.time() * 1000 < self._token_expiry:
            return self._token

        async def _fetch_token() -> str:
            base_url = ENDPOINTS[self.config['environment']]
            auth = base64.b64encode(
                f"{self.config['consumerKey']}:{self.config['consumerSecret']}".encode()
            ).decode()

            try:
                async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                    response = await client.get(
                        f"{base_url}/oauth/v1/generate",
                        params={"grant_type": "client_credentials"},
                        headers={
                            "Authorization": f"Basic {auth}",
                        },
                    )

                if response.status_code >= 400:
                    try:
                        error_body = response.json()
                    except Exception:
                        error_body = {}
                    raise parse_mpesa_api_error(response.status_code, error_body)

                data: TokenResponse = response.json()

                if not data.get("access_token"):
                    raise MpesaAuthError("No access token in response", data)

                self._token = data["access_token"]
                self._token_expiry = time.time() * 1000 + 50 * 60 * 1000

                return self._token

            except httpx.TimeoutException:
                raise MpesaTimeoutError(
                    "Request timed out while getting access token"
                )

            except MpesaAuthError:
                raise

            except Exception as error:
                raise MpesaNetworkError(
                    f"Failed to get access token: {error}",
                    True,
                    error,
                )

        return await retryWithBackoff(
            _fetch_token,
            {
                "maxRetries": 3,
                "initialDelayMs": 1000,
                "onRetry": lambda error, attempt: print(
                    f"Retrying authentication (attempt {attempt}): {error}"
                ),
            },
        )

    def getBaseUrl(self) -> str:
        return ENDPOINTS[self.config['environment']]

    def getPassword(self) -> str:
        timestamp = self.getTimestamp()
        raw = f"{self.config['shortcode']}{self.config['passkey']}{timestamp}"
        return base64.b64encode(raw.encode()).decode()

    def getTimestamp(self) -> str:
        now = time.localtime()
        return (
            f"{now.tm_year:04d}"
            f"{now.tm_mon:02d}"
            f"{now.tm_mday:02d}"
            f"{now.tm_hour:02d}"
            f"{now.tm_min:02d}"
            f"{now.tm_sec:02d}"
        )
