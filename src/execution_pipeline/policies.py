"""
Policies for the Phase 16A ExecutionPipeline (v0).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IdempotencyKey:
    value: str


@dataclass(frozen=True)
class RetryPolicy:
    """
    Deterministic retry policy.

    Note: the pipeline does NOT sleep. It records attempt numbers in events.
    """

    max_attempts: int = 1

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("RetryPolicy.max_attempts must be >= 1")


@dataclass(frozen=True)
class TimeoutPolicy:
    """
    Timeout policy based on an injected time provider.

    deadline_seconds is interpreted as a strict wall-clock budget for a single
    run execution.
    """

    deadline_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.deadline_seconds <= 0:
            raise ValueError("TimeoutPolicy.deadline_seconds must be > 0")
