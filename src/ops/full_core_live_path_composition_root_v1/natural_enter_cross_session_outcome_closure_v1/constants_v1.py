"""Constants for Natural-Enter cross-session outcome closure v1."""

from __future__ import annotations

from typing import Final

OWNER: Final[str] = (
    "full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1"
)
PACKAGE_MARKER: Final[str] = "NATURAL_ENTER_CROSS_SESSION_OUTCOME_CLOSURE_V1"
SCHEMA_VERSION: Final[str] = "natural_enter_pending_outcome.v1"
EVENTS_LEDGER_BASENAME: Final[str] = "natural_enter_pending_outcome_events_v1.jsonl"
INDEX_BASENAME: Final[str] = "natural_enter_pending_outcome_index_v1.json"
CLOSURE_EVIDENCE_BASENAME: Final[str] = "natural_enter_pending_outcome_closure_evidence_v1.jsonl"
O4_STATE_DIRNAME: Final[str] = "natural_enter_pending_outcome_o4_v1"

DEFAULT_N_BARS_REQUIRED: Final[int] = 2
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
POST_COUNT: Final[int] = 0

STATUS_PENDING: Final[str] = "PENDING"
STATUS_IN_PROGRESS: Final[str] = "IN_PROGRESS"
STATUS_CLOSED: Final[str] = "CLOSED"
STATUS_FAILED_TERMINAL: Final[str] = "FAILED_TERMINAL"

EVENT_CREATED: Final[str] = "CREATED"
EVENT_BAR_INGESTED: Final[str] = "BAR_INGESTED"
EVENT_HORIZON_PROGRESS: Final[str] = "HORIZON_PROGRESS"
EVENT_CLOSED: Final[str] = "CLOSED"
EVENT_FAILED: Final[str] = "FAILED"

EVIDENCE_CLASS_REAL_PUBLIC: Final[str] = "REAL_PUBLIC_OBSERVATION"
EVIDENCE_CLASS_TEST_FIXTURE: Final[str] = "TEST_FIXTURE_EXPLICIT"

OPEN_STATUSES: Final[frozenset[str]] = frozenset({STATUS_PENDING, STATUS_IN_PROGRESS})
