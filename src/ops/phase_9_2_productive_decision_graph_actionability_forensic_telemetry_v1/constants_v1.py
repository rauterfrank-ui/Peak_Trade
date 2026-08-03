"""Constants for Phase 9.2 productive decision-graph actionability forensic telemetry."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "PHASE_9_2_PRODUCTIVE_DECISION_GRAPH_ACTIONABILITY_FORENSIC_TELEMETRY_V1"
TASK_ID = "IMPLEMENT_PRODUCTIVE_DECISION_GRAPH_ACTIONABILITY_FORENSIC_TELEMETRY_V1"
OWNER = "ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1"
PACKAGE_MARKER = "PHASE_9_2_PRODUCTIVE_DECISION_GRAPH_ACTIONABILITY_FORENSIC_TELEMETRY_V1=true"
SCHEMA_VERSION = "productive_decision_stage_observation.v1"
PRODUCER_VERSION = "productive_decision_graph_actionability_forensic_telemetry.v1"
EVENT_SCHEMA = "ProductiveDecisionStageObservationV1"
EVENT_VERSION = "v1"
STATE_VERSION = "v1"
SINGLE_WRITER_IDENTITY = "phase92_actionability_forensic_telemetry_writer_v1"

CORE_LOGIC_CHANGE = False
CONFIG_CHANGED = False
TRADING_THRESHOLDS_CHANGED = False
DECISION_PRECEDENCE_CHANGED = False
PARALLEL_DECISION_ENGINE_CREATED = False
TELEMETRY_DECISION_AUTHORITY = False
TELEMETRY_MUTATES_RUNTIME_STATE = False
TELEMETRY_MUTATES_DECISION = False
TELEMETRY_FAILURE_CHANGES_DECISION = False
TELEMETRY_REASON_CODES_CANONICAL_OR_MAPPED = True
SENSITIVE_VALUES_REDACTED = True
DIAGNOSTIC_ONLY = True
NO_THRESHOLD_RECOMMENDATION_IN_RUNTIME = True
NO_COUNTERFACTUAL_DECISION_USED_PRODUCTIVELY = True
NO_FLOAT_FALLBACK = True
MISSING_VALUES_EXPLICIT = True
ONE_PRIMARY_TERMINAL_REASON_PER_CYCLE = True
SECONDARY_REASONS_MAY_BE_RECORDED = True
PRIMARY_REASON_FOLLOWS_CALL_ORDER = True
PRIMARY_REASON_MUST_MATCH_ACTUAL_DECISION_PATH = True

FORCED_INTENT_ALLOWED = False
DIRECT_FILL_INJECTION_ALLOWED = False
MASTER_V2_BYPASS_ALLOWED = False
DOUBLE_PLAY_BYPASS_ALLOWED = False
COMPOSITION_BYPASS_ALLOWED = False
RISK_BYPASS_ALLOWED = False
SAFETY_BYPASS_ALLOWED = False
REAL_NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
SESSION_GO_ISSUANCE_ALLOWED = False
LIVE_TRADING_ALLOWED = False
TESTNET_ALLOWED = False
PAPER_EXCHANGE_ORDERS_ALLOWED = False
EXCHANGE_CREDENTIAL_USE_ALLOWED = False
REAL_CAPITAL_MOVEMENT_ALLOWED = False

PRODUCTIVE_HOST = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_CALLER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1."
    "decision_economics_cycle_bridge_v1.run_bridge_cycle_v1"
)
PRODUCTIVE_DECISION_AUTHORITY = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)

# Frozen productive actionability call order (instrumentation stages).
ACTIONABILITY_CALL_ORDER_V1: tuple[str, ...] = (
    "instrument_selection",
    "public_market_observation",
    "observation_identity",
    "distinct_observation_acceptance",
    "features",
    "typed_volatility_presence",
    "market_state_bull_bear",
    "directional_confirmation",
    "master_v2",
    "double_play",
    "dynamic_scope",
    "survival",
    "suitability",
    "composition",
    "risk",
    "safety",
    "exit_policy",
    "canonical_intent",
    "simulated_execution",
)

TERMINAL_OUTCOMES: tuple[str, ...] = (
    "ENTRY_INTENT",
    "REDUCE_INTENT",
    "EXIT_INTENT",
    "HOLD",
    "BLOCKED",
    "NO_SAMPLE",
    "DUPLICATE_SAMPLE",
    "STALE_SAMPLE",
    "FAIL_CLOSED",
)

PRIMARY_REASON_CLASSES: tuple[str, ...] = (
    "BLOCKED_BY_MISSING_MARKET_TRUTH",
    "BLOCKED_BY_DUPLICATE_OBSERVATION",
    "BLOCKED_BY_STALE_OBSERVATION",
    "BLOCKED_BY_FEATURES",
    "BLOCKED_BY_VOLATILITY_PRESENCE",
    "BLOCKED_BY_MARKET_STATE",
    "BLOCKED_BY_CONFIRMATION",
    "BLOCKED_BY_MASTER_V2",
    "BLOCKED_BY_DOUBLE_PLAY",
    "BLOCKED_BY_DYNAMIC_SCOPE",
    "BLOCKED_BY_SURVIVAL",
    "BLOCKED_BY_SUITABILITY",
    "BLOCKED_BY_COMPOSITION",
    "BLOCKED_BY_RISK",
    "BLOCKED_BY_SAFETY",
    "BLOCKED_BY_EXIT_PRECEDENCE",
    "HOLD_BY_CANONICAL_DECISION",
    "NO_ACTIONABLE_CHANGE",
    "FAIL_CLOSED_INTERNAL_ERROR",
)

# Call-order index of the stage that corresponds to each primary reason class.
PRIMARY_REASON_STAGE_INDEX: dict[str, int] = {
    "BLOCKED_BY_MISSING_MARKET_TRUTH": 1,
    "BLOCKED_BY_DUPLICATE_OBSERVATION": 3,
    "BLOCKED_BY_STALE_OBSERVATION": 3,
    "BLOCKED_BY_FEATURES": 4,
    "BLOCKED_BY_VOLATILITY_PRESENCE": 5,
    "BLOCKED_BY_MARKET_STATE": 6,
    "BLOCKED_BY_CONFIRMATION": 7,
    "BLOCKED_BY_MASTER_V2": 8,
    "BLOCKED_BY_DOUBLE_PLAY": 9,
    "BLOCKED_BY_DYNAMIC_SCOPE": 10,
    "BLOCKED_BY_SURVIVAL": 11,
    "BLOCKED_BY_SUITABILITY": 12,
    "BLOCKED_BY_COMPOSITION": 13,
    "BLOCKED_BY_RISK": 14,
    "BLOCKED_BY_SAFETY": 15,
    "BLOCKED_BY_EXIT_PRECEDENCE": 16,
    "HOLD_BY_CANONICAL_DECISION": 17,
    "NO_ACTIONABLE_CHANGE": 17,
    "FAIL_CLOSED_INTERNAL_ERROR": 0,
}

GATE_COUNTER_KEYS: tuple[str, ...] = (
    "TOTAL_CYCLES",
    "TOTAL_MARKET_OBSERVATIONS",
    "DISTINCT_OBSERVATIONS",
    "DUPLICATE_OBSERVATIONS",
    "MISSING_OBSERVATIONS",
    "STALE_OBSERVATIONS",
    "FEATURES_EVALUATED",
    "FEATURES_BLOCKED",
    "VOLATILITY_PRESENT",
    "VOLATILITY_MISSING",
    "VOLATILITY_STALE_DIAGNOSTIC",
    "BULL_STATE_COUNT",
    "BEAR_STATE_COUNT",
    "UNCLASSIFIED_MARKET_STATE_COUNT",
    "CONFIRMATION_OBSERVE_COUNT",
    "CONFIRMATION_CANDIDATE_COUNT",
    "CONFIRMATION_CONFIRMED_COUNT",
    "CONFIRMATION_INVALIDATED_COUNT",
    "CONFIRMATION_EXPIRED_COUNT",
    "CONFIRMATION_BLOCKED_COUNT",
    "MASTER_V2_LONG_COUNT",
    "MASTER_V2_SHORT_COUNT",
    "MASTER_V2_HOLD_COUNT",
    "MASTER_V2_BLOCKED_COUNT",
    "DOUBLE_PLAY_LONG_COUNT",
    "DOUBLE_PLAY_SHORT_COUNT",
    "DOUBLE_PLAY_HOLD_COUNT",
    "DOUBLE_PLAY_BLOCKED_COUNT",
    "DYNAMIC_SCOPE_EVALUATED_COUNT",
    "DYNAMIC_SCOPE_CREATED_COUNT",
    "DYNAMIC_SCOPE_TRANSITION_COUNT",
    "DYNAMIC_SCOPE_BLOCKED_COUNT",
    "DYNAMIC_SCOPE_NOT_REACHED_COUNT",
    "SURVIVAL_PASS_COUNT",
    "SURVIVAL_BLOCK_COUNT",
    "SUITABILITY_PASS_COUNT",
    "SUITABILITY_BLOCK_COUNT",
    "COMPOSITION_PASS_COUNT",
    "COMPOSITION_BLOCK_COUNT",
    "RISK_PASS_COUNT",
    "RISK_VETO_COUNT",
    "SAFETY_PASS_COUNT",
    "SAFETY_VETO_COUNT",
    "EXIT_POLICY_EVALUATED_COUNT",
    "EXIT_POLICY_TRIGGERED_COUNT",
    "EXIT_POLICY_BLOCKED_COUNT",
    "ENTRY_INTENT_COUNT",
    "REDUCE_INTENT_COUNT",
    "EXIT_INTENT_COUNT",
    "HOLD_COUNT",
    "NO_INTENT_COUNT",
)

ENTRY_FUNNEL_KEYS: tuple[str, ...] = (
    "accepted_observation_count",
    "features_ready_count",
    "market_state_classified_count",
    "confirmation_candidate_count",
    "confirmation_confirmed_count",
    "master_v2_directional_count",
    "double_play_directional_count",
    "dynamic_scope_ready_count",
    "survival_pass_count",
    "suitability_pass_count",
    "composition_pass_count",
    "risk_pass_count",
    "safety_pass_count",
    "entry_actionable_count",
    "entry_intent_count",
)

EXIT_FUNNEL_KEYS: tuple[str, ...] = (
    "open_position_cycles",
    "exit_policy_evaluated_count",
    "exit_policy_triggered_count",
    "risk_reduce_count",
    "safety_exit_count",
    "reduce_intent_count",
    "exit_intent_count",
)

MANIFEST_FILENAME = "MANIFEST.sha256"
SUMMARY_FILENAME = "SUMMARY.json"
STAGE_EVENTS_FILENAME = "stage_observations.jsonl"
CYCLE_TERMINALS_FILENAME = "cycle_terminals.jsonl"
AGGREGATE_COUNTERS_FILENAME = "aggregate_counters_v1.json"
TERMINAL_BLOCKER_HISTOGRAM_FILENAME = "terminal_blocker_histogram_v1.json"
SECONDARY_REASON_HISTOGRAM_FILENAME = "secondary_reason_histogram_v1.json"
ENTRY_FUNNEL_FILENAME = "entry_funnel_v1.json"
EXIT_FUNNEL_FILENAME = "exit_funnel_v1.json"
DISTANCE_STATS_FILENAME = "distance_to_actionability_stats_v1.json"
CALL_ORDER_PROOF_FILENAME = "call_order_proof_v1.json"
GOLDEN_PARITY_PROOF_FILENAME = "golden_parity_proof_v1.json"
AUTHORITY_MATRIX_FILENAME = "authority_matrix_v1.json"
VERIFIER_RESULT_FILENAME = "verifier_result_v1.json"
CONFIG_DIGEST_FILENAME = "config_digest_v1.json"
REPLAY_DIGEST_FILENAME = "deterministic_replay_digest_v1.json"
BOTTLENECK_INTERPRETATION_FILENAME = "bottleneck_interpretation_v1.json"

EVIDENCE_DIRNAME = (
    "capability_phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1"
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
