"""Fail-closed SideState restore: no silent enum swallow, no invented default."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.sidestate_restore_v1 import (
    INVALID_PERSISTED_SIDESTATE,
    SideStateRestoreError,
    parse_persisted_side_state_v1,
)
from trading.master_v2.double_play_state import SideState

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)


@pytest.mark.parametrize(
    "raw",
    [
        SideState.LONG_ARMED,
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.LONG_ARMED_SWITCH_TERMINAL,
        SideState.NEUTRAL_OBSERVE,
        SideState.KILL_ALL,
        "long_armed",
        "long_armed_neutral_start",
        "long_armed_switch_terminal",
        "neutral_observe",
        "kill_all",
    ],
)
def test_valid_persisted_sidestate_restores(raw: object) -> None:
    restored = parse_persisted_side_state_v1(raw)
    expected = raw if isinstance(raw, SideState) else SideState(str(raw))
    assert restored is expected
    assert restored is not None


def test_kill_all_restores_as_sidestate_not_filegate() -> None:
    restored = parse_persisted_side_state_v1("kill_all")
    assert restored is SideState.KILL_ALL
    assert restored.value != "FILEGATE_KILLED"


@pytest.mark.parametrize("raw", ["not_a_side_state", "LONG_ARMED", "FILEGATE_KILLED", "unknown"])
def test_unknown_persisted_sidestate_fails_closed(raw: str) -> None:
    with pytest.raises(SideStateRestoreError) as caught:
        parse_persisted_side_state_v1(raw)
    assert caught.value.reason_code == INVALID_PERSISTED_SIDESTATE
    assert "persisted_sidestate_unknown" in caught.value.detail


def test_none_persisted_sidestate_fails_closed() -> None:
    with pytest.raises(SideStateRestoreError) as caught:
        parse_persisted_side_state_v1(None)
    assert caught.value.reason_code == INVALID_PERSISTED_SIDESTATE
    assert "missing" in caught.value.detail


def test_empty_persisted_sidestate_fails_closed() -> None:
    with pytest.raises(SideStateRestoreError) as caught:
        parse_persisted_side_state_v1("  ")
    assert caught.value.reason_code == INVALID_PERSISTED_SIDESTATE


def test_unparseable_persisted_sidestate_fails_closed() -> None:
    with pytest.raises(SideStateRestoreError) as caught:
        parse_persisted_side_state_v1(123)
    assert caught.value.reason_code == INVALID_PERSISTED_SIDESTATE
    assert "unparseable" in caught.value.detail


def test_invalid_restore_does_not_normalize_to_another_sidestate() -> None:
    with pytest.raises(SideStateRestoreError):
        parse_persisted_side_state_v1("garbage")
    # No fallback value is returned; caller cannot continue with a guessed state.


def test_host_restore_is_typed_fail_closed_before_replay() -> None:
    text = HOST.read_text(encoding="utf-8")
    restore_at = text.index("parse_persisted_side_state_v1(")
    replay_at = text.index("run_integrated_offline_trading_logic_replay_v1(")
    assert restore_at < replay_at
    assert "SIDESTATE_RESTORE_ALPHA_BLOCKED" in text
    assert "state.side_state = SideState(state.dynamic_scope_binding.side_state)" not in text
    sidestate_block = text[restore_at : text.index("state.scope_direction_state", restore_at)]
    assert "except SideStateRestoreError" in sidestate_block
    assert "except Exception" not in sidestate_block
    assert "pass" not in sidestate_block


def test_host_does_not_swallow_sidestate_restore_errors() -> None:
    text = HOST.read_text(encoding="utf-8")
    assert "SideStateRestoreError" in text
    assert "SIDESTATE_RESTORE_ALPHA_BLOCKED" in text
