"""Tests for bounded-pilot operator preflight packet CLI (read-only orchestration)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def _passing_readiness_bundle() -> tuple[bool, dict]:
    return True, {
        "contract": "bounded_pilot_readiness_v1",
        "ok": True,
        "blocked_at": None,
        "message": "ok",
    }


def _green_stop_snapshot() -> dict:
    return {
        "contract": "operator_stop_signal_snapshot_v1",
        "incident_stop_artifact": {"status": "none", "path": None, "parsed": None, "error": None},
        "kill_switch_file": {
            "status": "unavailable",
            "path": "data/kill_switch/state.json",
            "kill_switch_active": None,
            "state": None,
        },
        "consistency_notes": [],
    }


def test_build_packet_green(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: _passing_readiness_bundle(),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 0
    assert packet["contract"] == mod.CONTRACT_ID
    assert packet["summary"]["packet_ok"] is True
    assert packet["summary"]["readiness_ok"] is True
    assert packet["summary"]["stop_snapshot_ok"] is True
    assert packet["bounded_pilot_readiness"]["ok"] is True
    assert packet["stop_signal_snapshot"]["contract"] == "operator_stop_signal_snapshot_v1"
    assert "metadata" in packet
    assert "generated_at_utc" in packet["metadata"]


def test_build_packet_blocked_on_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (
            False,
            {
                "contract": "bounded_pilot_readiness_v1",
                "ok": False,
                "blocked_at": "live_readiness",
                "message": "live readiness failed (1 check(s))",
            },
        ),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 1
    assert packet["summary"]["packet_ok"] is False
    assert packet["summary"]["readiness_ok"] is False
    assert packet["stop_signal_snapshot"] is not None
    assert any("bounded_pilot_readiness" in b for b in (packet["summary"]["blocked"] or []))


def test_build_packet_blocked_on_stop_signal_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: _passing_readiness_bundle(),
    )

    def _bad_snapshot(repo: Path) -> dict:
        s = _green_stop_snapshot()
        s["kill_switch_file"] = {
            "status": "error",
            "path": "data/kill_switch/state.json",
            "kill_switch_active": None,
            "state": None,
            "error": "invalid json",
        }
        return s

    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        _bad_snapshot,
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 1
    assert packet["summary"]["readiness_ok"] is True
    assert packet["summary"]["stop_snapshot_ok"] is False
    assert packet["summary"]["packet_ok"] is False
    assert any("kill_switch_file" in b for b in (packet["summary"]["blocked"] or []))


def test_build_packet_exit_2_on_stop_snapshot_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: _passing_readiness_bundle(),
    )

    def _boom(repo: Path) -> dict:
        raise RuntimeError("snapshot boom")

    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        _boom,
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 2
    assert packet["summary"]["packet_ok"] is False
    assert packet["stop_signal_snapshot"].get("orchestrator_error") == "snapshot boom"


def test_build_packet_exit_2_on_readiness_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    def _boom_readiness(*a, **k):
        raise RuntimeError("readiness boom")

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        _boom_readiness,
    )

    packet, code = mod.build_operator_preflight_packet(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert code == 2
    assert packet["bounded_pilot_readiness"].get("orchestrator_error") == "readiness boom"
    assert packet["stop_signal_snapshot"] is None


def test_main_json_green(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    import scripts.ops.bounded_pilot_operator_preflight_packet as mod

    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: _passing_readiness_bundle(),
    )
    monkeypatch.setattr(
        "scripts.ops.snapshot_operator_stop_signals.build_stop_signal_snapshot",
        lambda repo: _green_stop_snapshot(),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["bounded_pilot_operator_preflight_packet", "--json", "--repo-root", str(ROOT)],
    )
    assert mod.main() == 0
    out = json.loads(capsys.readouterr().out.strip())
    assert out["contract"] == mod.CONTRACT_ID
    assert out["summary"]["packet_ok"] is True
