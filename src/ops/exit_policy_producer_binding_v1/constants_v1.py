"""Constants for CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1."""

from __future__ import annotations

from pathlib import Path

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_UP_DISTANCE,
)

CAPABILITY_ID = "CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1"
SCHEMA_VERSION = "exit_policy_producer_binding.v1"
PRODUCER_VERSION = "exit_policy_producer_binding.v1"
PACKAGE_MARKER = "EXIT_POLICY_PRODUCER_BINDING_V1=true"
OWNER = "ops.exit_policy_producer_binding_v1"
AUTHORITY_OWNER = OWNER
STATE_VERSION = "v1"
SINGLE_WRITER_IDENTITY = "cap65_exit_policy_producer_writer_v1"

CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = False
RUNTIME_ACTIVATED = False
LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
FORCED_EXIT_SIGNAL_ALLOWED = False
FORCED_INTENT_ALLOWED = False
DIRECT_FILL_INJECTION_ALLOWED = False
EXIT_END_TO_END_EVIDENCE_PROVEN = False
POSITION_FLIP_ALLOWED = False

# Reuse Cap 6.3 frozen distances — no new trading numerics introduced.
FROZEN_ADVERSE_EXIT_DISTANCE = float(CANONICAL_ADVERSE_EXIT_DISTANCE)
FROZEN_PROFIT_PROTECTION_DISTANCE = float(CANONICAL_UP_DISTANCE)

# Cap 6.5 producer-binding constant for wallclock time-exit anchor duration.
# Binds foundation helper wallclock_time_exit_due_v1; not a Cap 6.3 decision-config key.
CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS = 3600.0

PRODUCTIVE_HOST = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_DECISION_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
ENTRY_EXIT_POLICY_OWNER = (
    "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0"
)
ADVERSE_PRODUCER_OWNER = (
    "trading.master_v2.scope_event_generator_scenario_binding_adapter_v0."
    "derive_scope_adverse_exit_signal_v0"
)
ADVERSE_RESOLVE_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "resolve_integrated_scope_adverse_exit_signal_v0"
)
SAFETY_PRODUCER_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2."
    "safety_binding_v2.evaluate_bridge_safety_v2"
)
TIME_FOUNDATION_OWNER = (
    "trading.market_state.time_sample_epoch_semantics_v1.wallclock_time_exit_due_v1"
)
PREDECESSOR_CAPABILITY = "CAPABILITY_6_4_FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1"

CALL_GRAPH_EXIT_PRODUCER_STEP = "exit_policy_producer_evaluation"
CALL_GRAPH_EXIT_STATE_COMMIT_STEP = "exit_policy_state_commit"

EXIT_STATE_FILENAME = "exit_policy_state_v1.json"
COMMIT_MARKER_FILENAME = "exit_policy_commit_marker_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
WRITER_LOCK_FILENAME = "exit_policy_writer.lock"
STAGING_DIRNAME_PREFIX = ".cap65_exit_policy_staging_"
EVIDENCE_FILENAME = "exit_policy_producer_binding_evidence_v1.json"
RESULT_FILENAME = "exit_policy_producer_binding_result_v1.json"
GATE_FILENAME = "exit_policy_gate_results_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
AUTHORITY_MATRIX_FILENAME = "exit_authority_matrix_v1.json"

CANONICAL_EXIT_PRECEDENCE = (
    "safety_authority",
    "hard_risk",
    "reconciliation",
    "mandatory_exit",
    "existing_position",
    "reversal",
    "new_entry",
    "observe",
    "no_action",
)

MANDATORY_EXIT_PRIORITY = (
    "adverse_scope_exit",
    "profit_protection_exit",
    "time_exit",
    "strategy_invalidation_exit",
)

CALL_GRAPH_BEFORE = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "canonical_decision_runtime_config_bind",
    "okx_public_market_data",
    "distinct_market_observation_acceptor",
    "observation_acceptance_result",
    "feature_pipeline",
    "regime_pipeline",
    "directional_confirmation_progress",
    "directional_assessment_confirmation_integration",
    "previous_canonical_runtime_scope_state",
    "master_v2_double_play_integrated_offline_replay",
    "dynamic_scope_transition",
    "canonical_confirmation_state_commit",
    "canonical_dynamic_scope_state_commit",
    "decision_path_atomic_runtime_commit",
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
    "analytical_simulated_execution",
    "simulated_fill_fee_slippage",
    "canonical_futures_accounting",
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    "risk_state_from_accounting",
    "simulated_economics_no_order_path",
    "pending_evidence_cursor_commit",
    "evidence",
    "full_economic_reconstruction_verifier",
)

CALL_GRAPH_AFTER = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "canonical_decision_runtime_config_bind",
    "okx_public_market_data",
    "distinct_market_observation_acceptor",
    "observation_acceptance_result",
    "feature_pipeline",
    "regime_pipeline",
    "directional_confirmation_progress",
    "directional_assessment_confirmation_integration",
    "previous_canonical_runtime_scope_state",
    CALL_GRAPH_EXIT_PRODUCER_STEP,
    "master_v2_double_play_integrated_offline_replay",
    "dynamic_scope_transition",
    "canonical_confirmation_state_commit",
    "canonical_dynamic_scope_state_commit",
    "decision_path_atomic_runtime_commit",
    CALL_GRAPH_EXIT_STATE_COMMIT_STEP,
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
    "analytical_simulated_execution",
    "simulated_fill_fee_slippage",
    "canonical_futures_accounting",
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    "risk_state_from_accounting",
    "simulated_economics_no_order_path",
    "pending_evidence_cursor_commit",
    "evidence",
    "full_economic_reconstruction_verifier",
)

REQUIRED_GATE_FLAGS = (
    "EXIT_POLICY_PRODUCERS_BOUND",
    "PLACEHOLDER_FALSE_SIGNAL_USED_AS_UNBOUND_STUB",
    "EXIT_PATH_RUNTIME_REACHABLE",
    "EXIT_INDEPENDENCE_PROVEN",
    "EXIT_PRECEDENCE_EXACT",
    "SAFETY_EXIT_PRECEDES_ALPHA",
    "HARD_RISK_REDUCE_PRECEDES_ALPHA",
    "RECONCILIATION_PRECEDES_ALPHA",
    "MANDATORY_EXIT_PRECEDES_NEW_ENTRY",
    "POSITION_FLIP_ALLOWED",
    "EXIT_POLICY_STATE_RESTART_PROVEN",
    "NO_DUPLICATE_EXIT_INTENT",
    "NO_DUPLICATE_EXIT_FILL",
    "NO_LOST_EXIT_TRIGGER",
    "DUPLICATE_OBSERVATION_DOES_NOT_TRIGGER_NEW_EXIT",
    "RUNTIME_RESTART_DOES_NOT_RESET_EXIT_STATE",
    "EXIT_RISK_SAFETY_STATE_PRESERVED",
    "CORE_LOGIC_UNCHANGED",
    "GOLDEN_VECTOR_PARITY_PASS",
    "EXIT_PRECEDENCE_PARITY_PROVEN",
    "EFFECTIVE_NUMERIC_VALUES_UNCHANGED",
    "DETERMINISTIC_REPLAY_PROVEN",
    "FAILURE_INJECTION_PROVEN",
    "EVIDENCE_VERIFIED",
    "RUNTIME_NOT_ACTIVATED",
    "EXIT_END_TO_END_EVIDENCE_PROVEN",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
