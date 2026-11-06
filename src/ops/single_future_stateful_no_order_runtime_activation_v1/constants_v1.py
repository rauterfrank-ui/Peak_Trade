"""Constants for CAPABILITY_7_2_SINGLE_FUTURE_STATEFUL_NO_ORDER_RUNTIME_ACTIVATION_V1."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "CAPABILITY_7_2_SINGLE_FUTURE_STATEFUL_NO_ORDER_RUNTIME_ACTIVATION_V1"
SCHEMA_VERSION = "single_future_stateful_no_order_runtime_activation.v1"
PRODUCER_VERSION = "single_future_stateful_no_order_runtime_activation.v1"
PACKAGE_MARKER = "SINGLE_FUTURE_STATEFUL_NO_ORDER_RUNTIME_ACTIVATION_V1=true"
OWNER = "ops.single_future_stateful_no_order_runtime_activation_v1"
AUTHORITY_OWNER = OWNER
STATE_VERSION = "v1"
SINGLE_WRITER_IDENTITY = "cap72_stateful_no_order_activation_writer_v1"

PREDECESSOR_CAPABILITY_ID = "CAPABILITY_7_1_SIMULATED_ENTRY_REDUCE_EXIT_ACTIONABILITY_EVIDENCE_V1"
PREDECESSOR_MERGE_SHA = "1d447fcecc4886a690cd9e83da11c2c38995e43f"

CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = True
LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
LIVE_ORDERS = False
TESTNET_ORDERS = False
PAPER_EXCHANGE_ORDERS = False
EXCHANGE_CREDENTIAL_USE = False
REAL_CAPITAL_MOVEMENT = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False
DASHBOARD_AUTHORITY_EFFECT = "NONE"
DASHBOARD_ROLE = "READ_ONLY_CONSUMER"

# Canonical runtime mode — sole productive source.
RUNTIME_MODE = "INTERNAL_SIMULATED_EXECUTION_PUBLIC_MD_CAPABLE_NO_ORDER"
RUNTIME_MODE_OWNER = OWNER

# Activation status values Cap 7.2 alone may set productively.
STATEFUL_RUNTIME_READY_FOR_ACTIVATION = True
FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE_WHEN_ACTIVATED = True
SIMULATED_EXECUTION_ACTIVE_WHEN_ACTIVATED = True
PUBLIC_MD_RUNTIME_CAPABLE = True
PUBLIC_MD_NETWORK_SESSION_OBSERVED = False

PRODUCTIVE_HOST = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_HOST_ENTRY = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1."
    "decision_economics_cycle_bridge_v1.run_bridge_cycle_v1"
)
SIMULATED_EXECUTION_PORT_OWNER = (
    "ops.single_future_stateful_no_order_runtime_activation_v1.simulated_execution_port_v1"
)
SIMULATED_EXECUTION_DELEGATE = (
    "ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1."
    "apply_intended_action_via_canonical_accounting_v1"
)

CONFIG_RELATIVE_PATH = "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"

NETWORK_ALLOWLIST = "PUBLIC_MARKET_DATA_ENDPOINTS_ONLY"
HTTP_METHOD_ALLOWLIST = "GET_ONLY"
PUBLIC_MD_ALLOWED_HOSTS = (
    "www.okx.com",
    "okx.com",
)
PUBLIC_MD_ALLOWED_PATH_PREFIXES = (
    "/api/v5/public/",
    "/api/v5/market/",
)
FORBIDDEN_PRIVATE_PATH_PREFIXES = (
    "/api/v5/trade/",
    "/api/v5/account/",
    "/api/v5/users/",
)
FORBIDDEN_HTTP_METHODS = ("POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE")

ACTIVATION_STATE_FILENAME = "activation_state_v1.json"
COMMIT_MARKER_FILENAME = "activation_commit_marker_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".cap72_activation_staging_"

EVIDENCE_DIRNAME = "capability_7_2_single_future_stateful_no_order_runtime_activation_v1"
EVIDENCE_FILENAME = "single_future_stateful_no_order_runtime_activation_evidence_v1.json"
RESULT_FILENAME = "single_future_stateful_no_order_runtime_activation_result_v1.json"
GATE_FILENAME = "activation_gate_results_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
AUTHORITY_MATRIX_FILENAME = "authority_activation_matrix_v1.json"
PRECONDITION_MATRIX_FILENAME = "precondition_matrix_v1.json"
CALL_GRAPH_FILENAME = "call_graph_before_after_v1.json"
EXECUTION_PORT_PROOF_FILENAME = "execution_port_proof_v1.json"
NETWORK_PROOF_FILENAME = "network_credential_negative_proof_v1.json"
STARTUP_RESTART_PROOF_FILENAME = "startup_restart_reconciliation_proof_v1.json"
ROLLBACK_PROOF_FILENAME = "rollback_proof_v1.json"
PARITY_PROOF_FILENAME = "parity_proof_v1.json"
NO_ORDER_PROOF_FILENAME = "no_order_boundary_proof_v1.json"
CLAIM_MATRIX_FILENAME = "claim_matrix_v1.json"
TEST_MANIFEST_FILENAME = "test_manifest_v1.json"
ACTIVATION_STATUS_FILENAME = "activation_status_v1.json"

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

CALL_GRAPH_AFTER = (
    "repository_config_integrity_check",
    "no_order_mode_validation",
    "activation_state_validation",
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "canonical_decision_runtime_config_bind",
    "stateful_decision_runtime",
    "canonical_intent",
    "simulated_execution_port",
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

REQUIRED_PRECONDITIONS = (
    "C1_PRODUCTIVELY_BOUND",
    "C2_PRODUCTIVELY_BOUND",
    "C3_PRODUCTIVELY_BOUND",
    "CONFIRMATION_STATE_PERSISTED",
    "CONFIRMATION_SESSION_ID_STABLE",
    "DYNAMIC_SCOPE_STATE_PERSISTED",
    "DECISION_PATH_RESTART_PROVEN",
    "EXIT_POLICY_PRODUCERS_BOUND",
    "ENTRY_END_TO_END_EVIDENCE_PROVEN",
    "EXIT_END_TO_END_EVIDENCE_PROVEN",
    "NONZERO_FEE_EVIDENCE_PROVEN",
    "NONZERO_SLIPPAGE_EVIDENCE_PROVEN",
    "RECONCILIATION_BEFORE_ALPHA",
    "CONFIG_TRUTH_ALIGNED",
    "EVIDENCE_VERIFIER_PASS",
    "LEGACY_PARALLEL_AUTHORITY_ABSENT",
    "REAL_EXECUTION_ADAPTER_CONSTRUCTED",
    "EXCHANGE_ORDER_SUBMIT_REACHABLE",
    "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE",
    "PUBLIC_MD_PRIVATE_ENDPOINT_REACHABLE",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
)

# Negative preconditions must remain false.
NEGATIVE_PRECONDITIONS = (
    "REAL_EXECUTION_ADAPTER_CONSTRUCTED",
    "EXCHANGE_ORDER_SUBMIT_REACHABLE",
    "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE",
    "PUBLIC_MD_PRIVATE_ENDPOINT_REACHABLE",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
)

LEGACY_ACTIVATION_FLAG_OWNERS = (
    "ops.single_future_canonical_runtime_pre_activation_closure_v1.constants_v1.RUNTIME_ACTIVATED",
    "ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1.constants_v1.RUNTIME_ACTIVATED",
    "ops.simulated_entry_reduce_exit_actionability_evidence_v1.constants_v1.RUNTIME_ACTIVATED",
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1.RUNTIME_BRIDGE_LIVE_ACTIVATED",
    "ops.shadow_preparation_readiness_gate_v0.runtime_activation_authorized",
)


def repo_root_v1() -> Path:
    return Path(__file__).resolve().parents[3]
