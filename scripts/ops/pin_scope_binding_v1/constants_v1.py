"""Pin and scope binding constants. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

SCHEMA_ID: Final = "PIN_SCOPE_BINDING_V1"
SCHEMA_VERSION: Final = 1

AUTHORITY: Final = "NONE"
TRADING_AUTHORITY: Final = "NONE"
SAFETY_AUTHORITY: Final = "NONE"
EXECUTION_AUTHORITY: Final = "NONE"
RUNTIME_AUTHORIZATION_EFFECT: Final = "NONE"
GUARDIAN_IDENTITY: Final = False
LIVE_GATE: Final = False
NETWORK_ACCESS: Final = False
COVERAGE_PROOF: Final = False

STATUS_ACCEPTED: Final = "ACCEPTED"
STATUS_PIN_MISMATCH: Final = "PIN_MISMATCH"
STATUS_INPUT_SOURCE_STALE: Final = "INPUT_SOURCE_STALE"
STATUS_SCOPE_EMPTY: Final = "SCOPE_EMPTY"
STATUS_SCOPE_CONFLICT: Final = "SCOPE_CONFLICT"
STATUS_INVALID_PROVENANCE: Final = "INVALID_PROVENANCE"
STATUS_INVALID_SCOPE: Final = "INVALID_SCOPE"

SCOPE_FIELDS: Final = ("allowed_nodes", "exclusions", "unassigned")
PROVENANCE_ROLES: Final = ("census", "landscape", "graph")

CENSUS_PIN_FIELD: Final = "pin"
LANDSCAPE_COMMIT_FIELD: Final = "commit_pin"
LANDSCAPE_TREE_FIELD: Final = "tree_pin"
GRAPH_PIN_FIELD: Final = "pin"
