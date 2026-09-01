"""Versioned enumerations for the offline DDO contract foundation v0.

Only tokens that are either (a) explicitly named in the AUTHORITY=NONE
Blueprint / Implementation-Completeness addendum, or (b) the explicit
UNKNOWN sentinel, are bound here. Existing repo reason-code dialects are
not copied or normalized.
"""

from __future__ import annotations

from typing import Final

UNKNOWN: Final[str] = "UNKNOWN"

ENUM_COMPATIBILITY_POLICY_V0: Final[str] = "FAIL_CLOSED_UNKNOWN_VALUE"
SCHEMA_VERSION_COMPATIBILITY_POLICY_V0: Final[str] = "FAIL_CLOSED_UNSUPPORTED_VERSION"

# Blueprint page 3: first-class decision types. TRADE-specific tokens are OPEN.
DECISION_TYPE_V0: Final[tuple[str, ...]] = (
    "NO_ENTRY",
    "NO_EXIT",
    "BULL_TO_BEAR",
    "BEAR_TO_BULL",
    "STALE_BLOCK",
    "RISK_BLOCK",
    "KILL_SWITCH",
    "RECONCILIATION_BLOCK",
    "DYNAMIC_SCOPE_TRANSITION",
    "DYNAMIC_SCOPE_NON_TRANSITION",
    UNKNOWN,
)

# Blueprint section 46 names canonical NO_ACTION as a DecisionEvent result.
# Other result tokens remain unbound in v0.
DECISION_RESULT_V0: Final[tuple[str, ...]] = (
    "NO_ACTION",
    UNKNOWN,
)

INCIDENT_CLASS_V0: Final[tuple[str, ...]] = (
    "KILL_SWITCH",
    "STALE",
    "RECONCILIATION",
    "RISK",
    UNKNOWN,
)

# Blueprint KillSwitch classification. Optional on IncidentRecord; not computed.
KILL_SWITCH_CORRECTNESS_V0: Final[tuple[str, ...]] = (
    "TRUE_POSITIVE",
    "FALSE_POSITIVE",
    "FALSE_NEGATIVE",
    "TRUE_NEGATIVE",
    UNKNOWN,
)

KILL_SWITCH_TIMING_LABEL_V0: Final[tuple[str, ...]] = (
    "TOO_EARLY",
    "ACCEPTABLE",
    "TOO_LATE",
    UNKNOWN,
)

# Blueprint stale post-event attribution classes. Optional; UNKNOWN admissible.
STALE_ROOT_CAUSE_V0: Final[tuple[str, ...]] = (
    "VENUE_FEED_DELAY",
    "NETWORK_DELAY",
    "LOCAL_CONSUMER_BACKLOG",
    "TIMESTAMP_DEFECT",
    "CLOCK_SKEW",
    "MISSING_OBSERVATION",
    "PARSER_SCHEMA_DEFECT",
    "INTERNAL_PROCESSING_LATENCY",
    UNKNOWN,
)

# Blueprint section 7 root_cause family. Optional on OutcomeRecord.
OUTCOME_ROOT_CAUSE_V0: Final[tuple[str, ...]] = (
    "MARKET",
    "DATA",
    "INFRASTRUCTURE",
    "POLICY",
    "EXECUTION",
    "OPERATOR",
    UNKNOWN,
)

COUNTERFACTUAL_ADMISSIBILITY_V0: Final[tuple[str, ...]] = (
    "OBSERVED",
    "REPLAYABLE",
    "MODELLED",
    "UNAVAILABLE",
    UNKNOWN,
)

OUTCOME_LINK_STATUS_V0: Final[tuple[str, ...]] = (
    "ABSENT",
    "PRESENT",
    UNKNOWN,
)

RECORD_TYPE_V0: Final[tuple[str, ...]] = (
    "decision_event",
    "incident_record",
    "outcome_record",
)

NULLABILITY_V0: Final[tuple[str, ...]] = (
    "REQUIRED",
    "OPTIONAL",
    "CONDITIONALLY_REQUIRED",
)

OPEN_UNBOUND_ENUMS_V0: Final[tuple[str, ...]] = (
    "DECISION_TYPE_TRADE_SPECIFIC_TOKENS",
    "DECISION_RESULT_BEYOND_NO_ACTION_AND_UNKNOWN",
)

DECISION_TYPE_TRADE_SPECIFIC_STATUS: Final[str] = "OPEN"
DECISION_RESULT_EXTENDED_STATUS: Final[str] = "OPEN"
