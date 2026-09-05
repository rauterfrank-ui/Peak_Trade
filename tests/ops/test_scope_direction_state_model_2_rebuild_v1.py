"""Model 2 plus overlay-inert: ScopeDirectionState is a SideState projection."""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    DOMAIN_TO_PERSISTENCE_MATRIX,
    STATE_VERSION,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    _update_session_state_from_replay,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_composition_matrix_v1 import (
    CompositionDirectionState,
    CompositionSelectedSide,
)
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    scope_direction_from_side_state_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOST = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
MODELS = REPO_ROOT / "src/ops/dynamic_scope_persistence_binding_v1" / "models_v1.py"

_MAPPED_SHORT = (
    SideState.SHORT_ARMED,
    SideState.SHORT_ARMED_NEUTRAL_START,
    SideState.SHORT_ARMED_SWITCH_TERMINAL,
    SideState.SHORT_ACTIVE,
    SideState.SHORT_BLOCKED,
    SideState.SWITCH_SHORT_TO_LONG_PENDING,
)
_MAPPED_LONG = (
    SideState.LONG_ARMED,
    SideState.LONG_ARMED_NEUTRAL_START,
    SideState.LONG_ARMED_SWITCH_TERMINAL,
    SideState.LONG_ACTIVE,
    SideState.LONG_BLOCKED,
    SideState.SWITCH_LONG_TO_SHORT_PENDING,
)
_FALLBACK_LONG = (
    SideState.NEUTRAL_OBSERVE,
    SideState.CHOP_GUARD_BLOCK,
    SideState.KILL_ALL,
)
_ALL_SIDESTATES = tuple(SideState)
_PENDING_UNCHANGED = (
    (SideState.SWITCH_LONG_TO_SHORT_PENDING, ScopeDirectionState.LONG),
    (SideState.SWITCH_SHORT_TO_LONG_PENDING, ScopeDirectionState.SHORT),
)


def _replay_result(*, next_side: SideState, selected: CompositionSelectedSide) -> SimpleNamespace:
    return SimpleNamespace(
        intermediate=SimpleNamespace(
            state_switch=SimpleNamespace(next_side_state=next_side),
            composition_result=SimpleNamespace(selected_side=selected),
        )
    )


def test_mapped_sidestates_rebuild_from_canonical_table() -> None:
    for side in _MAPPED_SHORT:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.SHORT
    for side in _MAPPED_LONG:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.LONG


def test_neutral_chop_kill_rebuild_to_explicit_long() -> None:
    for side in _FALLBACK_LONG:
        assert scope_direction_from_side_state_v1(side) is ScopeDirectionState.LONG


def test_persisted_short_token_is_not_rebuild_input() -> None:
    """NEUTRAL + persisted SHORT must not survive as generator orientation."""
    rebuilt = scope_direction_from_side_state_v1(SideState.NEUTRAL_OBSERVE)
    assert rebuilt is ScopeDirectionState.LONG
    assert rebuilt is not ScopeDirectionState.SHORT


def test_cap62_scope_direction_is_rebuild_deterministically() -> None:
    row = next(
        item
        for item in DOMAIN_TO_PERSISTENCE_MATRIX
        if item["domain_field"] == "scope_direction_state"
    )
    assert row["classification"] == "REBUILD_DETERMINISTICALLY"
    assert "scope_direction_from_side_state_v1" in str(row["canonical_owner"])
    assert row["classification"] != "PERSIST_DIRECTLY"


def test_from_dict_does_not_invent_long_on_missing() -> None:
    payload = {
        "state_version": STATE_VERSION,
        "scope_session_id": "sess-1",
        "instrument_id": "INST",
        "venue": "OKX",
        "repository_sha": "abc",
        "config_digest": "def",
        "side_state": "neutral_observe",
    }
    loaded = CanonicalDynamicScopeStateV1.from_dict(payload)
    assert loaded.scope_direction_state != "LONG"
    assert loaded.scope_direction_state == ""


def test_from_dict_preserves_raw_token_without_promoting_it() -> None:
    payload = {
        "state_version": STATE_VERSION,
        "scope_session_id": "sess-1",
        "instrument_id": "INST",
        "venue": "OKX",
        "repository_sha": "abc",
        "config_digest": "def",
        "side_state": "short_active",
        "scope_direction_state": "SHORT",
    }
    loaded = CanonicalDynamicScopeStateV1.from_dict(payload)
    assert loaded.scope_direction_state == "SHORT"
    rebuilt = scope_direction_from_side_state_v1(SideState(loaded.side_state))
    assert rebuilt is ScopeDirectionState.SHORT


