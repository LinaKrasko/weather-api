import asyncio
import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        now = time.time()
        async with self._lock:
            value = self._items.get(key)
            if value is None:
                return None

            expires_at, payload = value
            if expires_at <= now:
                self._items.pop(key, None)
                return None

            return payload

    async def set(self, key: str, payload: Any) -> None:
        expires_at = time.time() + self.ttl_seconds
        async with self._lock:
            self._items[key] = (expires_at, payload)
