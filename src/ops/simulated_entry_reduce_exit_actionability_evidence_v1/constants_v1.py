"""Constants for CAPABILITY_7_1_SIMULATED_ENTRY_REDUCE_EXIT_ACTIONABILITY_EVIDENCE_V1."""

from __future__ import annotations

from pathlib import Path

from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
    CANONICAL_UP_DISTANCE,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
    FROZEN_ADVERSE_EXIT_DISTANCE,
    FROZEN_PROFIT_PROTECTION_DISTANCE,
)

CAPABILITY_ID = "CAPABILITY_7_1_SIMULATED_ENTRY_REDUCE_EXIT_ACTIONABILITY_EVIDENCE_V1"
SCHEMA_VERSION = "simulated_entry_reduce_exit_actionability_evidence.v1"
PRODUCER_VERSION = "simulated_entry_reduce_exit_actionability_evidence.v1"
PACKAGE_MARKER = "SIMULATED_ENTRY_REDUCE_EXIT_ACTIONABILITY_EVIDENCE_V1=true"
OWNER = "ops.simulated_entry_reduce_exit_actionability_evidence_v1"
STATE_VERSION = "v1"
SINGLE_WRITER_IDENTITY = "cap71_actionability_evidence_writer_v1"

CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = False
RUNTIME_ACTIVATED = False
LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
FORCED_INTENT_ALLOWED = False
DIRECT_INTENT_INJECTION_ALLOWED = False
DIRECT_FILL_INJECTION_ALLOWED = False
MASTER_V2_BYPASS_ALLOWED = False
DOUBLE_PLAY_BYPASS_ALLOWED = False
COMPOSITION_BYPASS_ALLOWED = False
RISK_BYPASS_ALLOWED = False
SAFETY_BYPASS_ALLOWED = False
EXIT_POLICY_BYPASS_ALLOWED = False
SIMULATED_EXECUTION_BYPASS_ALLOWED = False
POSITION_FLIP_ALLOWED = False

# Reuse Cap 6.3 / 6.5 frozen numerics — no new trading thresholds.
ADVERSE_EXIT_DISTANCE = float(FROZEN_ADVERSE_EXIT_DISTANCE)
PROFIT_PROTECTION_DISTANCE = float(FROZEN_PROFIT_PROTECTION_DISTANCE)
TIME_EXIT_MAX_HOLD_SECONDS = float(CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS)
UP_DISTANCE = float(CANONICAL_UP_DISTANCE)
CANONICAL_ADVERSE = float(CANONICAL_ADVERSE_EXIT_DISTANCE)

PRODUCTIVE_HOST = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_ENTRY_CALLER = (
    "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0"
)
PRODUCTIVE_REDUCE_CALLER = PRODUCTIVE_ENTRY_CALLER
PRODUCTIVE_EXIT_CALLER = (
    "ops.exit_policy_producer_binding_v1.host_binding_v1.evaluate_host_exit_policy_producers_v1"
)
SIMULATED_EXECUTION_CALLER = (
    "ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1."
    "apply_intended_action_via_canonical_accounting_v1"
)
ACCOUNTING_CALLER = (
    "ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1."
    "AccountingSessionV1.apply_fill"
)
PERSISTENCE_CALLER = (
    "ops.full_decision_path_atomic_restart_closure_v1.persistence_v1."
    "commit_decision_path_atomic_transaction_v1"
)
RECONCILIATION_CALLER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1."
    "decision_economics_cycle_bridge_v1.ensure_productive_reconciliation_startup_gate_v1"
)

PREDECESSOR_CAPABILITIES = (
    "CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1",
    "CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1",
    "CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1",
    "CAPABILITY_6_4_FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1",
    "CAPABILITY_6_5_EXIT_POLICY_PRODUCER_BINDING_V1",
)

MANIFEST_FILENAME = "MANIFEST.sha256"
EVIDENCE_FILENAME = "simulated_entry_reduce_exit_actionability_evidence_v1.json"
RESULT_FILENAME = "simulated_entry_reduce_exit_actionability_result_v1.json"
GATE_FILENAME = "actionability_gate_results_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
AUTHORITY_MATRIX_FILENAME = "authority_evidence_matrix_v1.json"
LIFECYCLE_FIXTURE_FILENAME = "lifecycle_fixture_spec_v1.json"
LONG_TRACE_FILENAME = "long_lifecycle_trace_v1.json"
SHORT_TRACE_FILENAME = "short_lifecycle_trace_v1.json"
REDUCE_TRACE_FILENAME = "reduce_lifecycle_trace_v1.json"
RESTART_TRACE_FILENAME = "restart_recovery_traces_v1.json"
INTENT_LEDGER_FILENAME = "entry_reduce_exit_intent_ledger_v1.jsonl"
FILL_LEDGER_FILENAME = "fill_ledger_v1.jsonl"
FEE_SLIPPAGE_LEDGER_FILENAME = "fee_slippage_ledger_v1.jsonl"
ACCOUNTING_RECON_FILENAME = "accounting_reconstruction_v1.json"
PORTFOLIO_RECON_FILENAME = "portfolio_reconstruction_v1.json"
RECONCILIATION_FILENAME = "reconciliation_results_v1.json"
REPLAY_DIGEST_FILENAME = "deterministic_replay_digest_comparison_v1.json"
SAFETY_PROOF_FILENAME = "safety_risk_exit_precedence_proof_v1.json"
NO_ORDER_PROOF_FILENAME = "no_order_boundary_proof_v1.json"

