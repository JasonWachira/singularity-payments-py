import asyncio
import time
from typing import TypedDict, Optional, Dict, Protocol

from .errors import MpesaRateLimitError


class RateLimiterOptions(TypedDict, total=False):
    maxRequests: int
    windowMs: int
    keyPrefix: str


class RateLimitEntry(TypedDict):
    count: int
    resetAt: int




class RateLimiter:
    def __init__(self, options: RateLimiterOptions):
        self.options: RateLimiterOptions = {
            "keyPrefix": "mpesa",
            **options,
        }
        self.store: Dict[str, RateLimitEntry] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup()

    async def checkLimit(self, key: str) -> None:
        full_key = f"{self.options['keyPrefix']}:{key}"
        now = int(time.time() * 1000)

        entry = self.store.get(full_key)

        if not entry or now >= entry["resetAt"]:
            self.store[full_key] = {
                "count": 1,
                "resetAt": now + self.options["windowMs"],
            }
            return

        if entry["count"] >= self.options["maxRequests"]:
            retry_after = (entry["resetAt"] - now + 999) // 1000
            raise MpesaRateLimitError(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after,
                {
                    "limit": self.options["maxRequests"],
                    "windowMs": self.options["windowMs"],
                    "resetAt": entry["resetAt"],
                },
            )

        entry["count"] += 1

    

    def getUsage(self, key: str) -> dict:
        full_key = f"{self.options['keyPrefix']}:{key}"
        now = int(time.time() * 1000)
        entry = self.store.get(full_key)

        if not entry or now >= entry["resetAt"]:
            return {
                "count": 0,
                "remaining": self.options["maxRequests"],
                "resetAt": now + self.options["windowMs"],
            }

        return {
            "count": entry["count"],
            "remaining": max(0, self.options["maxRequests"] - entry["count"]),
            "resetAt": entry["resetAt"],
        }

    

    def reset(self, key: str) -> None:
        full_key = f"{self.options['keyPrefix']}:{key}"
        self.store.pop(full_key, None)

    def resetAll(self) -> None:
        self.store.clear()

    def _start_cleanup(self) -> None:
        async def cleanup():
            while True:
                await asyncio.sleep(60)
                now = int(time.time() * 1000)
                self.store = {
                    k: v for k, v in self.store.items()
                    if now < v["resetAt"]
                }

        self._cleanup_task = asyncio.create_task(cleanup())

    def destroy(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
        self.store.clear()


# -------------------------
# Redis-backed rate limiter
# -------------------------

class RedisLike(Protocol):
    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: str, mode: str, duration: int) -> None: ...
    async def incr(self, key: str) -> int: ...
    async def expire(self, key: str, seconds: int) -> None: ...


class RedisRateLimiter:
    def __init__(self, redis: RedisLike, options: RateLimiterOptions):
        self.redis = redis
        self.options: RateLimiterOptions = {
            "keyPrefix": "mpesa",
            **options,
        }

    async def checkLimit(self, key: str) -> None:
        full_key = f"{self.options['keyPrefix']}:{key}"
        count = await self.redis.incr(full_key)

        if count == 1:
            await self.redis.expire(
                full_key,
                (self.options["windowMs"] + 999) // 1000,
            )

        if count > self.options["maxRequests"]:
            ttl_key = f"{full_key}:ttl"
            ttl = await self.redis.get(ttl_key)
            retry_after = int(ttl) if ttl else (self.options["windowMs"] + 999) // 1000

            raise MpesaRateLimitError(
                f"Rate limit exceeded. Try again in {retry_after} seconds.",
                retry_after,
                {
                    "limit": self.options["maxRequests"],
                    "windowMs": self.options["windowMs"],
                },
            )

    async def reset(self, key: str) -> None:
        full_key = f"{self.options['keyPrefix']}:{key}"
        await self.redis.set(full_key, "0", "EX", 0)
