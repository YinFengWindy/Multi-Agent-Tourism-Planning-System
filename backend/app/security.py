import asyncio
import time

from fastapi import HTTPException, Request

from app.config import get_settings


class InMemoryRateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit_per_minute = limit_per_minute
        self._buckets: dict[str, tuple[int, int]] = {}
        self._lock = asyncio.Lock()

    async def enforce(self, request: Request) -> None:
        identifier = request.client.host if request.client else "anonymous"
        bucket = int(time.time() // 60)
        async with self._lock:
            current_bucket, count = self._buckets.get(identifier, (bucket, 0))
            if current_bucket != bucket:
                current_bucket, count = bucket, 0
            count += 1
            self._buckets[identifier] = (current_bucket, count)
            if count > self.limit_per_minute:
                raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试。")


rate_limiter = InMemoryRateLimiter(get_settings().rate_limit_per_minute)


async def enforce_rate_limit(request: Request) -> None:
    await rate_limiter.enforce(request)

