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

# Explicit evaluation horizons. Numeric bar/count policy remains unbound.
EVALUATION_HORIZON_V0: Final[tuple[str, ...]] = (
    "DECISION_TIME",
    "IMMEDIATE_POST_EVENT",
    "EVENT_RECOVERY",
    "N_BARS",
    "POSITION_LIFECYCLE",
    UNKNOWN,
)

PROTECTED_CONDITION_V0: Final[tuple[str, ...]] = (
    "PRESENT",
    "ABSENT",
    UNKNOWN,
)

SAFETY_SCORE_V0: Final[tuple[str, ...]] = (
    "SAFETY_CONTRACT_SATISFIED",
    "SAFETY_CONTRACT_NOT_SATISFIED",
    "SAFETY_NOT_APPLICABLE",
    UNKNOWN,
)

DECISION_SCORE_V0: Final[tuple[str, ...]] = (
    "REPLAY_CLASSIFICATION_MATCH",
    UNKNOWN,
)

PROMOTION_CLASS_V0: Final[tuple[str, ...]] = (
    "P0",
    "P1",
    "P2",
    "P3",
)

GATE_RESULT_V0: Final[tuple[str, ...]] = (
    "PASS",
    "FAIL",
    "INSUFFICIENT_EVIDENCE",
    UNKNOWN,
)

SUPERVISOR_STATE_V0: Final[tuple[str, ...]] = (
    "STOPPED",
    "INITIALIZING",
    "SYNCING",
    "READY",
    "EVALUATING",
    "PLANNED",
    "PERMISSION_CHECK",
    "SUBMITTING",
    "RECONCILING",
    "OBSERVING",
    "WAITING",
    "DEGRADED",
    "RECOVERING",
    "HALTED",
)

SUPERVISOR_OUTCOME_V0: Final[tuple[str, ...]] = (
    "CONTINUE",
    "WAIT",
    "DEGRADE",
    "HALT",
    "RECOVER",
    "RETRY",
)

SUPERVISOR_EVENT_V0: Final[tuple[str, ...]] = (
    "authorized_start",
    "invariants_valid",
    "critical_invariant_fails",
    "fresh_state_proven",
    "recoverable_dependency_issue",
    "cycle_due",
    "canonical_no_action",
    "canonical_plan_candidate_produced",
    "plan_still_admissible",
    "ephemeral_predicates_true",
    "hard_predicate_false",
    "transport_outcome_known",
    "transport_outcome_ambiguous",
    "venue_truth_proven",
    "truth_not_provable_recoverable",
    "evidence_persisted_coherent",
    "recovery_policy_admits_attempt",
    "reproof_succeeds",
    "unrecoverable_invariant",
    "duplicate_cycle_invocation",
    UNKNOWN,
)

SUPERVISOR_ACTION_V0: Final[tuple[str, ...]] = (
    "create_cycle_epoch",
    "load_exact_versions",
    "persist_initialization_proof",
    "persist_failure",
    "persist_sync_proof",
    "record_degraded_reason",
    "allocate_unique_cycle_id",
    "persist_decision_event",
    "persist_decision_lineage",
    "freeze_plan_identity",
    "persist_permit_identity",
    "persist_deny_no_wire",
    "persist_exact_response",
    "forbid_resend_mark_ambiguity",
    "persist_reconciliation_proof",
    "no_risk_increase",
    "close_cycle",
    "bounded_recovery_action",
    "fail_closed",
    "no_wire",
    "collapse_duplicate_cycle",
)

RECORD_TYPE_V0: Final[tuple[str, ...]] = (
    "decision_event",
    "incident_record",
    "outcome_record",
    "counterfactual_record",
    "attribution_record",
    "learning_hypothesis",
    "candidate_artifact",
    "validation_evidence_pack",
    "promotion_policy",
    "promotion_eligibility_record",
    "release_artifact",
    "deployment_record",
    "rollback_record",
    "autonomy_cycle_record",
    "health_snapshot",
    "canonical_experiment_identity_ref",
    "drift_observation_record",
    "drift_assessment_record",
    "known_good_reference",
    "drift_policy",
)

