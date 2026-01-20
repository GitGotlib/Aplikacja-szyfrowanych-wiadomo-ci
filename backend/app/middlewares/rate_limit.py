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
    max_buckets: int = 50_000
    cleanup_interval_seconds: int = 60

    def __post_init__(self) -> None:
        self._buckets: dict[str, tuple[int, float]] = {}
        self._last_cleanup = time.time()

    def _cleanup(self, now: float, *, force: bool = False) -> None:
        if not force and (now - self._last_cleanup) < self.cleanup_interval_seconds:
            return
        self._last_cleanup = now
        expired_before = now - self.window_seconds
        self._buckets = {k: v for k, v in self._buckets.items() if v[1] >= expired_before}

    def check(self, key: str) -> None:
        now = time.time()
        if len(self._buckets) > self.max_buckets:
            self._cleanup(now, force=True)
        count, window_start = self._buckets.get(key, (0, now))

        if now - window_start >= self.window_seconds:
            self._buckets[key] = (1, now)
            return

        if count + 1 > self.max_requests:
            raise RateLimitError("rate limit")

        self._buckets[key] = (count + 1, window_start)
