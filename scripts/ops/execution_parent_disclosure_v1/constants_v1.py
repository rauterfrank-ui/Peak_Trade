"""Execution disclosure admission constants. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Final

SCHEMA_ID: Final = "DISCLOSURE_OBSERVATION_CHANNEL_V1"
SCHEMA_VERSION: Final = 1

EXPECTED_BASELINE_SHA: Final = "37e51e3c7988026d2caa8c9a83ff46a056e416a8"
EXPECTED_BASELINE_TREE: Final = "4619907408f709ba6781377b853d7efb682bc49d"

PARENT_ID: Final = "PARENT_EXECUTION"
GHV_ID: Final = "PARENT_EXECUTION_GHV"
CAUSAL_GRAPH_ID: Final = "PARENT_EXECUTION_CURRENT_CAUSAL_GRAPH"
GHOSV_ID: Final = "PARENT_EXECUTION_GHOSV"
INSTRUMENT_IDS: Final = {
    "ghv_id": GHV_ID,
    "causal_graph_id": CAUSAL_GRAPH_ID,
    "ghosv_id": GHOSV_ID,
}

AUTHORITY: Final = "NONE"
ACTIVATION: Final = "DISABLED"
DOUBLE_PLAY_FULL_OWNER_LOCK: Final = "LEVEL_3"

STATUS_ADMITTED: Final = "ADMITTED"
STATUS_DISCLOSURE_SCOPE_ABSENT: Final = "DISCLOSURE_SCOPE_ABSENT"
STATUS_LOADER_REJECT: Final = "LOADER_REJECT"
STATUS_UNEXPECTED_MEMBERSHIP_ACCEPTED: Final = "UNEXPECTED_MEMBERSHIP_ACCEPTED"
STATUS_REJECTED: Final = "REJECTED"

CLASSIFICATION_OBSERVED: Final = "OBSERVED"
CLASSIFICATION_UNKNOWN: Final = "UNKNOWN"

OBSERVED_FIELDS: Final = frozenset(
    {"subject_id", "classification", "path", "symbol", "start_line", "end_line"}
)
UNKNOWN_FIELDS: Final = frozenset({"subject_id", "classification", "unknown_reason"})
GIT_READ_COMMANDS: Final = frozenset({"ls-tree", "show"})
