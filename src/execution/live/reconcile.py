"""
Finish C3 — Minimal reconciler (mock broker state, NO network).

Compares local order intent vs broker-reported snapshot and emits a structured report.
Corrective actions are descriptive strings only (not executed).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Sequence

BrokerSignal = Optional[Literal["rate_limit", "timeout", "transient"]]


@dataclass(frozen=True)
class LocalOrder:
    order_id: str
    qty: float
    filled_qty: float
    status: str  # open | cancelled | filled


@dataclass(frozen=True)
class BrokerOrder:
    order_id: str
    qty: float
    filled_qty: float
    status: str


@dataclass(frozen=True)
class ReconcileMismatch:
    order_id: str
    code: str
    message: str


@dataclass(frozen=True)
class ReconcileReport:
    mismatches: tuple[ReconcileMismatch, ...]
    corrective_actions: tuple[str, ...]
    broker_signal: BrokerSignal = None


def reconcile_orders(
    local: Sequence[LocalOrder],
    broker: Sequence[BrokerOrder],
    *,
    broker_signal: BrokerSignal = None,
) -> ReconcileReport:
    """
    Diff local vs broker snapshots (all mock data).

    broker_signal simulates transport/exchange errors without I/O:
    - rate_limit: reconcile aborts with a single mismatch + backoff action
    - timeout / transient: single mismatch + retry suggestion (caller uses BoundedRetryTracker)
    """
    actions: list[str] = []
    mismatches: list[ReconcileMismatch] = []

    if broker_signal == "rate_limit":
        mismatches.append(
            ReconcileMismatch(
                order_id="*",
                code="rate_limit",
                message="broker_snapshot_unavailable: rate_limit",
            )
        )
        actions.append("mock_action: exponential_backoff_wait (no network in C3)")
        return ReconcileReport(
            mismatches=tuple(mismatches),
            corrective_actions=tuple(actions),
            broker_signal=broker_signal,
        )

    if broker_signal in ("timeout", "transient"):
        mismatches.append(
            ReconcileMismatch(
                order_id="*",
                code=broker_signal,
                message=f"broker_snapshot_unavailable: {broker_signal}",
            )
        )
        actions.append("mock_action: bounded_retry_with_same_snapshot_request")
        return ReconcileReport(
            mismatches=tuple(mismatches),
            corrective_actions=tuple(actions),
            broker_signal=broker_signal,
        )

    bmap = {b.order_id: b for b in broker}
    for lo in local:
        bo = bmap.get(lo.order_id)
        if bo is None:
            mismatches.append(
                ReconcileMismatch(
                    order_id=lo.order_id,
                    code="missing_on_broker",
                    message="local order not present in broker snapshot",
                )
            )
            actions.append(f"mock_action: verify_broker_listing order_id={lo.order_id}")
            continue
        if lo.filled_qty != bo.filled_qty:
            mismatches.append(
                ReconcileMismatch(
                    order_id=lo.order_id,
                    code="partial_fill_mismatch",
                    message=f"filled local={lo.filled_qty} broker={bo.filled_qty}",
                )
            )
            actions.append(f"mock_action: resync_fills order_id={lo.order_id}")
        if lo.status != bo.status:
            mismatches.append(
                ReconcileMismatch(
                    order_id=lo.order_id,
                    code="status_mismatch",
                    message=f"status local={lo.status} broker={bo.status}",
                )
            )
            actions.append(f"mock_action: reconcile_status order_id={lo.order_id}")

    l_ids = {o.order_id for o in local}
    for bo in broker:
        if bo.order_id not in l_ids:
            mismatches.append(
                ReconcileMismatch(
                    order_id=bo.order_id,
                    code="ghost_broker_order",
                    message="broker order not in local intent",
                )
            )
            actions.append(f"mock_action: ingest_or_cancel_ghost order_id={bo.order_id}")

    return ReconcileReport(
        mismatches=tuple(mismatches),
        corrective_actions=tuple(actions),
        broker_signal=None,
    )


def cancel_race_mismatch(local_status: str, broker_status: str) -> Optional[ReconcileMismatch]:
    """Detect cancel vs open race: local cancelled but broker still open."""
    if local_status == "cancelled" and broker_status == "open":
        return ReconcileMismatch(
            order_id="(single)",
            code="cancel_race",
            message="local cancelled broker still open",
        )
    return None
