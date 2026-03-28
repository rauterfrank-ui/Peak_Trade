from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.execution.contracts import OrderSide
from src.execution.orchestrator import ExecutionMode, ExecutionOrchestrator, OrderIntent
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter


def _read_jsonl(path: Path) -> list[dict]:
    lines = []
    if not path.exists():
        return lines
    for raw in path.read_text().splitlines():
        if raw.strip():
            lines.append(json.loads(raw))
    return lines


def test_reject_bad_qty_emits_validation_reject(tmp_path: Path):
    log_path = tmp_path / "execution_events.jsonl"
    orch = ExecutionOrchestrator(
        adapter=SimulatedVenueAdapter(),
        execution_mode=ExecutionMode.PAPER,
        execution_events_log_path=str(log_path),
    )

    intent = OrderIntent(
        run_id="run_001",
        session_id="sess_001",
        intent_id="intent_bad_qty",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0"),
    )

    res = orch.submit_intent(intent)
    assert res.success is False

    events = _read_jsonl(log_path)
    assert [e["event_type"] for e in events] == ["INTENT", "VALIDATION_REJECT"]
    assert events[1]["reason_code"] == "VALIDATION_REJECT_BAD_QTY"


def test_reject_kill_switch_emits_risk_reject(tmp_path: Path):
    log_path = tmp_path / "execution_events.jsonl"
    orch = ExecutionOrchestrator(
        adapter=SimulatedVenueAdapter(),
        execution_mode=ExecutionMode.PAPER,
        execution_events_log_path=str(log_path),
        kill_switch_active=True,
    )

    intent = OrderIntent(
        run_id="run_001",
        session_id="sess_001",
        intent_id="intent_kill",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
    )

    res = orch.submit_intent(intent)
    assert res.success is False

    events = _read_jsonl(log_path)
    assert [e["event_type"] for e in events] == ["INTENT", "RISK_REJECT"]
    assert events[1]["reason_code"] == "RISK_REJECT_KILL_SWITCH"


def test_reject_kill_switch_from_state_file_without_explicit_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Orchestrator blocks when state file says KILLED even if kill_switch_active is False."""
    log_path = tmp_path / "execution_events.jsonl"
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"state": "KILLED"}), encoding="utf-8")
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(state_file))
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)

    orch = ExecutionOrchestrator(
        adapter=SimulatedVenueAdapter(),
        execution_mode=ExecutionMode.PAPER,
        execution_events_log_path=str(log_path),
        kill_switch_active=False,
    )

    intent = OrderIntent(
        run_id="run_001",
        session_id="sess_001",
        intent_id="intent_kill_file",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.01"),
    )

    res = orch.submit_intent(intent)
    assert res.success is False

    events = _read_jsonl(log_path)
    assert [e["event_type"] for e in events] == ["INTENT", "RISK_REJECT"]
    assert events[1]["reason_code"] == "RISK_REJECT_KILL_SWITCH"


def test_reject_max_position_emits_risk_reject(tmp_path: Path):
    log_path = tmp_path / "execution_events.jsonl"
    orch = ExecutionOrchestrator(
        adapter=SimulatedVenueAdapter(),
        execution_mode=ExecutionMode.PAPER,
        execution_events_log_path=str(log_path),
        max_position_qty=Decimal("0.005"),
    )

    intent = OrderIntent(
        run_id="run_001",
        session_id="sess_001",
        intent_id="intent_maxpos",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.010"),
    )

    res = orch.submit_intent(intent)
    assert res.success is False

    events = _read_jsonl(log_path)
    assert [e["event_type"] for e in events] == ["INTENT", "RISK_REJECT"]
    assert events[1]["reason_code"] == "RISK_REJECT_MAX_POSITION"
