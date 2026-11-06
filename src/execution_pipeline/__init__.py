"""
ExecutionPipeline (Phase 16A) — governance-safe, NO-LIVE.

Dieses Paket ist bewusst von `src.execution.*` getrennt, um:
- bestehende Public APIs nicht zu brechen
- eine klare v0 Event-/API-Contract-Surface zu bieten
- Watch-only Observability (read-only) zu ermoeglichen
"""

from .adapter import (
    ExecutionAdapter,
    InMemoryExecutionAdapter,
    NullExecutionAdapter,
    OrderStatus,
    SubmitAck,
    SubmitRequest,
)
from .contracts import (
    ExecutionContext,
    ExecutionError,
    ExecutionPlan,
    ExecutionResult,
    OrderPlan,
)
from .events_v0 import ExecutionEventV0, ExecutionEventTypeV0
from .pipeline import ExecutionPipeline
from .policies import IdempotencyKey, RetryPolicy, TimeoutPolicy
from .store import JsonlExecutionRunStore, RunSummaryV0
from .telemetry import JsonlTelemetryEmitter, NullTelemetryEmitter, TelemetryEmitter

__all__ = [
    # pipeline
    "ExecutionPipeline",
    # contracts
    "ExecutionContext",
    "ExecutionPlan",
    "OrderPlan",
    "ExecutionResult",
    "ExecutionError",
    # events
    "ExecutionEventV0",
    "ExecutionEventTypeV0",
    # policies
    "RetryPolicy",
    "TimeoutPolicy",
    "IdempotencyKey",
    # adapter
    "ExecutionAdapter",
    "NullExecutionAdapter",
    "InMemoryExecutionAdapter",
    "SubmitRequest",
    "SubmitAck",
    "OrderStatus",
    # telemetry
    "TelemetryEmitter",
    "NullTelemetryEmitter",
    "JsonlTelemetryEmitter",
    # store
    "JsonlExecutionRunStore",
    "RunSummaryV0",
]
