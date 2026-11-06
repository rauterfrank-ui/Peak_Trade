"""
Contracts for ExecutionPipeline (v0).

Design goals:
- minimal, typed, deterministic
- NO-LIVE enablement (adapters are required to be side-effect safe in CI)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .policies import IdempotencyKey, RetryPolicy, TimeoutPolicy


@dataclass(frozen=True)
class ExecutionError(Exception):
    """
    Typed pipeline error with stable error_code.
    """

    error_code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.error_code}: {self.message}"


@dataclass(frozen=True)
class OrderPlan:
    """
    Minimal order intent for this pipeline (v0).
    """

    order_id: str
    symbol: str
    side: str  # "buy" / "sell" (stringly-typed on purpose for decoupling)
    quantity: float
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionPlan:
    """
    A run contains one or more orders executed in sequence (MVP).
    """

    orders: List[OrderPlan]
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    timeout: TimeoutPolicy = field(default_factory=TimeoutPolicy)


@dataclass(frozen=True)
class ExecutionContext:
    """
    Context for a single execution run.
    """

    run_id: str
    correlation_id: str
    idempotency_key: IdempotencyKey
    created_at: datetime


@dataclass
class ExecutionResult:
    """
    Result for a single run.
    """

    run_id: str
    correlation_id: str
    status: str  # "success" | "failed" | "canceled"
    orders: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[ExecutionError] = None
