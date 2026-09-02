"""Standing constants for the canonical offline position-creation path wiring.

This slice composes existing Master-V2 / Double-Play / 29P / Safety / 29Q /
mapper outputs into the existing Z2DB offline seam. It does not mint a second
trading authority and does not reach a productive wire.
"""

from __future__ import annotations

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    ENTER_LONG_MAPPER_SIDE,
    ENTER_SHORT_MAPPER_SIDE,
    OWNER_GO as Z2DB_OWNER_GO,
    PRODUCTIVE_WIRE_REACHABLE,
)

PATH_WIRING_OWNER_GO = "PEAK_TRADE_OWNER_GO_OFFLINE_CANONICAL_POSITION_CREATION_PATH_WIRING_V1"
PATH_WIRING_WORKPACKAGE_ID = "OFFLINE_CANONICAL_POSITION_CREATION_PATH_WIRING_V1"
PATH_WIRING_THIS_SLICE = "11.13.5.Z2DM"
PATH_WIRING_PREDECESSOR_SLICE = "11.13.5.Z2DL"
PATH_WIRING_CONTRACT_VERSION = "v1"
ASSEMBLER_ID = "canonical_offline_lineage_assembler_v1"
ASSEMBLER_CONTRACT_VERSION = "v1"
LINEAGE_PROVENANCE_PRODUCTIVE = "PRODUCTIVE_TYPED_UPSTREAM"
LINEAGE_PROVENANCE_FIXTURE = "FIXTURE_ONLY"
REQUIRED_QUANTITY_UNIT = "CONTRACTS"
ENTRY_INTENT_ACTIONS: frozenset[str] = frozenset({"ENTER_LONG", "ENTER_SHORT"})
HOLD_DECISION_OUTCOMES: frozenset[str] = frozenset(
    {"hold", "no_action", "observe", "cancel_pending", "reconcile_only"}
)
EXIT_DECISION_OUTCOMES: frozenset[str] = frozenset({"exit", "reduce"})
BLOCKED_DECISION_OUTCOMES: frozenset[str] = frozenset({"blocked"})
PLAN_TO_DECISION_OUTCOME: dict[str, str] = {
    "ENTER_LONG": "enter_long",
    "ENTER_SHORT": "enter_short",
}
PLAN_TO_PLAN_SIDE: dict[str, str] = {
    "ENTER_LONG": "LONG",
    "ENTER_SHORT": "SHORT",
}
PLAN_TO_MAPPER_SIDE: dict[str, str] = {
    "ENTER_LONG": ENTER_LONG_MAPPER_SIDE,
    "ENTER_SHORT": ENTER_SHORT_MAPPER_SIDE,
}
ALLOWED_PERMISSION_OWNER_GOS: frozenset[str] = frozenset({Z2DB_OWNER_GO, PATH_WIRING_OWNER_GO})
HOST_GRAPH_ACTIVATION = False
CANONICAL_OFFLINE_POSITION_CREATION_PATH_IMPLEMENTED = True
PRODUCTIVE_WIRE_REACHABLE_BY_THIS_SLICE = PRODUCTIVE_WIRE_REACHABLE
Z2DB_PERMISSION_OWNER_GO = Z2DB_OWNER_GO
