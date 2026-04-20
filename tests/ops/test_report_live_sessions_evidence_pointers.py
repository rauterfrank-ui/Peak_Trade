"""
Tests for scripts/report_live_sessions.py --evidence-pointers (read-only).
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

from src.experiments.live_session_registry import (  # noqa: E402
    LiveSessionRecord,
    find_live_session_registry_json_for_session_id,
    register_live_session_run,
)


def _sample_record(
    *,
    session_id: str,
    mode: str = "bounded_pilot",
    started_at: Optional[datetime] = None,
) -> LiveSessionRecord:
    now = started_at or datetime.utcnow()
    return LiveSessionRecord(
        session_id=session_id,
        run_id="run_ev_test",
        run_type="live_session_live",
        mode=mode,
        env_name="pilot_env",
        symbol="BTC/USDT",
        status="completed",
        started_at=now,
        finished_at=now + timedelta(minutes=1),
        config={"strategy_name": "test"},
        metrics={"realized_pnl": 0.0},
        cli_args=["python", "scripts/run_execution_session.py", "--mode", "bounded_pilot"],
    )


def test_find_registry_newest_when_duplicate_session_id(tmp_path: Path) -> None:
    reg = tmp_path / "live_sessions"
    reg.mkdir()
    older = _sample_record(session_id="dup", started_at=datetime(2025, 1, 1, 12, 0, 0))
    newer = _sample_record(session_id="dup", started_at=datetime(2026, 1, 1, 12, 0, 0))
    register_live_session_run(older, base_dir=reg)
    register_live_session_run(newer, base_dir=reg)
    found = find_live_session_registry_json_for_session_id("dup", base_dir=reg)
    assert found is not None
    rec, path = found
    assert rec.session_id == "dup"
    assert "20260101" in path.name


def test_evidence_pointers_text_success_missing_exec_jsonl(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    rec = _sample_record(session_id="sess_ptr_1")
    register_live_session_run(rec, base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--evidence-pointers",
            "--session-id",
            "sess_ptr_1",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    out = capsys.readouterr().out
    assert "sess_ptr_1" in out
    assert "run_ev_test" in out
    assert "bounded_pilot" in out
    assert "present: no" in out


def test_evidence_pointers_json_stable_and_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    rec = _sample_record(session_id="sess_json_1")
    register_live_session_run(rec, base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--evidence-pointers",
            "--session-id",
            "sess_json_1",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["contract"] == "report_live_sessions.evidence_pointers"
    assert payload["session_id"] == "sess_json_1"
    assert payload["execution_events_session_jsonl"]["present"] is False
    assert "out/ops/execution_events/sessions/" in payload["execution_events_session_jsonl"]["path"]


def test_evidence_pointers_unknown_session_nonzero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--evidence-pointers",
            "--session-id",
            "does_not_exist",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 1

    err = capsys.readouterr().err
    assert "does_not_exist" in err
    assert "no live session registry entry" in err


def test_evidence_pointers_exec_jsonl_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    sid = "sess_with_exec"
    rec = _sample_record(session_id=sid)
    register_live_session_run(rec, base_dir=reg)

    exec_path = (
        tmp_path / "out" / "ops" / "execution_events" / "sessions" / sid / "execution_events.jsonl"
    )
    exec_path.parent.mkdir(parents=True)
    exec_path.write_text("{}\n", encoding="utf-8")

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--evidence-pointers",
            "--session-id",
            sid,
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    assert "present: yes" in capsys.readouterr().out


def test_evidence_pointers_latest_bounded_pilot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    t0 = datetime(2026, 2, 1, 10, 0, 0)
    shadow = _sample_record(
        session_id="newer_shadow", mode="shadow", started_at=t0 + timedelta(hours=1)
    )
    pilot = _sample_record(session_id="want_this", mode="bounded_pilot", started_at=t0)
    register_live_session_run(pilot, base_dir=reg)
    register_live_session_run(shadow, base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--evidence-pointers",
            "--latest-bounded-pilot",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    out = capsys.readouterr().out
    assert "want_this" in out
    assert "newer_shadow" not in out


def test_evidence_pointers_usage_both_selectors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--evidence-pointers",
            "--session-id",
            "a",
            "--latest-bounded-pilot",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "not both" in capsys.readouterr().err


def test_evidence_pointers_usage_missing_selector(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--evidence-pointers",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "requires" in capsys.readouterr().err


def test_expected_session_scoped_path_matches_observable_convention() -> None:
    from src.observability.execution_events import expected_session_scoped_events_jsonl_path

    p = expected_session_scoped_events_jsonl_path("a/b:c d")
    assert p.parts[-3:] == ("sessions", "a_b_c_d", "execution_events.jsonl")
