"""Unit tests for execution_events logger (enabled/disabled/out-guard/session-scoped)."""

import importlib.util
import json
import os
from pathlib import Path

import pytest

from src.observability.execution_events import (
    clear_session_context,
    emit,
    set_session_context,
)


def test_disabled_no_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir()
    monkeypatch.setenv("PT_EXEC_EVENTS_ENABLED", "false")
    emit(event_type="x", level="info")
    p = tmp_path / "out/ops/execution_events/execution_events.jsonl"
    assert not p.exists()


def test_enabled_writes_under_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir()
    monkeypatch.setenv("PT_EXEC_EVENTS_ENABLED", "true")
    monkeypatch.setenv("PT_EXEC_MODE", "testnet")
    monkeypatch.setenv(
        "PT_EXEC_EVENTS_JSONL_PATH", "out/ops/execution_events/execution_events.jsonl"
    )
    emit(event_type="order_submit", level="info", msg="hi")
    p = tmp_path / "out/ops/execution_events/execution_events.jsonl"
    assert p.exists()
    obj = json.loads(p.read_text(encoding="utf-8").splitlines()[0])
    assert obj["event_type"] == "order_submit"
    assert obj["mode"] == "testnet"


def test_refuses_outside_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir()
    monkeypatch.setenv("PT_EXEC_EVENTS_ENABLED", "true")
    monkeypatch.setenv("PT_EXEC_EVENTS_JSONL_PATH", "../evil.jsonl")
    with pytest.raises(ValueError, match="outside out"):
        emit(event_type="x", level="info")


def test_session_scoped_writes_to_session_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When set_session_context is active, events go to sessions/<session_id>/execution_events.jsonl."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir()
    monkeypatch.setenv("PT_EXEC_EVENTS_ENABLED", "true")
    monkeypatch.setenv("PT_EXEC_MODE", "bounded_pilot")

    set_session_context("session_20260315_abc123")
    try:
        emit(event_type="order_submit", level="info", msg="session-scoped")
    finally:
        clear_session_context()

    p = (
        tmp_path
        / "out/ops/execution_events/sessions/session_20260315_abc123/execution_events.jsonl"
    )
    assert p.exists()
    obj = json.loads(p.read_text(encoding="utf-8").splitlines()[0])
    assert obj["event_type"] == "order_submit"
    assert obj["session_id"] == "session_20260315_abc123"


def test_bounded_pilot_enables_execution_events(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_execution_session sets PT_EXEC_EVENTS_ENABLED=true for bounded_pilot mode."""
    monkeypatch.delenv("PT_EXEC_EVENTS_ENABLED", raising=False)
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "run_execution_session", root / "scripts" / "run_execution_session.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class Args:
        mode = "bounded_pilot"

    mod._ensure_bounded_pilot_events_enabled(Args())
    assert os.environ.get("PT_EXEC_EVENTS_ENABLED") == "true"


def test_shadow_mode_does_not_set_exec_events_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_execution_session does not set PT_EXEC_EVENTS_ENABLED for shadow mode."""
    monkeypatch.delenv("PT_EXEC_EVENTS_ENABLED", raising=False)
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "run_execution_session", root / "scripts" / "run_execution_session.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class Args:
        mode = "shadow"

    mod._ensure_bounded_pilot_events_enabled(Args())
    assert os.environ.get("PT_EXEC_EVENTS_ENABLED") is None