FEATURE_WARMUP_SEED_LONG = (3500.0, 3501.0, 3502.0)
FEATURE_WARMUP_SEED_SHORT = (3300.0, 3301.0, 3302.0)

CALL_GRAPH_V1 = (
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
    "exit_policy_producer_evaluation",
    "master_v2_double_play_integrated_offline_replay",
    "dynamic_scope_transition",
    "canonical_confirmation_state_commit",
    "canonical_dynamic_scope_state_commit",
    "decision_path_atomic_runtime_commit",
    "exit_policy_state_commit",
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
    "ENTRY_PATH_RUNTIME_REACHABLE",
    "ENTRY_INTENT_OBSERVED",
    "ENTRY_SIMULATED_FILL_OBSERVED",
    "ENTRY_ACCOUNTING_APPLIED",
    "ENTRY_PORTFOLIO_PERSISTED",
    "ENTRY_RESTART_RECONSTRUCTED",
    "ENTRY_END_TO_END_EVIDENCE_PROVEN",
    "EXIT_PATH_RUNTIME_REACHABLE",
    "EXIT_INDEPENDENCE_PROVEN",
    "EXIT_INTENT_OBSERVED",
    "EXIT_SIMULATED_FILL_OBSERVED",
    "EXIT_ACCOUNTING_APPLIED",
    "EXIT_PORTFOLIO_PERSISTED",
    "EXIT_RESTART_RECONSTRUCTED",
    "EXIT_END_TO_END_EVIDENCE_PROVEN",
    "LONG_LIFECYCLE_PROVEN",
    "SHORT_LIFECYCLE_PROVEN",
    "PARTIAL_REDUCE_LIFECYCLE_PROVEN",
    "ADVERSE_EXIT_PROVEN",
    "PROFIT_EXIT_PROVEN",
    "TIME_OR_INVALIDATION_EXIT_PROVEN",
    "NONZERO_FEE_EVIDENCE_PROVEN",
    "NONZERO_SLIPPAGE_EVIDENCE_PROVEN",
    "ACCOUNTING_RECONSTRUCTION_MATCH",
    "PORTFOLIO_RECONSTRUCTION_MATCH",
    "REALIZED_PNL_RECONSTRUCTION_MATCH",
    "DECISION_PATH_RESTART_PROVEN",
    "RESTART_DURING_OPEN_POSITION_PROVEN",
    "RESTART_DURING_CONFIRMATION_PROVEN",
    "RESTART_DURING_DYNAMIC_SCOPE_PROVEN",
    "NO_DUPLICATE_CONFIRMATION_ADVANCE",
    "NO_DUPLICATE_SCOPE_TRANSITION",
    "NO_DUPLICATE_ENTRY_INTENT",
    "NO_DUPLICATE_REDUCE_INTENT",
    "NO_DUPLICATE_EXIT_INTENT",
    "NO_DUPLICATE_ENTRY_FILL",
    "NO_DUPLICATE_REDUCE_FILL",
    "NO_DUPLICATE_EXIT_FILL",
    "NO_DUPLICATE_FEE_APPLICATION",
    "NO_DUPLICATE_SLIPPAGE_APPLICATION",
    "NO_LOST_EXIT_TRIGGER",
    "NO_PORTFOLIO_STATE_ROLLBACK",
    "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART",
    "EVIDENCE_RECOVERY_IDEMPOTENT",
    "DETERMINISTIC_REPLAY_PROVEN",
    "GOLDEN_VECTOR_PARITY_PASS",
    "CALL_ORDER_PARITY_PROVEN",
    "INPUT_OUTPUT_PARITY_PROVEN",
    "STATE_TRANSITION_PARITY_PROVEN",
    "DECISION_REASON_PARITY_PROVEN",
    "RISK_PARITY_PROVEN",
    "SAFETY_PARITY_PROVEN",
    "EXIT_PRECEDENCE_PARITY_PROVEN",
    "CORE_LOGIC_UNCHANGED",
    "EFFECTIVE_NUMERIC_VALUES_UNCHANGED",
    "EVIDENCE_VERIFIER_PASS",
    "NETWORK_SESSION_STARTED",
    "AUTHORIZATION_CONSUMED",
    "ACTIVATION_CHANGED",
    "ORDER_SIDE_EFFECT_OCCURRED",
    "POSITION_FLIP_ALLOWED",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
