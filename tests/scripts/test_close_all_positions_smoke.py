"""LB-EMG-001 — mock-only emergency close script smoke (no network)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "live" / "close_all_positions.py"


def _load_close_module():
    spec = importlib.util.spec_from_file_location(
        "close_all_positions_emg",
        SCRIPT_PATH,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["close_all_positions_emg"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_help_mentions_no_live_and_mock_scope() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "NO-LIVE" in out
    assert "mock" in out.lower()


def test_default_is_dry_run_and_exits_zero() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "dry_run=True" in result.stdout


def test_execute_flag_uses_mock_non_dry_branch() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--execute"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "dry_run=False" in result.stdout
    assert "LB_EMG_001_MOCK" in result.stdout


def test_run_emergency_close_all_v1_unit() -> None:
    mod = _load_close_module()
    r = mod.run_emergency_close_all_v1(dry_run=True, broker=mod.MockEmergencyBrokerV1())
    assert r.exit_code == 0
    assert r.dry_run is True
    assert len(r.messages) >= 1


def test_mock_broker_satisfies_emergency_broker_protocol() -> None:
    mod = _load_close_module()
    b = mod.MockEmergencyBrokerV1()
    assert isinstance(b, mod.EmergencyBroker)


def test_run_emergency_close_all_v1_dry_run_false_branch() -> None:
    mod = _load_close_module()
    r = mod.run_emergency_close_all_v1(dry_run=False, broker=mod.MockEmergencyBrokerV1())
    assert r.dry_run is False
    assert any("dry_run=False" in m for m in r.messages)
    assert any("LB_EMG_001_MOCK" in m for m in r.messages)


def test_run_emergency_close_all_v1_rejects_non_broker() -> None:
    mod = _load_close_module()

    class _Bad:
        pass

    with pytest.raises(TypeError, match="EmergencyBroker"):
        mod.run_emergency_close_all_v1(dry_run=True, broker=_Bad())  # type: ignore[arg-type]


def test_custom_in_memory_broker() -> None:
    mod = _load_close_module()

    class _Tiny(mod.EmergencyBroker):
        def close_all_positions(self, *, dry_run: bool) -> list[str]:
            return [f"custom_ok dry_run={dry_run}"]

    r = mod.run_emergency_close_all_v1(dry_run=True, broker=_Tiny())
    assert r.messages == ("custom_ok dry_run=True",)


def test_module_has_no_network_imports() -> None:
    mod = _load_close_module()
    # Script must not bind network client libs at import/load time.
    forbidden = ("socket", "urllib", "requests", "httpx", "aiohttp")
    src = Path(mod.__file__).read_text(encoding="utf-8")
    for name in forbidden:
        assert f"import {name}" not in src, f"unexpected import {name}"


def test_cli_unknown_flag_exits_nonzero() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--not-a-real-flag"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