NULLABILITY_V0: Final[tuple[str, ...]] = (
    "REQUIRED",
    "OPTIONAL",
    "CONDITIONALLY_REQUIRED",
)

VALIDATION_GATE_IDS_V0: Final[tuple[str, ...]] = (
    "provenance_complete",
    "deterministic_replay_pass",
    "walk_forward_pass",
    "monte_carlo_pass",
    "stress_pass",
    "fault_injection_pass",
    "safety_regression_pass",
    "authority_invariants_pass",
    "observability_non_regression_pass",
    "shadow_min_evidence_met",
    "economic_policy_pass",
    "rollback_ready",
    "compatibility_pass",
)

HARD_ELIGIBILITY_GATES_V0: Final[tuple[str, ...]] = (
    "safety_regression_pass",
    "authority_invariants_pass",
)

EXPERIMENT_IDENTITY_BINDING_STATUS_V0: Final[tuple[str, ...]] = (
    "BOUND",
    "UNKNOWN",
    "REJECTED_NONCANONICAL",
    "REJECTED_INCOMPLETE",
    "REJECTED_NONEQUIVALENT",
)

DRIFT_DOMAIN_V0: Final[tuple[str, ...]] = (
    "DATA_DRIFT",
    "FEATURE_DRIFT",
    "MODEL_OUTPUT_DRIFT",
    "PERFORMANCE_DRIFT",
    "CALIBRATION_DRIFT",
    "EXECUTION_OBSERVATION_DRIFT",
    "SCHEMA_DRIFT",
    "AUTHORITY_DRIFT",
    "SAFETY_DRIFT",
    UNKNOWN,
)

HARD_NON_COMPENSABLE_DRIFT_DOMAINS_V0: Final[frozenset[str]] = frozenset(
    {
        "AUTHORITY_DRIFT",
        "SAFETY_DRIFT",
    }
)

DRIFT_VERDICT_V0: Final[tuple[str, ...]] = (
    "DRIFT_DETECTED",
    "NO_DRIFT",
    "INSUFFICIENT_EVIDENCE",
    UNKNOWN,
)

DRIFT_REASON_CODE_V0: Final[tuple[str, ...]] = (
    "REFERENCE_MISMATCH",
    "HORIZON_EXCEEDED",
    "SCHEMA_INCOMPATIBLE",
    "AUTHORITY_REGRESSION",
    "SAFETY_REGRESSION",
    "INSUFFICIENT_EVIDENCE",
    UNKNOWN,
)

COMPATIBILITY_STATUS_V0: Final[tuple[str, ...]] = (
    "COMPATIBLE",
    "INCOMPATIBLE",
    UNKNOWN,
)

PRODUCER_FAILURE_SEMANTICS_V0: Final[tuple[str, ...]] = (
    "FAIL_CLOSED",
    "INSUFFICIENT_EVIDENCE",
    UNKNOWN,
)

OPEN_UNBOUND_ENUMS_V0: Final[tuple[str, ...]] = (
    "DECISION_TYPE_TRADE_SPECIFIC_TOKENS",
    "DECISION_RESULT_BEYOND_NO_ACTION_AND_UNKNOWN",
    "HEALTH_SNAPSHOT_OPAQUE_READINESS_TOKENS",
    "DEPLOYMENT_RESULT_TOKENS",
    "ROLLBACK_RESULT_TOKENS",
    "HYPOTHESIS_AUTHOR_KIND_TOKENS",
    "ECONOMIC_SCORE_NUMERIC_POLICY",
    "EVALUATION_HORIZON_NUMERIC_BAR_COUNT",
)

DECISION_TYPE_TRADE_SPECIFIC_STATUS: Final[str] = "OPEN"
DECISION_RESULT_EXTENDED_STATUS: Final[str] = "OPEN"
