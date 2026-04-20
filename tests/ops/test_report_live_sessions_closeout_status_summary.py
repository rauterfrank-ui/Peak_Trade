"""
Tests for scripts/report_live_sessions.py --bounded-pilot-closeout-status-summary (read-only).
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
    mode: str = "bounded_pilot",
    started_at: Optional[datetime] = None,
) -> LiveSessionRecord:
    now = started_at or datetime.utcnow()
    return LiveSessionRecord(
        session_id=session_id,
        run_id="run_co",
        run_type="live_session_live",
        mode=mode,
        env_name="pilot_env",
        symbol="BTC/USDT",
        status=status,
        started_at=now,
        finished_at=None if status == "started" else now + timedelta(minutes=1),
        config={},
        metrics={},
        cli_args=[],
    )


def test_closeout_summary_terminal_completed_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(
        _rec(session_id="bp_done", status="completed", started_at=datetime(2024, 6, 1, 12, 0, 0)),
        base_dir=reg,
    )

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

    data = json.loads(capsys.readouterr().out)
    assert data["contract"] == "report_live_sessions.bounded_pilot_closeout_status_summary"
    assert "disclaimer" in data
    assert "abort_triage_hints" in data
    hints = data["abort_triage_hints"]
    assert len(hints) == 1
    assert "not live authorization" in hints[0]["disclaimer"].lower()
    assert hints[0]["primary_runbook"].endswith("RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md")
    co = data["closeout"]
    assert co["primary_session_id"] == "bp_done"
    assert co["closeout_signal_summary"] == "REGISTRY_TERMINAL_IN_NEWEST_ARTIFACT"
    assert co["registry_terminal_in_newest_artifact"] is True
    assert co["open_vs_terminal_artifact_conflict"] is False
    assert co["newest_registry_status"] == "completed"
    assert len(co["registry_bounded_pilot_artifacts_for_session"]) == 1


def test_closeout_summary_open_started_non_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_old", status="completed"), base_dir=reg)
    register_live_session_run(_rec(session_id="bp_open", status="started"), base_dir=reg)

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

    data = json.loads(capsys.readouterr().out)
    assert data["session_focus"]["primary_session_id"] == "bp_open"
    hints = data["abort_triage_hints"]
    assert len(hints) == 1
    assert hints[0]["primary_runbook"].endswith("RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md")
    assert "stale state is unresolved" in hints[0]["section_5_keywords"]
    co = data["closeout"]
    assert co["closeout_signal_summary"] == "REGISTRY_NON_TERMINAL_NEWEST_ONLY"
    assert co["registry_terminal_in_newest_artifact"] is False
    assert co["open_vs_terminal_artifact_conflict"] is False


def test_closeout_summary_conflict_newest_started_older_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    sid = "bp_same"
    register_live_session_run(
        _rec(session_id=sid, status="completed", started_at=datetime(2024, 1, 1, 10, 0, 0)),
        base_dir=reg,
    )
    register_live_session_run(
        _rec(session_id=sid, status="started", started_at=datetime(2024, 6, 1, 10, 0, 0)),
        base_dir=reg,
    )

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

    data = json.loads(capsys.readouterr().out)
    co = data["closeout"]
    hints = data["abort_triage_hints"]
    assert len(hints) == 1
    assert hints[0]["primary_runbook"].endswith("RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md")
    assert "session-end mismatch is unresolved" in hints[0]["section_5_keywords"]
    assert co["primary_session_id"] == sid
    assert co["closeout_signal_summary"] == "AMBIGUOUS_NEWEST_STARTED_WITH_OLDER_TERMINAL"
    assert co["registry_terminal_in_newest_artifact"] is False
    assert co["any_terminal_artifact_exists"] is True
    assert co["open_vs_terminal_artifact_conflict"] is True
    assert len(co["registry_bounded_pilot_artifacts_for_session"]) == 2


def test_closeout_summary_execution_events_pointer_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_evt", status="completed"), base_dir=reg)

    ej = tmp_path / "out" / "ops" / "execution_events" / "sessions" / "bp_evt"
    ej.mkdir(parents=True)
    (ej / "execution_events.jsonl").write_text("{}\n", encoding="utf-8")

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

    data = json.loads(capsys.readouterr().out)
    assert data["abort_triage_hints"] == []
    assert data["closeout"]["execution_events_jsonl_present"] is True
    assert data["closeout"]["pointers"]["execution_events_session_jsonl"]["present"] is True


def test_closeout_summary_empty_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reports" / "experiments" / "live_sessions").mkdir(parents=True)

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

    data = json.loads(capsys.readouterr().out)
    assert data["closeout"]["closeout_signal_summary"] == "NO_BOUNDED_PILOT_SESSION_IN_REGISTRY"
    assert data["closeout"]["primary_session_id"] is None
    hints = data["abort_triage_hints"]
    assert len(hints) == 1
    assert "ABORT_TRIAGE_COMPASS" in hints[0]["primary_runbook"]


def test_closeout_summary_text_stable_keywords(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_txt", status="failed"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-closeout-status-summary",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    out = capsys.readouterr().out
    assert "closeout_signal_summary:" in out
    assert "REGISTRY_TERMINAL_IN_NEWEST_ARTIFACT" in out
    assert "bp_txt" in out
    assert "abort triage hints" in out.lower()


def test_closeout_summary_conflicts_with_readiness(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-closeout-status-summary",
            "--bounded-pilot-readiness-summary",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "only one" in capsys.readouterr().err.lower()


def test_closeout_summary_rejects_config_path(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-closeout-status-summary",
            "--config-path",
            "/nope.toml",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "config-path" in capsys.readouterr().err.lower()


def test_closeout_summary_registry_base_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    alt = tmp_path / "alt_registry"
    alt.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_alt", status="aborted"), base_dir=alt)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-closeout-status-summary",
            "--json",
            "--registry-base",
            str(alt),
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["registry_dir"] == str(alt)
    assert data["closeout"]["primary_session_id"] == "bp_alt"
    assert data["closeout"]["newest_registry_status"] == "aborted"
