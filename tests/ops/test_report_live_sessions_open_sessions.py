"""
Tests for scripts/report_live_sessions.py --open-sessions (read-only).
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


def _record(
    *,
    session_id: str,
    status: str,
    mode: str = "bounded_pilot",
    started_at: Optional[datetime] = None,
) -> LiveSessionRecord:
    now = started_at or datetime.utcnow()
    return LiveSessionRecord(
        session_id=session_id,
        run_id="run_open_test",
        run_type="live_session_live",
        mode=mode,
        env_name="pilot_env",
        symbol="BTC/USDT",
        status=status,
        started_at=now,
        finished_at=None if status == "started" else now + timedelta(minutes=1),
        config={"strategy_name": "test"},
        metrics={"realized_pnl": 0.0},
        cli_args=["python", "scripts/run_execution_session.py", "--mode", "bounded_pilot"],
    )


def test_open_sessions_lists_started_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_record(session_id="open_a", status="started"), base_dir=reg)
    register_live_session_run(_record(session_id="done_b", status="completed"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        ["report_live_sessions.py", "--open-sessions", "--log-level", "ERROR"],
    ):
        assert main() == 0

    out = capsys.readouterr().out
    assert "open_a" in out
    assert "OPEN" in out
    assert "done_b" not in out
    assert "registry_status=started" in out


def test_open_sessions_empty_stable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_record(session_id="done_only", status="completed"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        ["report_live_sessions.py", "--open-sessions", "--log-level", "ERROR"],
    ):
        assert main() == 0

    assert "none" in capsys.readouterr().out.lower()


def test_open_sessions_json_stable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_record(session_id="open_json", status="started"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        ["report_live_sessions.py", "--open-sessions", "--json", "--log-level", "ERROR"],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["contract"] == "report_live_sessions.open_sessions"
    assert data["count"] == 1
    assert data["sessions"][0]["session_id"] == "open_json"
    assert data["sessions"][0]["operator_lifecycle"] == "OPEN"
    assert data["sessions"][0]["closeout_note"] is not None


def test_open_sessions_latest_bounded_pilot_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    t0 = datetime(2026, 3, 1, 10, 0, 0)
    register_live_session_run(
        _record(session_id="older_bp", status="started", started_at=t0),
        base_dir=reg,
    )
    register_live_session_run(
        _record(session_id="newer_bp", status="started", started_at=t0 + timedelta(hours=2)),
        base_dir=reg,
    )

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--open-sessions",
            "--latest-bounded-pilot-open",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    out = capsys.readouterr().out
    assert "newer_bp" in out
    assert "older_bp" not in out


def test_open_sessions_bounded_pilot_only_excludes_shadow_started(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(
        _record(session_id="shadow_open", status="started", mode="shadow"),
        base_dir=reg,
    )
    register_live_session_run(
        _record(session_id="bp_open", status="started", mode="bounded_pilot"),
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
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    out = capsys.readouterr().out
    assert "bp_open" in out
    assert "shadow_open" not in out


def test_open_sessions_conflicts_with_evidence_pointers(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--open-sessions",
            "--evidence-pointers",
            "--session-id",
            "x",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "not both" in capsys.readouterr().err


def test_open_sessions_rejects_session_id_flag(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--open-sessions",
            "--session-id",
            "nope",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "session-id" in capsys.readouterr().err.lower()


def test_iter_live_session_registry_entries_yields_paths(tmp_path: Path) -> None:
    from src.experiments.live_session_registry import iter_live_session_registry_entries

    reg = tmp_path / "reg"
    reg.mkdir()
    register_live_session_run(_record(session_id="it1", status="started"), base_dir=reg)
    rows = list(iter_live_session_registry_entries(base_dir=reg))
    assert len(rows) == 1
    rec, path = rows[0]
    assert rec.session_id == "it1"
    assert path.name.endswith(".json")
