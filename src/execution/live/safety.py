"""
Finish C3 — Safety rails (mock-only, NO-LIVE default).

Invariant checks and bounded-retry bookkeeping. No I/O, no broker calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AbstractSet, MutableSet


class SafetyViolation(Exception):
    """Invariant or policy violation (C3 mock layer)."""


# Hard rule: live execution must remain disabled unless a future gated path exists.
LIVE_ENABLED_FORBIDDEN_DEFAULT = False


def assert_live_stays_disabled(live_enabled: bool) -> None:
    """C3 mock slice: production-style 'live' flag must not be True."""
    if live_enabled:
        raise SafetyViolation("live_enabled_must_be_false_in_c3_mock")


def assert_non_negative_qty(qty: float, *, label: str = "qty") -> None:
    if qty < 0:
        raise SafetyViolation(f"negative_{label}:{qty}")


def assert_non_negative_balance(balance: float) -> None:
    assert_non_negative_qty(balance, label="balance")


def fill_id_is_duplicate(seen: MutableSet[str], fill_id: str) -> bool:
    """
    Idempotency: return True if fill_id was already seen (duplicate event).
    Otherwise add fill_id to seen and return False.
    """
    if fill_id in seen:
        return True
    seen.add(fill_id)
    return False


def fill_id_would_duplicate(seen: AbstractSet[str], fill_id: str) -> bool:
    """Pure check without mutating seen (for reporting)."""
    return fill_id in seen


@dataclass
class BoundedRetryTracker:
    """
    Deterministic bounded retries (no wall clock, no watch loops).
    Stops after max_attempts attempts recorded.
    """

    max_attempts: int
    _attempts: int = field(default=0, init=False)

    def record_attempt(self) -> int:
        self._attempts += 1
        return self._attempts

    def should_stop(self) -> bool:
        return self._attempts >= self.max_attempts

    @property
    def attempts(self) -> int:
        return self._attempts
