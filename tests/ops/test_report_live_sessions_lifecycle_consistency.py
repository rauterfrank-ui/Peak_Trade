"""
Tests for scripts/report_live_sessions.py --bounded-pilot-lifecycle-consistency (read-only).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
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
        run_id="run_lc",
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


def test_lifecycle_minimal_fixture_partial_no_exec_jsonl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_done", status="completed"), base_dir=reg)

    from scripts.report_live_sessions import main

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

    data = json.loads(capsys.readouterr().out)
    assert data["contract"] == "report_live_sessions.bounded_pilot_lifecycle_consistency"
    lc = data["lifecycle_consistency"]
    assert lc["contract"] == "report_live_sessions.lifecycle_consistency_v1"
    assert lc["lifecycle_consistency_summary"] == "PARTIAL_TERMINAL_REGISTRY_WITHOUT_EXEC_JSONL"
    assert lc["partial_status"] is True
    assert "terminal_newest_artifact_but_execution_events_jsonl_missing" in lc["mismatch_signals"]
    assert data["closeout"]["execution_events_jsonl_present"] is False


def test_lifecycle_open_started_partial_no_terminal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_open", status="started"), base_dir=reg)

    from scripts.report_live_sessions import main

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

    data = json.loads(capsys.readouterr().out)
    lc = data["lifecycle_consistency"]
    assert lc["lifecycle_consistency_summary"] == "PARTIAL_NON_TERMINAL_REGISTRY_OPEN_OR_STARTED"
    assert lc["partial_status"] is True
    assert "newest_registry_artifact_non_terminal_only" in lc["mismatch_signals"]


def test_lifecycle_terminal_with_exec_aligned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_done", status="completed"), base_dir=reg)
    ej = tmp_path / "out" / "ops" / "execution_events" / "sessions" / "bp_done"
    ej.mkdir(parents=True)
    (ej / "execution_events.jsonl").write_text("{}\n", encoding="utf-8")

    from scripts.report_live_sessions import main

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

    data = json.loads(capsys.readouterr().out)
    lc = data["lifecycle_consistency"]
    assert lc["lifecycle_consistency_summary"] == "ALIGNED_TERMINAL_REGISTRY_WITH_EXEC_JSONL"
    assert lc["partial_status"] is False
    assert lc["mismatch_signals"] == []
    assert lc.get("abort_triage_hints") == []


def test_lifecycle_json_stable_sorted_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_sort", status="completed"), base_dir=reg)

    from scripts.report_live_sessions import main

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

    raw = capsys.readouterr().out
    parsed = json.loads(raw)
    assert json.dumps(parsed, indent=2, sort_keys=True) == raw.strip()


def test_lifecycle_conflicts_with_frontdoor(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-lifecycle-consistency",
            "--bounded-pilot-first-live-frontdoor",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "only one" in capsys.readouterr().err.lower()


def test_lifecycle_conflicts_run_type(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-lifecycle-consistency",
            "--run-type",
            "live_session_shadow",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "run-type" in capsys.readouterr().err.lower()


def test_lifecycle_abort_triage_hints_conflict_maps_session_end_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    sid = "bp_conflict"
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
            "--bounded-pilot-lifecycle-consistency",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    lc = data["lifecycle_consistency"]
    assert lc["lifecycle_consistency_summary"] == "REGISTRY_ARTIFACT_CONFLICT_STARTED_VS_TERMINAL"
    hints = lc["abort_triage_hints"]
    assert len(hints) == 1
    h0 = hints[0]
    assert "not live authorization" in h0["disclaimer"].lower()
    assert "read-only" in h0["disclaimer"].lower() or "read_only" in h0["disclaimer"].lower()
    assert h0["primary_runbook"].endswith("RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md")
    assert (
        h0["primary_runbook_docs_token"] == "DOCS_TOKEN_RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH"
    )
    assert "session-end mismatch is unresolved" in h0["section_5_keywords"]
    assert any(x.startswith("lifecycle_consistency_summary=") for x in h0["matched_signals"])
    assert any("mismatch_signal=" in x for x in h0["matched_signals"])


def test_lifecycle_abort_triage_hints_partial_no_exec_jsonl_telemetry_degraded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_partial_ev", status="completed"), base_dir=reg)

    from scripts.report_live_sessions import main

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

    data = json.loads(capsys.readouterr().out)
    lc = data["lifecycle_consistency"]
    assert lc["lifecycle_consistency_summary"] == "PARTIAL_TERMINAL_REGISTRY_WITHOUT_EXEC_JSONL"
    hints = lc["abort_triage_hints"]
    assert len(hints) == 1
    assert hints[0]["primary_runbook"].endswith("RUNBOOK_PILOT_INCIDENT_TELEMETRY_DEGRADED.md")
    assert "not live authorization" in hints[0]["disclaimer"].lower()
    assert "not a policy or go/no-go decision" in hints[0]["disclaimer"].lower()


def test_lifecycle_abort_triage_hints_empty_registry_navigates_compass_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
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
            "--bounded-pilot-lifecycle-consistency",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    lc = data["lifecycle_consistency"]
    assert lc["lifecycle_consistency_summary"] == "NO_BOUNDED_PILOT_SESSION"
    hints = lc["abort_triage_hints"]
    assert len(hints) == 1
    assert "ABORT_TRIAGE_COMPASS" in hints[0]["primary_runbook"]


def test_lifecycle_text_output_keywords(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_txt", status="started"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-lifecycle-consistency",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    out = capsys.readouterr().out
    assert "lifecycle" in out.lower()
    assert "consistency" in out.lower()
    assert "bp_txt" in out
    assert "partial_status" in out
