"""
Tests for scripts/report_live_sessions.py --bounded-pilot-readiness-summary (read-only).
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
        run_id="run_rs",
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


def _fake_readiness_ok(*_a: Any, **_k: Any) -> tuple[bool, dict[str, Any]]:
    return True, {
        "contract": "bounded_pilot_readiness_v1",
        "ok": True,
        "blocked_at": None,
        "message": "ok",
        "go_no_go": {"verdict": "GO_FOR_NEXT_PHASE_ONLY"},
        "live_readiness": {"all_passed": True},
    }


def _fake_packet_ok(*_a: Any, **_k: Any) -> tuple[dict[str, Any], int]:
    return {"summary": {"packet_ok": True, "blocked": []}}, 0


@patch(
    "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
    side_effect=_fake_packet_ok,
)
@patch(
    "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
    side_effect=_fake_readiness_ok,
)
def test_readiness_summary_prefers_open_bounded_pilot(
    _m_r: Any,
    _m_p: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="closed_bp", status="completed"), base_dir=reg)
    register_live_session_run(_rec(session_id="open_bp", status="started"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-readiness-summary",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["contract"] == "report_live_sessions.bounded_pilot_readiness_summary"
    assert data["session_focus"]["primary_session_id"] == "open_bp"
    assert data["session_focus"]["primary_source"] == "open_bounded_pilot"
    assert data["session_focus"]["pointers"]["session_id"] == "open_bp"
    assert data["bounded_pilot_readiness"]["ok"] is True
    assert data["operator_preflight_packet"]["packet_ok"] is True
    assert data["operator_preflight_packet"]["evaluated"] is True


@patch(
    "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
    side_effect=_fake_packet_ok,
)
@patch(
    "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
    side_effect=_fake_readiness_ok,
)
def test_readiness_summary_latest_when_no_open(
    _m_r: Any,
    _m_p: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="only_closed", status="completed"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-readiness-summary",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["session_focus"]["primary_source"] == "latest_bounded_pilot_registry"
    assert data["session_focus"]["primary_session_id"] == "only_closed"
    ej = data["session_focus"]["pointers"]["execution_events_session_jsonl"]
    assert ej["present"] is False


def test_readiness_summary_packet_build_failure_marked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "reports" / "experiments" / "live_sessions").mkdir(parents=True)

    from scripts.report_live_sessions import main

    with patch(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        side_effect=_fake_readiness_ok,
    ):
        with patch(
            "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
            side_effect=RuntimeError("boom"),
        ):
            with patch.object(
                sys,
                "argv",
                [
                    "report_live_sessions.py",
                    "--bounded-pilot-readiness-summary",
                    "--json",
                    "--log-level",
                    "ERROR",
                ],
            ):
                assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["operator_preflight_packet"]["evaluated"] is False
    assert "boom" in data["operator_preflight_packet"]["error"]


def test_readiness_summary_conflicts_with_open_sessions(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-readiness-summary",
            "--open-sessions",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "only one" in capsys.readouterr().err.lower()


def test_readiness_summary_conflicts_session_id(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-readiness-summary",
            "--session-id",
            "x",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2


@patch(
    "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
    side_effect=_fake_packet_ok,
)
@patch(
    "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
    side_effect=_fake_readiness_ok,
)
def test_readiness_summary_packet_blocked_preview(
    _m_r: Any,
    _m_p: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _pkt(*_a: Any, **_k: Any) -> tuple[dict[str, Any], int]:
        return {
            "summary": {
                "packet_ok": False,
                "blocked": ["a", "b", "c"],
            }
        }, 1

    monkeypatch.chdir(tmp_path)
    (tmp_path / "reports" / "experiments" / "live_sessions").mkdir(parents=True)

    from scripts.report_live_sessions import main

    with patch(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        side_effect=_pkt,
    ):
        with patch.object(
            sys,
            "argv",
            [
                "report_live_sessions.py",
                "--bounded-pilot-readiness-summary",
                "--json",
                "--log-level",
                "ERROR",
            ],
        ):
            assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["operator_preflight_packet"]["packet_ok"] is False
    assert data["operator_preflight_packet"]["blocked_lines_total"] == 3
