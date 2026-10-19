"""Bounded Master V2 GHOSV constants. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

CONTRACT_ID: Final = "MASTER_V2_GHOSV_CONTRACT_V1"
SCHEMA_ID: Final = "MASTER_V2_GHOSV_FINDING_V1"
SCHEMA_VERSION: Final = 1
CATALOG_VERSION: Final = "MV2_GHOSV_CATALOG_V1"
DOMAIN: Final = "MASTER_V2"

AUTHORITY: Final = "NONE"
TRADING_AUTHORITY: Final = "NONE"
SAFETY_AUTHORITY: Final = "NONE"
EXECUTION_AUTHORITY: Final = "NONE"
RUNTIME_AUTHORIZATION_EFFECT: Final = "NONE"

GUARDIAN_IDENTITY: Final = False
GRAPH_ENGINE: Final = False
LIVE_GATE: Final = False
OWNER_SUBSTITUTE: Final = False
FULL_UNIVERSE_BOUNDARY_RATIFIED: Final = False

CURRENT_CODE_PIN: Final = "7628005ae495c115ff341d32fa932b7f4642f456"
CURRENT_TREE_PIN: Final = "e652f8d7b86c469311a068c34b0fb3f708c87d73"
CONTRACT_DOCUMENT_PROVENANCE: Final = "6e3143bdfaa769e329c260c45a2fd58bfeb65dfc"

PILOT_BASELINE_EDGE_COUNT: Final = 130
PILOT_BASELINE_EDGE_DIGEST: Final = (
    "b05a0c73c7e2cefd2b6630d00aafcb9d9f5221c36bd53851b25fe737688f94f2"
)
PILOT_PROJECTED_EDGE_COUNT: Final = 136
PILOT_PROJECTED_NODE_COUNT: Final = 131
PILOT_MAX_DEPTH: Final = 1

DECISION_OWNER_SYMBOL: Final = "run_integrated_offline_trading_logic_replay_v1"
CYCLE_SYMBOL: Final = "run_current_productive_master_v2_runtime_cycle_v1"

NOT_TESTED_REQUIREMENTS: Final = (
    "MV2-02",
    "MV2-03",
    "MV2-04",
    "MV2-05",
    "MV2-06",
    "MV2-07",
    "MV2-08",
)

FORBIDDEN_AGGREGATE_KEYS: Final = frozenset(
    {"overall_pass", "guardian_pass", "universe_pass", "live_authorized"}
)
ALLOWED_EVIDENCE_STATUS: Final = frozenset(
    {"PROVEN", "PARTIAL", "NOT_PROVEN", "NOT_TESTED", "UNRESOLVED"}
)
ALLOWED_AUTHORITY_EFFECT: Final = frozenset({"NONE", "CLAIM_REJECTED", "NOT_ASSESSED"})
ALLOWED_EFFECT: Final = frozenset(
    {"NONE_OBSERVED", "NOT_INTERPRETED", "EFFECT_UNREAD", "CLAIM_REJECTED"}
)
