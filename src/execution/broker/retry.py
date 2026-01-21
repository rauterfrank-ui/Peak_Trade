"""
Deterministic retry policy for broker operations (Finish C1).

Differences vs `src/execution/retry_policy.py`:
- No sleeps by default in tests (sleep is injectable)
- Deterministic (no jitter unless explicitly enabled)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

from src.execution.broker.errors import PermanentBrokerError, TransientBrokerError

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int = 3
    initial_delay_s: float = 0.0
    max_delay_s: float = 0.0
    exponential_base: float = 2.0


class RetryPolicy:
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        sleep: Optional[Callable[[float], None]] = None,
    ) -> None:
        self._config = config or RetryConfig()
        self._sleep = sleep or (lambda _s: None)

    def should_retry(self, exc: Exception, attempt: int) -> bool:
        if attempt >= self._config.max_retries:
            return False
        if isinstance(exc, PermanentBrokerError):
            return False
        if isinstance(exc, TransientBrokerError):
            return True
        # Conservative default: do not retry unknown exception types in broker layer.
        return False

    def delay_s(self, attempt: int) -> float:
        delay = self._config.initial_delay_s * (self._config.exponential_base**attempt)
        return min(delay, self._config.max_delay_s)

    def run(self, fn: Callable[[], T]) -> T:
        attempt = 0
        while True:
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001 - retry boundary
                if not self.should_retry(exc, attempt):
                    raise
                delay = self.delay_s(attempt)
                self._sleep(delay)
                attempt += 1
