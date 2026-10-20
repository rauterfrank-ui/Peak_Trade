"""Constants for the Double Play GHOSV observation adapter. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

SCHEMA_ID: Final = "DOUBLE_PLAY_GHOSV_OBSERVATION_V1"
SCHEMA_VERSION: Final = 1
AUTHORITY: Final = "NONE"

EXPECTED_BASELINE_SHA: Final = "97c8c954204c15f9af5a48995b889ce3fb223c64"
EXPECTED_BASELINE_TREE: Final = "898ede79de7e527db3632b8a3b32daf8b9b098b8"
EXISTING_GHOSV_CODE_PIN: Final = "7628005ae495c115ff341d32fa932b7f4642f456"

GHOSV_CONTRACT_RELATIVE: Final = "docs/ops/specs/MASTER_V2_GHOSV_CONTRACT_V1.md"
DECISION_PATH_RELATIVE: Final = "docs/ops/specs/MV2_DECISION_PATH_BOUNDARY_V1.md"
GHOSV_CONSTANTS_RELATIVE: Final = "scripts/ops/ghosv_master_v2_bounded_context_v1/constants_v1.py"
PERSISTENCE_CONSTANTS_RELATIVE: Final = (
    "src/ops/dynamic_scope_persistence_binding_v1/constants_v1.py"
)

REQUIREMENT_IDS: Final = ("MV2-04", "MV2-05", "MV2-06", "MV2-08")
NEGATIVE_CODES: Final = {
    "MV2-04": "DYNAMIC_SCOPE_ROLE_VIOLATION",
    "MV2-05": "OWNER_LOCK_VIOLATION",
    "MV2-08": "PERSISTENCE_EVIDENCE_ABSENT",
}

LOCK_TOKEN: Final = "DOUBLE_PLAY_FULL_OWNER_LOCK=LEVEL_3"
INTERNAL_AREA_TOKEN: Final = "DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA=true"
SEPARATE_UNIVERSE_TOKEN: Final = "DOUBLE_PLAY_SEPARATE_UNIVERSE=false"
SHARED_MODULE_TOKEN: Final = "double_play_state.py"
ENTRY_EXIT_SYMBOL: Final = "evaluate_double_play_entry_exit_policy_v0"

FORBIDDEN_OUTPUT_KEYS: Final = frozenset(
    {"overall_pass", "guardian_pass", "universe_pass", "live_authorized"}
)
