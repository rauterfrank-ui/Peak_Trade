from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from src.execution_pipeline import (
    ExecutionPipeline,
    ExecutionPlan,
    IdempotencyKey,
    InMemoryExecutionAdapter,
    OrderPlan,
    RetryPolicy,
    TimeoutPolicy,
)
from src.execution_pipeline.telemetry import JsonlTelemetryEmitter


def _read_jsonl(path: Path) -> list[dict]:
    out: list[dict] = []
    if not path.exists():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            out.append(json.loads(raw))
    return out


class StepClock:
    def __init__(self, start: datetime):
        self._t = start

    def __call__(self) -> datetime:
        self._t = self._t + timedelta(seconds=1)
        return self._t


def test_execution_pipeline_mvp_happy_path_emits_event_stream(tmp_path: Path) -> None:
    clock = StepClock(datetime(2026, 1, 1, 0, 0, 0))
    log = tmp_path / "execution_pipeline_events_v0.jsonl"

    adapter = InMemoryExecutionAdapter(fill_immediately=True)
    emitter = JsonlTelemetryEmitter(root=tmp_path, filename=log.name)
    pipe = ExecutionPipeline(adapter=adapter, emitter=emitter, now=clock)

    ctx = pipe.new_context(run_id="run_001", correlation_id="corr_001", idempotency_key="idem_001")
    plan = ExecutionPlan(
        orders=[OrderPlan(order_id="ord_001", symbol="BTC/EUR", side="buy", quantity=0.01)],
        retry=RetryPolicy(max_attempts=1),
        timeout=TimeoutPolicy(deadline_seconds=60.0),
    )

    res = pipe.execute(plan, ctx=ctx)
    assert res.status == "success"
    assert res.run_id == "run_001"

    events = _read_jsonl(log)
    assert [e["event_type"] for e in events] == [
        "created",
        "validated",
        "submitted",
        "acked",
        "filled",
    ]
    assert all(e["run_id"] == "run_001" for e in events)
    assert all(e["correlation_id"] == "corr_001" for e in events)


def test_execution_pipeline_mvp_retries_transient_reject(tmp_path: Path) -> None:
    clock = StepClock(datetime(2026, 1, 1, 0, 0, 0))
    log = tmp_path / "execution_pipeline_events_v0.jsonl"

    adapter = InMemoryExecutionAdapter(fill_immediately=True, fail_first_n_submits=1)
    emitter = JsonlTelemetryEmitter(root=tmp_path, filename=log.name)
    pipe = ExecutionPipeline(adapter=adapter, emitter=emitter, now=clock)

    ctx = pipe.new_context(run_id="run_002", correlation_id="corr_002", idempotency_key="idem_002")
    plan = ExecutionPlan(
        orders=[OrderPlan(order_id="ord_002", symbol="BTC/EUR", side="buy", quantity=0.01)],
        retry=RetryPolicy(max_attempts=2),
        timeout=TimeoutPolicy(deadline_seconds=60.0),
    )

    res = pipe.execute(plan, ctx=ctx)
    assert res.status == "success"

    events = _read_jsonl(log)
    assert [e["event_type"] for e in events] == [
        "created",
        "validated",
        "submitted",  # attempt 1
        "failed",  # attempt 1 (final=false)
        "submitted",  # attempt 2
        "acked",
        "filled",
    ]
    assert events[3]["payload"]["final"] is False


def test_execution_pipeline_mvp_timeout_fails_run(tmp_path: Path) -> None:
    clock = StepClock(datetime(2026, 1, 1, 0, 0, 0))
    log = tmp_path / "execution_pipeline_events_v0.jsonl"

    adapter = InMemoryExecutionAdapter(fill_immediately=True)
    emitter = JsonlTelemetryEmitter(root=tmp_path, filename=log.name)
    pipe = ExecutionPipeline(adapter=adapter, emitter=emitter, now=clock)

    ctx = pipe.new_context(run_id="run_003", correlation_id="corr_003", idempotency_key="idem_003")
    plan = ExecutionPlan(
        orders=[OrderPlan(order_id="ord_003", symbol="BTC/EUR", side="buy", quantity=0.01)],
        retry=RetryPolicy(max_attempts=1),
        timeout=TimeoutPolicy(deadline_seconds=0.0001),
    )

    res = pipe.execute(plan, ctx=ctx)
    assert res.status == "failed"
    assert res.error is not None
    assert res.error.error_code == "timeout"


def test_execution_pipeline_mvp_idempotency_prevents_duplicate_order_creation(
    tmp_path: Path,
) -> None:
    clock = StepClock(datetime(2026, 1, 1, 0, 0, 0))
    log = tmp_path / "execution_pipeline_events_v0.jsonl"

    adapter = InMemoryExecutionAdapter(fill_immediately=True)
    emitter = JsonlTelemetryEmitter(root=tmp_path, filename=log.name)
    pipe = ExecutionPipeline(adapter=adapter, emitter=emitter, now=clock)

    # Keep ctx stable across both calls
    ctx = pipe.new_context(
        run_id="run_004",
        correlation_id="corr_004",
        idempotency_key=IdempotencyKey("idem_004").value,
        created_at=datetime(2026, 1, 1, 0, 0, 0),
    )
    plan = ExecutionPlan(
        orders=[OrderPlan(order_id="ord_004", symbol="BTC/EUR", side="buy", quantity=0.01)],
        retry=RetryPolicy(max_attempts=1),
        timeout=TimeoutPolicy(deadline_seconds=60.0),
    )

    r1 = pipe.execute(plan, ctx=ctx)
    r2 = pipe.execute(plan, ctx=ctx)
    assert r1.status == "success"
    assert r2.status == "success"
    # InMemory adapter must not create a second distinct order entry for same idempotency key
    assert len(adapter._orders) == 1  # type: ignore[attr-defined]
