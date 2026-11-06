from __future__ import annotations

from pathlib import Path

import pytest


def _read_lines(p: Path) -> list[str]:
    if not p.exists():
        return []
    return [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_prbj_heartbeat_throttle_writes_under_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange: out-only path (execution_events guard requires path under cwd/out)
    monkeypatch.chdir(tmp_path)
    out_dir = tmp_path / "out" / "ops" / "execution_events"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "execution_events.jsonl"

    monkeypatch.setenv("PT_EXEC_EVENTS_ENABLED", "true")
    monkeypatch.setenv("PT_EXEC_MODE", "testnet")
    monkeypatch.setenv("PT_EXEC_EVENTS_JSONL_PATH", str(jsonl_path))

    # Import after env is set (so helper uses same emit module env)
    from scripts.run_testnet_session import _maybe_emit_heartbeat

    # Act: throttle=30s, simulate time
    last = 0.0
    last = _maybe_emit_heartbeat(now_ts=10.0, last_ts=last, throttle_s=30, symbol="BTC/EUR")
    last = _maybe_emit_heartbeat(now_ts=20.0, last_ts=last, throttle_s=30, symbol="BTC/EUR")
    last = _maybe_emit_heartbeat(now_ts=40.0, last_ts=last, throttle_s=30, symbol="BTC/EUR")

    # Assert: exactly 1 line written (at t=40)
    lines = _read_lines(jsonl_path)
    assert len(lines) == 1
    assert '"event_type": "market_tick"' in lines[0]
    assert '"mode": "testnet"' in lines[0]
