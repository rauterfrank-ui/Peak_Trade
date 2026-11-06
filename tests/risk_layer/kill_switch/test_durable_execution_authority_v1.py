"""Durable KS-A execution authority: persist writer + canonical FILEGATE reader."""

from __future__ import annotations

import json
from argparse import Namespace
from datetime import datetime

import pytest

from src.ops.gates.risk_gate import kill_switch_should_block_trading
from src.risk_layer.kill_switch.cli import cmd_trigger
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState


def _persist_config(tmp_path, monkeypatch):
    path = tmp_path / "kill_switch_state.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(path))
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    return path


def test_cli_trigger_persists_and_second_process_filegate_blocks(tmp_path, monkeypatch):
    path = _persist_config(tmp_path, monkeypatch)
    process_a = KillSwitch(
        {
            "persist_state": True,
            "require_approval_code": False,
            "recovery_cooldown_seconds": 0,
        }
    )
    args = Namespace(reason="durable-authority-test", confirm=True)
    cmd_trigger(args, process_a)

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["state"] == "KILLED"
    assert KillSwitchState[raw["state"]] is KillSwitchState.KILLED

    process_b = KillSwitch(
        {
            "persist_state": True,
            "require_approval_code": False,
            "recovery_cooldown_seconds": 0,
        }
    )
    assert process_b.state is KillSwitchState.KILLED
    assert kill_switch_should_block_trading(explicit_active=False) is True


def test_killed_and_recovering_block_active_does_not(tmp_path, monkeypatch):
    path = _persist_config(tmp_path, monkeypatch)
    persistence = StatePersistence(str(path))
    persistence.save(KillSwitchState.KILLED, killed_at=datetime.utcnow(), trigger_reason="t")
    assert kill_switch_should_block_trading(explicit_active=False) is True
    persistence.save(KillSwitchState.RECOVERING, recovery_started_at=datetime.utcnow())
    assert kill_switch_should_block_trading(explicit_active=False) is True
    persistence.save(KillSwitchState.ACTIVE)
    assert kill_switch_should_block_trading(explicit_active=False) is False


def test_peak_kill_switch_overlay_when_unconfigured(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PEAK_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
    assert kill_switch_should_block_trading(explicit_active=False) is True


def test_persistence_atomic_json_enum_round_trip(tmp_path):
    path = tmp_path / "state.json"
    persistence = StatePersistence(str(path))
    for state in KillSwitchState:
        persistence.save(state, trigger_reason=state.name)
        loaded = persistence.load()
        assert loaded is not None
        assert loaded["state"] == state.name
        assert KillSwitchState[loaded["state"]] is state
        json.loads(path.read_text(encoding="utf-8"))
        assert not list(tmp_path.glob("*.tmp"))


def test_missing_unreadable_invalid_state_policies(tmp_path, monkeypatch):
    configured = tmp_path / "missing.json"
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(configured))
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    assert kill_switch_should_block_trading(explicit_active=False) is True

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(bad))
    assert kill_switch_should_block_trading(explicit_active=False) is True

    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"state": "NOPE"}), encoding="utf-8")
    monkeypatch.setenv("PEAK_KILL_SWITCH_STATE_PATH", str(invalid))
    assert kill_switch_should_block_trading(explicit_active=False) is True

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PEAK_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    assert kill_switch_should_block_trading(explicit_active=False) is False


def test_recovery_does_not_silently_clear_killed(tmp_path, monkeypatch):
    path = _persist_config(tmp_path, monkeypatch)
    ks = KillSwitch(
        {
            "persist_state": True,
            "require_approval_code": False,
            "recovery_cooldown_seconds": 0,
        }
    )
    assert ks.trigger("trip") is True
    assert json.loads(path.read_text(encoding="utf-8"))["state"] == "KILLED"

    restarted = KillSwitch(
        {
            "persist_state": True,
            "require_approval_code": False,
            "recovery_cooldown_seconds": 0,
        }
    )
    assert restarted.state is KillSwitchState.KILLED
    assert restarted.complete_recovery() is False
    assert json.loads(path.read_text(encoding="utf-8"))["state"] == "KILLED"
    assert kill_switch_should_block_trading(explicit_active=False) is True

    assert restarted.request_recovery("operator") is True
    assert json.loads(path.read_text(encoding="utf-8"))["state"] == "RECOVERING"
    assert kill_switch_should_block_trading(explicit_active=False) is True

    assert restarted.complete_recovery() is True
    assert json.loads(path.read_text(encoding="utf-8"))["state"] == "ACTIVE"
    assert kill_switch_should_block_trading(explicit_active=False) is False


def test_cli_trigger_refuses_in_memory_only_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PEAK_KILL_SWITCH_STATE_PATH", raising=False)
    monkeypatch.delenv("PEAKTRADE_KILL_SWITCH_STATE_PATH", raising=False)
    ks = KillSwitch({"persist_state": False, "require_approval_code": False})
    with pytest.raises(RuntimeError, match="did not persist"):
        cmd_trigger(Namespace(reason="no-persist", confirm=True), ks)
