"""
ExecutionPipeline (v0 MVP) — Order Execution Pipeline.

Key properties:
- deterministic: injected time provider, no sleeps
- governance-safe: adapters are NO-LIVE
- telemetry-first: emits stable v0 events for watch-only UI
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

from .adapter import ExecutionAdapter, NullExecutionAdapter, SubmitRequest
from .contracts import ExecutionContext, ExecutionError, ExecutionPlan, ExecutionResult, OrderPlan
from .events_v0 import ExecutionEventV0
from .policies import IdempotencyKey
from .telemetry import NullTelemetryEmitter, TelemetryEmitter

TimeProvider = Callable[[], datetime]


@dataclass(frozen=True)
class ExecutionPipelineConfig:
    telemetry_enabled: bool = True


class ExecutionPipeline:
    def __init__(
        self,
        *,
        adapter: Optional[ExecutionAdapter] = None,
        emitter: Optional[TelemetryEmitter] = None,
        now: Optional[TimeProvider] = None,
        config: Optional[ExecutionPipelineConfig] = None,
    ) -> None:
        self._adapter: ExecutionAdapter = adapter or NullExecutionAdapter()
        self._emitter: TelemetryEmitter = emitter or NullTelemetryEmitter()
        self._now: TimeProvider = now or datetime.utcnow
        self._config = config or ExecutionPipelineConfig()

    def _emit(self, event: ExecutionEventV0) -> None:
        if not self._config.telemetry_enabled:
            return
        self._emitter.emit(event)

    def new_context(
        self,
        *,
        idempotency_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
        run_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> ExecutionContext:
        rid = run_id or uuid.uuid4().hex
        cid = correlation_id or f"corr_{uuid.uuid4().hex}"
        idem = IdempotencyKey(idempotency_key or f"idem_{uuid.uuid4().hex}")
        ca = created_at or self._now()
        return ExecutionContext(run_id=rid, correlation_id=cid, idempotency_key=idem, created_at=ca)

    def execute(self, plan: ExecutionPlan, *, ctx: ExecutionContext) -> ExecutionResult:
        start = self._now()
        deadline = start + timedelta(seconds=float(plan.timeout.deadline_seconds))

        self._emit(
            ExecutionEventV0(
                ts=start,
                run_id=ctx.run_id,
                correlation_id=ctx.correlation_id,
                idempotency_key=ctx.idempotency_key.value,
                event_type="created",
                payload={"n_orders": len(plan.orders)},
            )
        )

        err = self._validate_plan(plan)
        if err is not None:
            self._emit(
                ExecutionEventV0(
                    ts=self._now(),
                    run_id=ctx.run_id,
                    correlation_id=ctx.correlation_id,
                    idempotency_key=ctx.idempotency_key.value,
                    event_type="failed",
                    payload={"final": True, "error": err.error_code, "message": err.message},
                )
            )
            return ExecutionResult(
                run_id=ctx.run_id,
                correlation_id=ctx.correlation_id,
                status="failed",
                orders=[],
                error=err,
            )

        self._emit(
            ExecutionEventV0(
                ts=self._now(),
                run_id=ctx.run_id,
                correlation_id=ctx.correlation_id,
                idempotency_key=ctx.idempotency_key.value,
                event_type="validated",
                payload={"ok": True},
            )
        )

        orders_out: list[Dict[str, Any]] = []
        for op in plan.orders:
            if self._now() > deadline:
                terr = ExecutionError(
                    error_code="timeout",
                    message="execution_run_timeout_exceeded",
                    details={"deadline_seconds": plan.timeout.deadline_seconds},
                )
                self._emit(
                    ExecutionEventV0(
                        ts=self._now(),
                        run_id=ctx.run_id,
                        correlation_id=ctx.correlation_id,
                        order_id=op.order_id,
                        idempotency_key=ctx.idempotency_key.value,
                        event_type="failed",
                        payload={"final": True, "error": terr.error_code, "message": terr.message},
                    )
                )
                return ExecutionResult(
                    run_id=ctx.run_id,
                    correlation_id=ctx.correlation_id,
                    status="failed",
                    orders=orders_out,
                    error=terr,
                )

            order_res = self._execute_one(op, plan=plan, ctx=ctx)
            orders_out.append(order_res)
            if order_res.get("status") in ("failed", "canceled"):
                status = "canceled" if order_res.get("status") == "canceled" else "failed"
                err_obj = order_res.get("error")
                err = (
                    ExecutionError(
                        error_code=str(err_obj.get("error_code") or "failed"),
                        message=str(err_obj.get("message") or "order_failed"),
                        details=dict(err_obj.get("details") or {}),
                    )
                    if isinstance(err_obj, dict)
                    else None
                )
                return ExecutionResult(
                    run_id=ctx.run_id,
                    correlation_id=ctx.correlation_id,
                    status=status,
                    orders=orders_out,
                    error=err,
                )

        return ExecutionResult(
            run_id=ctx.run_id,
            correlation_id=ctx.correlation_id,
            status="success",
            orders=orders_out,
            error=None,
        )

    def _validate_plan(self, plan: ExecutionPlan) -> Optional[ExecutionError]:
        if plan.orders is None:
            return ExecutionError(error_code="invalid_plan", message="orders_missing")
        if len(plan.orders) == 0:
            return ExecutionError(error_code="invalid_plan", message="orders_empty")
        for o in plan.orders:
            if not o.order_id:
                return ExecutionError(error_code="invalid_order", message="order_id_missing")
            if not o.symbol:
                return ExecutionError(
                    error_code="invalid_order",
                    message="symbol_missing",
                    details={"order_id": o.order_id},
                )
            if o.side not in ("buy", "sell"):
                return ExecutionError(
                    error_code="invalid_order",
                    message="side_invalid",
                    details={"order_id": o.order_id, "side": o.side},
                )
            if o.quantity <= 0:
                return ExecutionError(
                    error_code="invalid_order",
                    message="quantity_invalid",
                    details={"order_id": o.order_id, "quantity": o.quantity},
                )
        return None

    def _execute_one(
        self, op: OrderPlan, *, plan: ExecutionPlan, ctx: ExecutionContext
    ) -> Dict[str, Any]:
        for attempt in range(1, int(plan.retry.max_attempts) + 1):
            req = SubmitRequest(
                run_id=ctx.run_id,
                correlation_id=ctx.correlation_id,
                order_id=op.order_id,
                symbol=op.symbol,
                side=op.side,
                quantity=op.quantity,
                idempotency_key=f"{ctx.idempotency_key.value}:{op.order_id}",
                meta=dict(op.meta),
            )

            self._emit(
                ExecutionEventV0(
                    ts=self._now(),
                    run_id=ctx.run_id,
                    correlation_id=ctx.correlation_id,
                    order_id=op.order_id,
                    idempotency_key=req.idempotency_key,
                    event_type="submitted",
                    payload={
                        "attempt": attempt,
                        "symbol": op.symbol,
                        "side": op.side,
                        "quantity": op.quantity,
                    },
                )
            )

            ack = self._adapter.submit(req)
            if not ack.accepted:
                self._emit(
                    ExecutionEventV0(
                        ts=self._now(),
                        run_id=ctx.run_id,
                        correlation_id=ctx.correlation_id,
                        order_id=op.order_id,
                        idempotency_key=req.idempotency_key,
                        event_type="failed",
                        payload={
                            "final": attempt >= plan.retry.max_attempts,
                            "attempt": attempt,
                            "reason": ack.reason or "rejected",
                        },
                    )
                )
                if attempt >= plan.retry.max_attempts:
                    return {
                        "order_id": op.order_id,
                        "status": "failed",
                        "error": {
                            "error_code": "submit_rejected",
                            "message": ack.reason or "rejected",
                            "details": {"attempt": attempt},
                        },
                    }
                continue

            self._emit(
                ExecutionEventV0(
                    ts=self._now(),
                    run_id=ctx.run_id,
                    correlation_id=ctx.correlation_id,
                    order_id=op.order_id,
                    idempotency_key=req.idempotency_key,
                    event_type="acked",
                    payload={"attempt": attempt, "venue_order_id": ack.venue_order_id},
                )
            )

            st = self._adapter.status(
                run_id=ctx.run_id, correlation_id=ctx.correlation_id, order_id=ack.order_id
            )
            if st.state == "filled":
                self._emit(
                    ExecutionEventV0(
                        ts=self._now(),
                        run_id=ctx.run_id,
                        correlation_id=ctx.correlation_id,
                        order_id=op.order_id,
                        idempotency_key=req.idempotency_key,
                        event_type="filled",
                        payload={"fill": st.fill or {}},
                    )
                )
                return {"order_id": op.order_id, "status": "filled", "fill": st.fill or {}}

            if st.state == "canceled":
                self._emit(
                    ExecutionEventV0(
                        ts=self._now(),
                        run_id=ctx.run_id,
                        correlation_id=ctx.correlation_id,
                        order_id=op.order_id,
                        idempotency_key=req.idempotency_key,
                        event_type="canceled",
                        payload={},
                    )
                )
                return {"order_id": op.order_id, "status": "canceled"}

            if st.state == "failed":
                self._emit(
                    ExecutionEventV0(
                        ts=self._now(),
                        run_id=ctx.run_id,
                        correlation_id=ctx.correlation_id,
                        order_id=op.order_id,
                        idempotency_key=req.idempotency_key,
                        event_type="failed",
                        payload={
                            "final": attempt >= plan.retry.max_attempts,
                            "attempt": attempt,
                            "error": st.error or {},
                        },
                    )
                )
                if attempt >= plan.retry.max_attempts:
                    return {
                        "order_id": op.order_id,
                        "status": "failed",
                        "error": {
                            "error_code": "status_failed",
                            "message": "adapter_status_failed",
                            "details": st.error or {},
                        },
                    }
                continue

            # Still acked/pending -> MVP treats as failure deterministically (no waits)
            self._emit(
                ExecutionEventV0(
                    ts=self._now(),
                    run_id=ctx.run_id,
                    correlation_id=ctx.correlation_id,
                    order_id=op.order_id,
                    idempotency_key=req.idempotency_key,
                    event_type="failed",
                    payload={
                        "final": attempt >= plan.retry.max_attempts,
                        "attempt": attempt,
                        "reason": f"unexpected_state:{st.state}",
                    },
                )
            )
            if attempt >= plan.retry.max_attempts:
                return {
                    "order_id": op.order_id,
                    "status": "failed",
                    "error": {
                        "error_code": "unexpected_state",
                        "message": f"unexpected_state:{st.state}",
                        "details": {"state": st.state},
                    },
                }

        return {
            "order_id": op.order_id,
            "status": "failed",
            "error": {"error_code": "unknown", "message": "exhausted", "details": {}},
        }
