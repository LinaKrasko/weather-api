import asyncio
import time
from collections import deque


class RateLimitExceeded(Exception):
    pass


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_interval_seconds = max(10, window_seconds)
        self._last_cleanup_at = 0.0

    async def check(self, client_id: str) -> None:
        now = time.time()
        window_start = now - self.window_seconds

        async with self._lock:
            bucket = self._requests.get(client_id)
            if bucket is None:
                bucket = deque()
                self._requests[client_id] = bucket

            while bucket and bucket[0] <= window_start:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                raise RateLimitExceeded("Rate limit exceeded")

            bucket.append(now)
            self._cleanup_if_needed(now, window_start)

    def _cleanup_if_needed(self, now: float, window_start: float) -> None:
        if now - self._last_cleanup_at < self._cleanup_interval_seconds:
            return

        stale_clients: list[str] = []
        for client_id, bucket in self._requests.items():
            while bucket and bucket[0] <= window_start:
                bucket.popleft()
            if not bucket:
                stale_clients.append(client_id)

        for client_id in stale_clients:
            self._requests.pop(client_id, None)

        self._last_cleanup_at = now
