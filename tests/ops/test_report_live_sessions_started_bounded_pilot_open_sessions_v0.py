"""
Characterization tests for started bounded-pilot open-session reports (read-only).

Uses only synthetic registries under tmp_path and out/ops execution_event stubs — never
the repository's real reports/experiments/live_sessions or real out/ops.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.experiments.live_session_registry import LiveSessionRecord, register_live_session_run  # noqa: E402


def _rec(
    *,
    session_id: str,
    status: str,
    started_at: Optional[datetime] = None,
) -> LiveSessionRecord:
    now = started_at or datetime(2026, 3, 19, 12, 0, 0)
    return LiveSessionRecord(
        session_id=session_id,
        run_id="run_v0",
        run_type="live_session_live",
        mode="bounded_pilot",
        env_name="pilot_env",
        symbol="BTC/USDT",
        status=status,
        started_at=now,
        finished_at=None if status == "started" else now + timedelta(minutes=1),
        config={},
        metrics={},
        cli_args=[],
    )


def _write_session_exec_jsonl(tmp_path: Path, session_id: str) -> Path:
    p = (
        tmp_path
        / "out"
        / "ops"
        / "execution_events"
        / "sessions"
        / session_id
        / "execution_events.jsonl"
    )
    p.parent.mkdir(parents=True)
    p.write_text(
        '{"event_type": "order_submit", "session_id": "%s"}\n' % session_id, encoding="utf-8"
    )
    return p


def test_open_sessions_bounded_pilot_json_exec_jsonl_present_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Two started bounded_pilot rows: exec JSONL only for one -> present true vs false."""
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    t0 = datetime(2026, 3, 19, 15, 14, 0)
    register_live_session_run(
        _rec(session_id="session_with_events", status="started", started_at=t0),
        base_dir=reg,
    )
    register_live_session_run(
        _rec(
            session_id="session_no_events",
            status="started",
            started_at=t0 + timedelta(minutes=6),
        ),
        base_dir=reg,
    )
    _write_session_exec_jsonl(tmp_path, "session_with_events")

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--open-sessions",
            "--bounded-pilot-only",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["contract"] == "report_live_sessions.open_sessions"
    assert data["count"] == 2
    by_id = {row["session_id"]: row for row in data["sessions"]}
    assert by_id["session_with_events"]["execution_events_session_jsonl"]["present"] is True
    assert by_id["session_no_events"]["execution_events_session_jsonl"]["present"] is False
    for row in data["sessions"]:
        assert row["registry_status"] == "started"
        assert row["closeout_note"] is not None
        assert "live authorization" not in row["closeout_note"].lower()


def test_open_sessions_json_omits_common_authority_claims(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(
        _rec(session_id="bp_only", status="started"),
        base_dir=reg,
    )
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--open-sessions",
            "--bounded-pilot-only",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0
    low = capsys.readouterr().out.lower()
    for phrase in (
        "live authorization granted",
        "signoff complete",
        "autonomous-ready",
        "externally-authorized",
        "go/no-go: go",
    ):
        assert phrase not in low


def test_closeout_and_lifecycle_non_terminal_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Shape aligned with real runs: non-terminal closeout + partial lifecycle, no go-live claims in JSON body."""
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_x", status="started"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-closeout-status-summary",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0
    out_co = capsys.readouterr().out
    co = json.loads(out_co)
    assert co["closeout"]["closeout_signal_summary"] == "REGISTRY_NON_TERMINAL_NEWEST_ONLY"
    assert "not live authorization" in out_co.lower()

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-lifecycle-consistency",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0
    life = json.loads(capsys.readouterr().out)
    assert life["lifecycle_consistency"]["lifecycle_consistency_summary"] == (
        "PARTIAL_NON_TERMINAL_REGISTRY_OPEN_OR_STARTED"
    )
    life_s = json.dumps(life).lower()
    assert "not live authorization" in life_s
