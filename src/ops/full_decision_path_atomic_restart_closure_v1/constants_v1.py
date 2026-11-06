"""Constants for CAPABILITY_6_4_FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "CAPABILITY_6_4_FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1"
SCHEMA_VERSION = "full_decision_path_atomic_restart_closure.v1"
PRODUCER_VERSION = "full_decision_path_atomic_restart_closure.v1"
PACKAGE_MARKER = "FULL_DECISION_PATH_ATOMIC_RESTART_CLOSURE_V1=true"
OWNER = "ops.full_decision_path_atomic_restart_closure_v1"
AUTHORITY_OWNER = OWNER
STATE_VERSION = "v1"
SINGLE_WRITER_IDENTITY = "cap64_decision_path_atomic_writer_v1"

ATOMICITY_MODEL = "VERSIONED_MULTI_RECORD_TRANSACTION_WITH_COMMIT_MARKER_AND_REPLAY"
SERIALIZATION_ADAPTER_HAS_NO_DECISION_AUTHORITY = True
ONE_STATE_OWNER_PER_STATE_ROOT = True
ONE_AUTHORITATIVE_WRITER_PER_STATE_ROOT = True
NO_NEW_PARALLEL_STATE_MODEL = True
MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED = False
DOUBLE_PLAY_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED = False

CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = False
RUNTIME_ACTIVATED = False
LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False

PRODUCTIVE_HOST = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_DECISION_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
PREDECESSOR_CAPABILITY = "CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1"
PREDECESSOR_CAP61 = "CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1"
PREDECESSOR_CAP62 = "CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1"
PREDECESSOR_CAP31 = "CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1"

JOURNAL_FILENAME = "decision_path_wal_journal_v1.json"
COMMIT_MARKER_FILENAME = "decision_path_commit_marker_v1.json"
PENDING_EVIDENCE_FILENAME = "pending_evidence_cursor_v1.json"
TRANSACTION_INDEX_FILENAME = "decision_path_transaction_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
WRITER_LOCK_FILENAME = "decision_path_atomic_writer.lock"
STAGING_DIRNAME_PREFIX = ".cap64_decision_path_staging_"
EVIDENCE_FILENAME = "full_decision_path_atomic_restart_closure_evidence_v1.json"
RESULT_FILENAME = "full_decision_path_atomic_restart_closure_result_v1.json"
GATE_FILENAME = "decision_path_atomic_gate_results_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
STATE_ROOT_MATRIX_FILENAME = "state_root_classification_matrix_v1.json"

CALL_GRAPH_ATOMIC_COMMIT_STEP = "decision_path_atomic_runtime_commit"
CALL_GRAPH_PENDING_EVIDENCE_STEP = "pending_evidence_cursor_commit"

MEMBER_CONFIRMATION = "confirmation"
MEMBER_DYNAMIC_SCOPE = "dynamic_scope"
MEMBER_DECISION_CONFIG = "decision_config"
MEMBER_ACCOUNTING = "accounting_portfolio"
MEMBER_RECONCILIATION_REF = "reconciliation_ref"
MEMBER_SELECTION_REF = "selection_ref"
MEMBER_VOLATILITY_REF = "volatility_ref"

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
    "master_v2_double_play_integrated_offline_replay",
    "dynamic_scope_transition",
    "canonical_confirmation_state_commit",
    "canonical_dynamic_scope_state_commit",
    CALL_GRAPH_ATOMIC_COMMIT_STEP,
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
    CALL_GRAPH_PENDING_EVIDENCE_STEP,
    "evidence",
    "full_economic_reconstruction_verifier",
)

REQUIRED_GATE_FLAGS = (
    "DECISION_PATH_RESTART_PROVEN",
    "NO_DUPLICATE_CONFIRMATION_ADVANCE",
    "NO_DUPLICATE_SCOPE_ADVANCE",
    "NO_DUPLICATE_FILL",
    "NO_LOST_SCOPE_TRANSITION",
    "NO_PORTFOLIO_STATE_ROLLBACK",
    "NO_MIXED_STATE_ROOT_COMMIT",
    "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART",
    "DIGEST_MATCH_AFTER_RESTART",
    "CONFIG_DIGEST_MATCH_AFTER_RESTART",
    "EVIDENCE_RECOVERY_IDEMPOTENT",
    "RUNTIME_RESTART_DOES_NOT_RESET_TRADING_STATE",
    "SILENT_CONFIRMATION_REINITIALIZATION_FALSE",
    "SILENT_DYNAMIC_SCOPE_REINITIALIZATION_FALSE",
    "CORE_LOGIC_UNCHANGED",
    "GOLDEN_VECTOR_PARITY_PASS",
    "CALL_ORDER_PARITY_PROVEN",
    "INPUT_OUTPUT_PARITY_PROVEN",
    "STATE_TRANSITION_PARITY_PROVEN",
    "DECISION_REASON_PARITY_PROVEN",
    "MASTER_V2_PARITY_PROVEN",
    "DOUBLE_PLAY_PARITY_PROVEN",
    "BULL_BEAR_PARITY_PROVEN",
    "DYNAMIC_SCOPE_RULE_PARITY_PROVEN",
    "RISK_PARITY_PROVEN",
    "SAFETY_PARITY_PROVEN",
    "EXIT_PRECEDENCE_PARITY_PROVEN",
    "EFFECTIVE_NUMERIC_VALUES_UNCHANGED",
    "DETERMINISTIC_REPLAY_PROVEN",
    "FAILURE_INJECTION_PROVEN",
    "EVIDENCE_VERIFIED",
    "RUNTIME_NOT_ACTIVATED",
    "NO_LIVE_ORDER_PATH",
    "NO_TESTNET_ORDER_PATH",
    "NO_NETWORK_ACCESS",
    "AUTHORIZATION_NOT_CONSUMED",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
