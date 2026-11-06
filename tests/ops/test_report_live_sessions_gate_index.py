"""
Tests for scripts/report_live_sessions.py --bounded-pilot-gate-index (read-only).
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
        run_id="run_gi",
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
def test_gate_index_prefers_open_bounded_pilot(
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
            "--bounded-pilot-gate-index",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["contract"] == "report_live_sessions.bounded_pilot_gate_index"
    gi = data["gate_enablement_index"]
    assert gi["contract"] == "report_live_sessions.gate_enablement_index_v1"
    assert gi["primary_session_id"] == "open_bp"
    assert gi["bounded_pilot_open_started_count"] == 1
    assert gi["closeout_signal_summary"] == "REGISTRY_NON_TERMINAL_NEWEST_ONLY"
    assert gi["go_no_go_verdict"] == "GO_FOR_NEXT_PHASE_ONLY"


@patch(
    "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
    side_effect=_fake_packet_ok,
)
@patch(
    "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
    side_effect=_fake_readiness_ok,
)
def test_gate_index_latest_when_no_open(
    _m_r: Any,
    _m_p: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="only_done", status="completed"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-gate-index",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    gi = data["gate_enablement_index"]
    assert gi["primary_source"] == "latest_bounded_pilot_registry"
    assert gi["closeout_signal_summary"] == "REGISTRY_TERMINAL_IN_NEWEST_ARTIFACT"
    assert gi["execution_events_jsonl_present"] is False


@patch(
    "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
    side_effect=_fake_packet_ok,
)
@patch(
    "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
    side_effect=_fake_readiness_ok,
)
def test_gate_index_execution_events_present(
    _m_r: Any,
    _m_p: Any,
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
            "--bounded-pilot-gate-index",
            "--json",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 0

    data = json.loads(capsys.readouterr().out)
    assert data["gate_enablement_index"]["execution_events_jsonl_present"] is True


def test_gate_index_conflicts_with_overview(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-gate-index",
            "--bounded-pilot-operator-overview",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2
    assert "only one" in capsys.readouterr().err.lower()


def test_gate_index_conflicts_session_id(capsys: pytest.CaptureFixture[str]) -> None:
    from scripts.report_live_sessions import main

    with patch.object(
        sys,
        "argv",
        [
            "report_live_sessions.py",
            "--bounded-pilot-gate-index",
            "--session-id",
            "x",
            "--log-level",
            "ERROR",
        ],
    ):
        assert main() == 2


def test_gate_index_text_contains_keywords(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    reg.mkdir(parents=True)
    register_live_session_run(_rec(session_id="bp_txt", status="started"), base_dir=reg)

    from scripts.report_live_sessions import main

    with patch(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        side_effect=_fake_readiness_ok,
    ):
        with patch(
            "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
            side_effect=_fake_packet_ok,
        ):
            with patch.object(
                sys,
                "argv",
                [
                    "report_live_sessions.py",
                    "--bounded-pilot-gate-index",
                    "--log-level",
                    "ERROR",
                ],
            ):
                assert main() == 0

    out = capsys.readouterr().out
    assert "gate" in out.lower()
    assert "enablement index" in out.lower()
    assert "go_no_go_verdict:" in out
    assert "bp_txt" in out


@patch(
    "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
    side_effect=_fake_packet_ok,
)
@patch(
    "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
    side_effect=_fake_readiness_ok,
)
def test_closeout_rejects_config_path_for_gate_index_context(
    _m_r: Any,
    _m_p: Any,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Closeout mode still rejects --config-path; gate-index allows it."""
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
    err = capsys.readouterr().err.lower()
    assert "config-path" in err
    assert "gate-index" in err