def test_host_rebuilds_from_sidestate_and_does_not_swallow() -> None:
    text = HOST.read_text(encoding="utf-8")
    restore_at = text.index("parse_persisted_side_state_v1(")
    rebuild_at = text.index("scope_direction_from_side_state_v1(state.side_state)", restore_at)
    replay_at = text.index("run_integrated_offline_trading_logic_replay_v1(")
    assert restore_at < rebuild_at < replay_at
    restore_block = text[restore_at:rebuild_at]
    assert "except SideStateRestoreError" in restore_block
    assert "SIDESTATE_RESTORE_ALPHA_BLOCKED" in text
    assert (
        "ScopeDirectionState(\n                state.dynamic_scope_binding.scope_direction_state"
        not in text
    )
    assert "except Exception:  # noqa: BLE001\n            pass" not in restore_block


def test_host_persist_does_not_write_overlay_cursor() -> None:
    text = HOST.read_text(encoding="utf-8")
    commit_at = text.index("commit_host_dynamic_scope_after_replay_v1(")
    commit_block = text[commit_at : commit_at + 1800]
    assert "scope_direction_from_side_state_v1(state.side_state)" in commit_block
    assert "scope_direction_state=str(state.scope_direction_state.value)" not in commit_block


def test_from_dict_source_does_not_default_to_long() -> None:
    text = MODELS.read_text(encoding="utf-8")
    assert 'payload.get("scope_direction_state") or "LONG"' not in text


def test_invalid_scope_direction_token_is_not_sidestate_alpha_block() -> None:
    text = HOST.read_text(encoding="utf-8")
    assert "SIDESTATE_RESTORE_ALPHA_BLOCKED" in text
    assert "SCOPE_DIRECTION_RESTORE_ALPHA_BLOCKED" not in text


def test_all_sidestates_runtime_restart_projection_parity() -> None:
    assert len(_ALL_SIDESTATES) == 15
    for side in _ALL_SIDESTATES:
        projected = scope_direction_from_side_state_v1(side)
        state = BridgeSessionStateV1(require_selection_binding=False)
        state.side_state = SideState.LONG_ACTIVE
        state.scope_direction_state = ScopeDirectionState.SHORT
        _update_session_state_from_replay(
            state,
            result=_replay_result(next_side=side, selected=CompositionSelectedSide.SHORT),
        )
        restart = scope_direction_from_side_state_v1(state.side_state)
        assert state.side_state is side
        assert state.scope_direction_state is projected
        assert restart is projected
        assert state.scope_direction_state is restart


def test_neutral_observe_after_selected_side_short_is_long() -> None:
    state = BridgeSessionStateV1(require_selection_binding=False)
    state.scope_direction_state = ScopeDirectionState.SHORT
    _update_session_state_from_replay(
        state,
        result=_replay_result(
            next_side=SideState.NEUTRAL_OBSERVE,
            selected=CompositionSelectedSide.SHORT,
        ),
    )
    assert state.side_state is SideState.NEUTRAL_OBSERVE
    assert state.scope_direction_state is ScopeDirectionState.LONG
    assert state.previous_composition_direction_state is CompositionDirectionState.SHORT


def test_chop_guard_block_after_selected_side_short_is_long() -> None:
    state = BridgeSessionStateV1(require_selection_binding=False)
    state.scope_direction_state = ScopeDirectionState.SHORT
    _update_session_state_from_replay(
        state,
        result=_replay_result(
            next_side=SideState.CHOP_GUARD_BLOCK,
            selected=CompositionSelectedSide.SHORT,
        ),
    )
    assert state.side_state is SideState.CHOP_GUARD_BLOCK
    assert state.scope_direction_state is ScopeDirectionState.LONG
    assert state.previous_composition_direction_state is CompositionDirectionState.SHORT


