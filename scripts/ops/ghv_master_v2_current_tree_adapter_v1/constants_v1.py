"""Pinned scope for the Master V2 current-tree GHV adapter. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

PACKAGE_ID: Final = "GHV_MASTER_V2_CURRENT_TREE_ADAPTER_V1"
AUTHORITY: Final = "NONE"
TRADING_AUTHORITY: Final = "NONE"
SAFETY_AUTHORITY: Final = "NONE"
EXECUTION_AUTHORITY: Final = "NONE"
RUNTIME_AUTHORIZATION_EFFECT: Final = "NONE"
EXTERNAL_POST_COUNT: Final = 0
PRODUCTIVE_IMPORTS: Final = False
OWNER_LOCK_MUTATED: Final = False
HOP_LIMIT: Final = 1
EDGE_TYPE: Final = "CALLS"

CURRENT_ORIGIN_MAIN_SHA: Final = "7628005ae495c115ff341d32fa932b7f4642f456"
CURRENT_ORIGIN_MAIN_TREE: Final = "e652f8d7b86c469311a068c34b0fb3f708c87d73"

MEMBERSHIP_START_ANCHOR: Final = "START_ANCHOR"
MEMBERSHIP_UNKNOWN: Final = "UNKNOWN_MEMBERSHIP"
EXISTENCE_EXISTS: Final = "EXISTS"
STATUS_NOT_PROVEN: Final = "NOT_PROVEN"
WIRING_WIRED: Final = "WIRED"
AUTHORIZATION_NOT_AUTHORIZED: Final = "NOT_AUTHORIZED"
FOREIGN_SEMANTICS: Final = "NOT_INTERPRETED"
COVERAGE_STATUS: Final = "PARTIAL"
SCOPE_ID: Final = "BOUNDED_MASTER_V2_FOUR_ANCHORS_ONE_DIRECT_HOP"

# Owner-named start anchors. Dynamic Scope is the symbol inside Double Play state.
ANCHORS: Final = (
    {
        "anchor_id": "productive_master_v2_runtime_cycle",
        "path": (
            "src/ops/full_core_live_path_composition_root_v1/"
            "current_productive_master_v2_runtime_cycle_v1.py"
        ),
        "symbol": "run_current_productive_master_v2_runtime_cycle_v1",
        "location_fact": "PRODUCTIVE_CYCLE_FILE",
    },
    {
        "anchor_id": "integrated_master_v2_replay",
        "path": "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        "symbol": "run_integrated_offline_trading_logic_replay_v1",
        "location_fact": "INTEGRATED_REPLAY_FILE",
    },
    {
        "anchor_id": "double_play_transition_state",
        "path": "src/trading/master_v2/double_play_state.py",
        "symbol": "transition_state",
        "location_fact": "DEFINED_IN_DOUBLE_PLAY_STATE_MODULE",
    },
    {
        "anchor_id": "dynamic_scope_update_dynamic_boundaries",
        "path": "src/trading/master_v2/double_play_state.py",
        "symbol": "update_dynamic_boundaries",
        "location_fact": "DEFINED_IN_DOUBLE_PLAY_STATE_MODULE",
    },
)
