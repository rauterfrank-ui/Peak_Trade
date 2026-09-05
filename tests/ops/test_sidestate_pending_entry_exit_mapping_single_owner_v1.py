"""Wallclock hosts consume the Replay Entry/Exit mapping owner — no local table."""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    _update_session_state_from_replay as _hardening_update,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    _update_session_state_from_replay as _cap72_update,
)
from trading.master_v2.double_play_composition_matrix_v1 import CompositionSelectedSide
from trading.master_v2.double_play_entry_exit_policy_v0 import EntryExitDirectionState
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _side_state_to_entry_exit_direction,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CAP72_HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
HARDENING_HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
    / "hardening_cycle_bridge_v2.py"
)
_ALL_SIDESTATES = tuple(SideState)
_PINNED_OWNER_ROWS = (
    (SideState.SWITCH_LONG_TO_SHORT_PENDING, EntryExitDirectionState.SHORT_ARMED),
    (SideState.SWITCH_SHORT_TO_LONG_PENDING, EntryExitDirectionState.LONG_ARMED),
    (SideState.LONG_ARMED_NEUTRAL_START, EntryExitDirectionState.LONG_ARMED),
    (SideState.LONG_ARMED_SWITCH_TERMINAL, EntryExitDirectionState.LONG_ARMED),
    (SideState.SHORT_ARMED_NEUTRAL_START, EntryExitDirectionState.SHORT_ARMED),
    (SideState.SHORT_ARMED_SWITCH_TERMINAL, EntryExitDirectionState.SHORT_ARMED),
)


def _replay_result(*, next_side: SideState) -> SimpleNamespace:
    return SimpleNamespace(
        intermediate=SimpleNamespace(
            state_switch=SimpleNamespace(next_side_state=next_side),
            composition_result=SimpleNamespace(selected_side=CompositionSelectedSide.NONE),
        )
    )


def test_cap72_consumes_replay_mapping_owner() -> None:
    src = inspect.getsource(_cap72_update)
    assert "side_map" not in src
    assert "_side_state_to_entry_exit_direction(state.side_state)" in src
    host_src = CAP72_HOST.read_text(encoding="utf-8")
    assert "from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (" in host_src
    assert "_side_state_to_entry_exit_direction" in host_src
    assert "SWITCH_LONG_TO_SHORT_PENDING: EntryExitDirectionState.LONG_ACTIVE" not in host_src
    assert "SWITCH_SHORT_TO_LONG_PENDING: EntryExitDirectionState.SHORT_ACTIVE" not in host_src


def test_hardening_v2_consumes_same_replay_mapping_owner() -> None:
    src = inspect.getsource(_hardening_update)
    assert "side_map" not in src
    assert "_side_state_to_entry_exit_direction(state.side_state)" in src
    host_src = HARDENING_HOST.read_text(encoding="utf-8")
    assert "from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (" in host_src
    assert "_side_state_to_entry_exit_direction" in host_src
    assert "SWITCH_LONG_TO_SHORT_PENDING: EntryExitDirectionState.LONG_ACTIVE" not in host_src
    assert "SWITCH_SHORT_TO_LONG_PENDING: EntryExitDirectionState.SHORT_ACTIVE" not in host_src


def test_all_sidestate_session_cursor_parity_with_replay_owner() -> None:
    for side in _ALL_SIDESTATES:
        expected = _side_state_to_entry_exit_direction(side)
        cap72 = BridgeSessionStateV1()
        _cap72_update(cap72, result=_replay_result(next_side=side))
        hardening = HardenedBridgeSessionStateV2()
        _hardening_update(hardening, result=_replay_result(next_side=side))
        assert cap72.direction_state is expected
        assert hardening.direction_state is expected
        assert cap72.direction_state is hardening.direction_state


def test_pending_and_armed_identity_rows_match_replay_owner() -> None:
    for side, expected in _PINNED_OWNER_ROWS:
        assert _side_state_to_entry_exit_direction(side) is expected
        cap72 = BridgeSessionStateV1()
        _cap72_update(cap72, result=_replay_result(next_side=side))
        hardening = HardenedBridgeSessionStateV2()
        _hardening_update(hardening, result=_replay_result(next_side=side))
        assert cap72.direction_state is expected
        assert hardening.direction_state is expected


def test_runbook_records_single_owner_materialization() -> None:
    runbook = (REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    section_at = runbook.index(
        "11.2.1.H SIDESTATE_PENDING_ENTRY_EXIT_MAPPING_SINGLE_OWNER_MINIMUM_ATOMIC_REPAIR"
    )
    section = runbook[section_at : runbook.index("## 11.3 Autonomy state model", section_at)]
    assert "CORE_LOGIC_CHANGE=true" in section
    assert "ENTRY_EXIT_MAPPING_OWNER=_side_state_to_entry_exit_direction" in section
    assert "PENDING_TARGET_REWRITE_AUTHORIZED=false" in section
    assert "NEW_ECONOMIC_GUARD_CLASS_COUNT=0" in section
    assert "HARD_STOP_AFTER_THIS_TASK=true" in section
