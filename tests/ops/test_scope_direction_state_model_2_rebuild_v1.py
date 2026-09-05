"""Model 2: ScopeDirectionState is rebuilt from SideState, not restart truth."""

from __future__ import annotations

from pathlib import Path

from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    DOMAIN_TO_PERSISTENCE_MATRIX,
    STATE_VERSION,
)
from src.ops.dynamic_scope_persistence_binding_v1.models_v1 import (
    CanonicalDynamicScopeStateV1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
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
    SideState.SHORT_ACTIVE,
    SideState.SHORT_BLOCKED,
    SideState.SWITCH_SHORT_TO_LONG_PENDING,
)
_MAPPED_LONG = (
    SideState.LONG_ARMED,
    SideState.LONG_ACTIVE,
    SideState.LONG_BLOCKED,
    SideState.SWITCH_LONG_TO_SHORT_PENDING,
)
_FALLBACK_LONG = (
    SideState.NEUTRAL_OBSERVE,
    SideState.CHOP_GUARD_BLOCK,
    SideState.KILL_ALL,
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
