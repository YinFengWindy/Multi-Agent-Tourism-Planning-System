import asyncio
import time
from typing import Any

try:
    import redis.asyncio as redis
except ImportError:  # pragma: no cover
    redis = None


class MemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float | None, Any]] = {}
        self._lock = asyncio.Lock()

    async def get_json(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            expires_at, value = entry
            if expires_at is not None and expires_at < time.time():
                self._store.pop(key, None)
                return None
            return value

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
        async with self._lock:
            self._store[key] = (expires_at, value)


class RedisCache:
    def __init__(self, client: Any) -> None:
        self._client = client

    async def get_json(self, key: str) -> Any | None:
        return await self._client.json().get(key)

    async def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        await self._client.json().set(key, "$", value)
        await self._client.expire(key, ttl_seconds)


async def create_cache(redis_url: str) -> MemoryCache | RedisCache:
    if redis and redis_url:
        try:
            client = redis.from_url(redis_url, decode_responses=True)
            await client.ping()
            return RedisCache(client)
        except Exception:
            return MemoryCache()
    return MemoryCache()

