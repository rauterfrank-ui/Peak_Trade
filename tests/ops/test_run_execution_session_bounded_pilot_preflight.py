"""Tests for bounded_pilot non-dry-run operator preflight packet parity in run_execution_session CLI."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "run_execution_session.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("run_execution_session_cli", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _green_packet() -> tuple[dict, int]:
    return (
        {
            "contract": "bounded_pilot_operator_preflight_packet_v1",
            "summary": {
                "readiness_ok": True,
                "stop_snapshot_ok": True,
                "packet_ok": True,
                "blocked": [],
                "notes": [],
            },
        },
        0,
    )


def test_preflight_packet_ok_returns_0(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()
    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        lambda *a, **k: _green_packet(),
    )
    assert mod._bounded_pilot_non_dry_run_preflight_packet_ok(ROOT, "config/config.toml") == 0


def test_preflight_packet_blocked_returns_1(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()

    def _bad(*a, **k):
        return (
            {
                "contract": "bounded_pilot_operator_preflight_packet_v1",
                "summary": {
                    "readiness_ok": True,
                    "stop_snapshot_ok": False,
                    "packet_ok": False,
                    "blocked": ["stop_signal_snapshot.kill_switch_file: error (x)"],
                    "notes": [],
                },
            },
            1,
        )

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _bad,
    )
    assert mod._bounded_pilot_non_dry_run_preflight_packet_ok(ROOT, "config/config.toml") == 1


def test_preflight_packet_orchestrator_error_returns_2(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()

    def _broken(*a, **k):
        return (
            {
                "contract": "bounded_pilot_operator_preflight_packet_v1",
                "summary": {
                    "packet_ok": False,
                    "blocked": ["stop_signal_snapshot: exception (boom)"],
                },
            },
            2,
        )

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _broken,
    )
    assert mod._bounded_pilot_non_dry_run_preflight_packet_ok(ROOT, "config/config.toml") == 2


def test_preflight_packet_build_raises_returns_2(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()

    def _raise(*a, **k):
        raise RuntimeError("packet boom")

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _raise,
    )
    assert mod._bounded_pilot_non_dry_run_preflight_packet_ok(ROOT, "config/config.toml") == 2


def test_main_non_dry_run_returns_1_when_preflight_packet_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.core.environment import (
        LIVE_CONFIRM_TOKEN,
        PT_BOUNDED_PILOT_INVOKED_FROM_GATE,
        PT_LIVE_CONFIRM_TOKEN_ENV,
    )

    mod = _load_mod()
    monkeypatch.setenv(PT_BOUNDED_PILOT_INVOKED_FROM_GATE, "1")
    monkeypatch.setenv(PT_LIVE_CONFIRM_TOKEN_ENV, LIVE_CONFIRM_TOKEN)

    def _bad(*a, **k):
        return (
            {
                "contract": "bounded_pilot_operator_preflight_packet_v1",
                "summary": {
                    "packet_ok": False,
                    "blocked": ["stop_signal_snapshot.kill_switch_file: error (e)"],
                },
            },
            1,
        )

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _bad,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_execution_session",
            "--mode",
            "bounded_pilot",
            "--strategy",
            "ma_crossover",
            "--steps",
            "1",
        ],
    )
    assert mod.main() == 1


def test_main_non_dry_run_reaches_downstream_after_preflight_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Preflight GREEN then existing main path runs (fail later at load_config)."""
    from src.core.environment import (
        LIVE_CONFIRM_TOKEN,
        PT_BOUNDED_PILOT_INVOKED_FROM_GATE,
        PT_LIVE_CONFIRM_TOKEN_ENV,
    )

    mod = _load_mod()
    monkeypatch.setenv(PT_BOUNDED_PILOT_INVOKED_FROM_GATE, "1")
    monkeypatch.setenv(PT_LIVE_CONFIRM_TOKEN_ENV, LIVE_CONFIRM_TOKEN)
    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        lambda *a, **k: _green_packet(),
    )

    def _after_preflight(_p):
        raise RuntimeError("after_preflight_marker")

    monkeypatch.setattr("src.core.peak_config.load_config", _after_preflight)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_execution_session",
            "--mode",
            "bounded_pilot",
            "--strategy",
            "ma_crossover",
            "--steps",
            "1",
        ],
    )
    assert mod.main() == 1


def test_main_non_dry_run_returns_2_when_preflight_orchestrator_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.core.environment import (
        LIVE_CONFIRM_TOKEN,
        PT_BOUNDED_PILOT_INVOKED_FROM_GATE,
        PT_LIVE_CONFIRM_TOKEN_ENV,
    )

    mod = _load_mod()
    monkeypatch.setenv(PT_BOUNDED_PILOT_INVOKED_FROM_GATE, "1")
    monkeypatch.setenv(PT_LIVE_CONFIRM_TOKEN_ENV, LIVE_CONFIRM_TOKEN)

    def _broken(*a, **k):
        return (
            {
                "contract": "bounded_pilot_operator_preflight_packet_v1",
                "summary": {
                    "packet_ok": False,
                    "blocked": ["stop_signal_snapshot: exception (boom)"],
                },
            },
            2,
        )

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _broken,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_execution_session",
            "--mode",
            "bounded_pilot",
            "--strategy",
            "ma_crossover",
            "--steps",
            "1",
        ],
    )
    assert mod.main() == 2


def test_bounded_pilot_dry_run_skips_preflight_in_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dry-run must not invoke preflight packet helper (abgrenzung)."""
    mod = _load_mod()
    called: list = []

    def _should_not_run(*a, **k):
        called.append(True)
        return _green_packet()

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _should_not_run,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_execution_session",
            "--mode",
            "bounded_pilot",
            "--strategy",
            "ma_crossover",
            "--steps",
            "1",
            "--dry-run",
        ],
    )
    rc = mod.main()
    assert rc == 0
    assert called == []
