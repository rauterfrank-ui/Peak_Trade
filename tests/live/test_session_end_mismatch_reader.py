"""Unit tests for session_end_mismatch_reader (artifact-driven, read-only)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.experiments.live_session_registry import (
    STATUS_COMPLETED,
    STATUS_STARTED,
    LiveSessionRecord,
    register_live_session_run,
)
from src.live.session_end_mismatch_reader import (
    READER_SCHEMA_VERSION,
    RUNBOOK_TOKEN,
    build_session_end_mismatch_state,
)


def _stale() -> dict:
    return {
        "balance": "unknown",
        "position": "unknown",
        "order": "unknown",
        "exposure": "unknown",
        "summary": "unknown",
    }


def _bal_sem() -> dict:
    return {
        "balance_semantic_state": None,
        "balance_reason_code": None,
        "balance_operator_visible_state": None,
    }


def test_reader_no_artifacts(tmp_path: Path) -> None:
    out = build_session_end_mismatch_state(
        sessions_root=tmp_path / "missing_sessions",
        live_runs_root=tmp_path / "missing_lr",
        stale_state=_stale(),
        balance_semantics_state=_bal_sem(),
    )
    assert out["status"] == "unknown"
    assert out["summary"] == "no_signal"
    assert out["blocked_next_session"] is False
    assert out["data_source"] == "none"
    assert out["runbook"] == RUNBOOK_TOKEN
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION


def test_reader_registry_latest_started_mismatch(tmp_path: Path) -> None:
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    rec = LiveSessionRecord(
        session_id="sess_started",
        run_id=None,
        run_type="live_session_shadow",
        mode="shadow",
        env_name="env",
        symbol="BTC/EUR",
        status=STATUS_STARTED,
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    register_live_session_run(rec, base_dir=reg)
    out = build_session_end_mismatch_state(
        sessions_root=reg,
        live_runs_root=tmp_path / "live_runs",
        stale_state=_stale(),
        balance_semantics_state=_bal_sem(),
    )
    assert out["status"] == "mismatch_signal"
    assert out["summary"] == "registry_latest_session_not_terminal"
    assert out["blocked_next_session"] is True
    assert "live_session_registry" in out["data_source"]


def test_reader_registry_completed_aligned_no_live_runs(tmp_path: Path) -> None:
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 2, tzinfo=timezone.utc)
    rec = LiveSessionRecord(
        session_id="sess_done",
        run_id=None,
        run_type="live_session_shadow",
        mode="shadow",
        env_name="env",
        symbol="BTC/EUR",
        status=STATUS_COMPLETED,
        started_at=t0,
        finished_at=t1,
    )
    register_live_session_run(rec, base_dir=reg)
    out = build_session_end_mismatch_state(
        sessions_root=reg,
        live_runs_root=tmp_path / "live_runs",
        stale_state=_stale(),
        balance_semantics_state=_bal_sem(),
    )
    assert out["status"] == "aligned"
    assert out["blocked_next_session"] is False
    assert out["summary"] == "local_artifacts_consistent_for_closure_observation"


def test_reader_live_runs_only_with_ended_at_aligned(tmp_path: Path) -> None:
    lr = tmp_path / "live_runs"
    run_dir = lr / "20260101_shadow_s_BTC-EUR_1h"
    run_dir.mkdir(parents=True)
    meta = {
        "run_id": "20260101_shadow_s_BTC-EUR_1h",
        "mode": "shadow",
        "strategy_name": "s",
        "symbol": "BTC/EUR",
        "timeframe": "1h",
        "started_at": "2026-01-01T00:00:00+00:00",
        "ended_at": "2026-01-01T12:00:00+00:00",
    }
    (run_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    out = build_session_end_mismatch_state(
        sessions_root=tmp_path / "no_reg",
        live_runs_root=lr,
        stale_state=_stale(),
        balance_semantics_state=_bal_sem(),
    )
    assert out["status"] == "aligned"
    assert "live_runs" in out["data_source"]
    assert out["blocked_next_session"] is False


def test_reader_live_runs_missing_ended_at_ambiguous(tmp_path: Path) -> None:
    lr = tmp_path / "live_runs"
    run_dir = lr / "run_open"
    run_dir.mkdir(parents=True)
    meta = {
        "run_id": "run_open",
        "mode": "shadow",
        "strategy_name": "s",
        "symbol": "BTC/EUR",
        "timeframe": "1h",
        "started_at": "2026-01-01T00:00:00+00:00",
    }
    (run_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    out = build_session_end_mismatch_state(
        sessions_root=tmp_path / "no_reg",
        live_runs_root=lr,
        stale_state=_stale(),
        balance_semantics_state=_bal_sem(),
    )
    assert out["status"] == "ambiguous"
    assert out["blocked_next_session"] is True
    assert out["summary"] == "live_runs_latest_run_missing_ended_at_in_metadata"
