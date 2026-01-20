from __future__ import annotations

import time
from dataclasses import dataclass

from app.core.exceptions import RateLimitError


@dataclass
class FixedWindowRateLimiter:
    """In-memory fixed-window rate limiter.

    Notes:
    - Suitable for single-instance academic POC.
    - For multi-instance, use a shared store (Redis) — intentionally out of scope.
    """

    window_seconds: int
    max_requests: int

    def __post_init__(self) -> None:
        self._buckets: dict[str, tuple[int, float]] = {}

    def check(self, key: str) -> None:
        now = time.time()
        count, window_start = self._buckets.get(key, (0, now))

        if now - window_start >= self.window_seconds:
            self._buckets[key] = (1, now)
            return

        if count + 1 > self.max_requests:
            raise RateLimitError("rate limit")

        self._buckets[key] = (count + 1, window_start)
