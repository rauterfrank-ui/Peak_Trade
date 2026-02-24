"""Unit tests for execution_events logger (enabled/disabled/out-guard)."""

import json
from pathlib import Path

import pytest

from src.observability.execution_events import emit


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