def test_kill_all_after_selected_side_short_is_long() -> None:
    state = BridgeSessionStateV1(require_selection_binding=False)
    state.scope_direction_state = ScopeDirectionState.SHORT
    _update_session_state_from_replay(
        state,
        result=_replay_result(
            next_side=SideState.KILL_ALL,
            selected=CompositionSelectedSide.SHORT,
        ),
    )
    assert state.side_state is SideState.KILL_ALL
    assert state.scope_direction_state is ScopeDirectionState.LONG
    assert state.previous_composition_direction_state is CompositionDirectionState.SHORT


def test_composition_overlay_cannot_mutate_scope_direction() -> None:
    state = BridgeSessionStateV1(require_selection_binding=False)
    _update_session_state_from_replay(
        state,
        result=_replay_result(
            next_side=SideState.LONG_ACTIVE,
            selected=CompositionSelectedSide.SHORT,
        ),
    )
    assert state.previous_composition_direction_state is CompositionDirectionState.SHORT
    assert state.scope_direction_state is ScopeDirectionState.LONG
    text = inspect.getsource(_update_session_state_from_replay)
    assert "state.scope_direction_state = ScopeDirectionState.LONG" not in text
    assert "state.scope_direction_state = ScopeDirectionState.SHORT" not in text
    assert "scope_direction_from_side_state_v1(state.side_state)" in text


def test_pending_mappings_remain_unchanged() -> None:
    for side, expected in _PENDING_UNCHANGED:
        assert scope_direction_from_side_state_v1(side) is expected
        state = BridgeSessionStateV1(require_selection_binding=False)
        _update_session_state_from_replay(
            state,
            result=_replay_result(next_side=side, selected=CompositionSelectedSide.SHORT),
        )
        assert state.scope_direction_state is expected


def test_persisted_short_token_remains_restart_inert() -> None:
    rebuilt = scope_direction_from_side_state_v1(SideState.NEUTRAL_OBSERVE)
    assert rebuilt is ScopeDirectionState.LONG
    text = HOST.read_text(encoding="utf-8")
    restore_at = text.index("parse_persisted_side_state_v1(")
    rebuild_at = text.index("scope_direction_from_side_state_v1(state.side_state)", restore_at)
    restore_block = text[restore_at:rebuild_at]
    assert "state.dynamic_scope_binding.scope_direction_state" not in restore_block


def test_sidestate_fail_closed_restore_is_unchanged() -> None:
    text = HOST.read_text(encoding="utf-8")
    restore_at = text.index("parse_persisted_side_state_v1(")
    sidestate_block = text[restore_at : text.index("state.scope_direction_state", restore_at)]
    assert "except SideStateRestoreError" in sidestate_block
    assert "SIDESTATE_RESTORE_ALPHA_BLOCKED" in text
    assert "except Exception" not in sidestate_block
    assert "pass" not in sidestate_block


def test_cap72_host_projects_before_next_generator_input() -> None:
    """Cap-7.2 overlay cannot leave a SHORT host cursor on Neutral/CHOP/KILL.

    The next cycle passes ``state.scope_direction_state`` into the generator.
    After this persist that cursor is the SideState projection, so composition
    selected_side cannot mutate generator direction on the Cap-7.2 host.
    """
    replay_src = inspect.getsource(_update_session_state_from_replay)
    host_src = HOST.read_text(encoding="utf-8")
    assert "scope_direction_state=state.scope_direction_state" in host_src
    assert "scope_direction_from_side_state_v1(state.side_state)" in replay_src
    for side in _FALLBACK_LONG:
        state = BridgeSessionStateV1(require_selection_binding=False)
        state.scope_direction_state = ScopeDirectionState.SHORT
        _update_session_state_from_replay(
            state,
            result=_replay_result(next_side=side, selected=CompositionSelectedSide.SHORT),
        )
        next_generator_cursor = state.scope_direction_state
        assert next_generator_cursor is ScopeDirectionState.LONG
        assert next_generator_cursor is scope_direction_from_side_state_v1(side)


def test_core_logic_change_is_adjudicated_honestly() -> None:
    runbook = (REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    section_at = runbook.index("11.2.1.D SCOPE_DIRECTION_OVERLAY_GENERATOR_INERT")
    section = runbook[section_at : section_at + 4000]
    assert "CORE_LOGIC_CHANGE=true" in section
    assert "OWNER_RATIFICATION_REQUIRED=true" in section
    assert "COMPOSITION_SELECTED_SIDE_CAN_MUTATE_GENERATOR_DIRECTION=false" in section
