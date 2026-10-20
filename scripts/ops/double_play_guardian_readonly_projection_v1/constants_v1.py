"""Constants for the Double Play guardian gap projection. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

SCHEMA_ID: Final = "DOUBLE_PLAY_GUARDIAN_READONLY_GAP_PROJECTION_V1"
SCHEMA_VERSION: Final = 1
DOMAIN: Final = "DOUBLE_PLAY"
INTERNAL_COMPONENT: Final = "DYNAMIC_SCOPE"

AUTHORITY: Final = "NONE"
TRADING_AUTHORITY: Final = "NONE"
SAFETY_AUTHORITY: Final = "NONE"
EXECUTION_AUTHORITY: Final = "NONE"

EXPECTED_BASELINE_SHA: Final = "97c8c954204c15f9af5a48995b889ce3fb223c64"
EXPECTED_BASELINE_TREE: Final = "898ede79de7e527db3632b8a3b32daf8b9b098b8"

GHOSV_CONTRACT_RELATIVE: Final = "docs/ops/specs/MASTER_V2_GHOSV_CONTRACT_V1.md"
DECISION_PATH_RELATIVE: Final = "docs/ops/specs/MV2_DECISION_PATH_BOUNDARY_V1.md"
GHOSV_CONSTANTS_RELATIVE: Final = "scripts/ops/ghosv_master_v2_bounded_context_v1/constants_v1.py"

LOCK_TOKEN: Final = "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_3"
HIERARCHY_TOKEN: Final = "MASTER V2 > DOUBLE PLAY > DYNAMIC SCOPE"
SEPARATE_UNIVERSE_TOKEN: Final = "DOUBLE_PLAY_SEPARATE_UNIVERSE=false"
INTERNAL_AREA_TOKEN: Final = "DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA=true"
AUTHORITY_TRANSFER_TOKEN: Final = "AUTHORITY_TRANSFER=false"

CATALOG_GAP_IDS: Final = ("MV2-04", "MV2-05", "MV2-06", "MV2-08")
TOOL_ROLES: Final = (
    "DOUBLE_PLAY_GHV",
    "DOUBLE_PLAY_CURRENT_CAUSAL_GRAPH",
    "DOUBLE_PLAY_GHOSV",
)

FORBIDDEN_OUTPUT_KEYS: Final = frozenset(
    {"overall_pass", "guardian_pass", "universe_pass", "live_authorized"}
)

ALLOWED_CLAIMS: Final = frozenset(
    {
        "treat_older_ghosv_pin_as_current",
        "treat_ops_census_node_as_trading_symbol",
        "treat_catalog_check_as_executed",
        "treat_missing_graph_symbol_as_isolation",
        "dynamic_scope_separate_universe",
        "infer_productive_persistence_from_state_persisted",
        "authority",
        "trading_authority",
        "safety_authority",
        "execution_authority",
    }
)
