from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest

from src.execution.live.orchestrator import DryrunConfig, LiveSessionOrchestrator
from src.execution.live.state import SessionStatus


@dataclass
class FixedClock:
    dt: datetime

    def now(self) -> datetime:
        return self.dt


class FlakySink:
    def __init__(self, *, fail_first: int = 0, fail_always: bool = False) -> None:
        self._fail_first = fail_first
        self._fail_always = fail_always
        self.writes: list[str] = []

    def write(self, line: str) -> None:
        if self._fail_always:
            raise RuntimeError("sink is down")
        if self._fail_first > 0:
            self._fail_first -= 1
            raise RuntimeError("transient sink error")
        self.writes.append(line)


@pytest.fixture(autouse=True)
def _no_live_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    # Guard against accidental real sleeps.
    monkeypatch.setattr(
        time,
        "sleep",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("sleep called")),
    )

    # Guard against accidental network usage.
    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network called")),
    )
    monkeypatch.setattr(
        socket.socket,
        "connect",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network called")),
        raising=True,
    )


def _parse_jsonl(lines: list[str]) -> list[dict[str, Any]]:
    return [json.loads(line) for line in lines]


def test_orchestrator_dryrun_happy_path_is_deterministic() -> None:
    orch = LiveSessionOrchestrator()
    clock = FixedClock(datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc))

    cfg = DryrunConfig(
        strategy_id="strat_demo",
        run_id="run_demo_001",
        seed=123,
        clock_mode="fixed",
        max_sink_retries=0,
        strategy_allowlist=["strat_demo"],
    )

    events1: list[str] = []
    states1: list[str] = []
    metrics1: list[str] = []
    audit1: list[str] = []
    res1 = orch.run_dryrun(
        cfg,
        clock=clock,
        event_sink=events1,
        state_sink=states1,
        metrics_sink=metrics1,
        audit_sink=audit1,
    )

    assert res1.accepted is True
    assert res1.status == SessionStatus.COMPLETED
    assert len(events1) == 3
    assert len(states1) == 3
    assert len(metrics1) == 1
    assert len(audit1) >= 2

    ev_objs = _parse_jsonl(events1)
    assert [e["event_type"] for e in ev_objs] == ["SESSION_START", "STRATEGY_TICK", "SESSION_STOP"]
    assert [e["ts_sim"] for e in ev_objs] == [0, 1, 2]

    # Run again; outputs must match exactly.
    events2: list[str] = []
    states2: list[str] = []
    metrics2: list[str] = []
    audit2: list[str] = []
    res2 = orch.run_dryrun(
        cfg,
        clock=clock,
        event_sink=events2,
        state_sink=states2,
        metrics_sink=metrics2,
        audit_sink=audit2,
    )
    assert res2.status == SessionStatus.COMPLETED
    assert events2 == events1
    assert states2 == states1
    assert metrics2 == metrics1
    assert audit2 == audit1


def test_orchestrator_dryrun_rejects_missing_strategy_id() -> None:
    orch = LiveSessionOrchestrator()
    clock = FixedClock(datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc))

    cfg = DryrunConfig(
        strategy_id="",
        run_id="run_demo_002",
        seed=1,
        max_sink_retries=0,
    )

    events: list[str] = []
    states: list[str] = []
    metrics: list[str] = []
    audit: list[str] = []
    res = orch.run_dryrun(
        cfg,
        clock=clock,
        event_sink=events,
        state_sink=states,
        metrics_sink=metrics,
        audit_sink=audit,
    )

    assert res.accepted is False
    assert res.status == SessionStatus.REJECTED
    assert res.reject_code == "C2_REJECT_MISSING_STRATEGY_ID"
    assert len(events) == 1
    assert _parse_jsonl(events)[0]["event_type"] == "REJECTED"


def test_orchestrator_dryrun_bounded_retry_on_sink_failure_no_real_sleep() -> None:
    orch = LiveSessionOrchestrator()
    clock = FixedClock(datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc))

    cfg = DryrunConfig(
        strategy_id="strat_demo",
        run_id="run_demo_003",
        seed=7,
        max_sink_retries=2,
        strategy_allowlist=["strat_demo"],
    )

    calls: list[float] = []
    sink = FlakySink(fail_first=1)
    audit: list[str] = []
    res = orch.run_dryrun(
        cfg,
        clock=clock,
        event_sink=sink,
        state_sink=[],
        metrics_sink=[],
        audit_sink=audit,
        sleep_fn=lambda seconds: calls.append(seconds),
    )

    assert res.status == SessionStatus.COMPLETED
    assert len(calls) == 1  # injected, but still no time.sleep usage
    assert any(json.loads(line)["code"] == "C2_SINK_WRITE_RETRY" for line in audit)


def test_orchestrator_dryrun_aborts_when_sink_permanently_fails() -> None:
    orch = LiveSessionOrchestrator()
    clock = FixedClock(datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc))

    cfg = DryrunConfig(
        strategy_id="strat_demo",
        run_id="run_demo_004",
        seed=7,
        max_sink_retries=1,
        strategy_allowlist=["strat_demo"],
    )

    sink = FlakySink(fail_always=True)
    audit: list[str] = []
    res = orch.run_dryrun(
        cfg,
        clock=clock,
        event_sink=sink,
        state_sink=[],
        metrics_sink=[],
        audit_sink=audit,
    )

    assert res.status == SessionStatus.FAILED
    assert res.fail_code == "C2_ABORT_SINK_WRITE_FAILED"
    assert any(json.loads(line)["code"] == "C2_SINK_WRITE_FAILED" for line in audit)
