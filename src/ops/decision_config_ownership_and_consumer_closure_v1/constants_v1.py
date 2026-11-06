"""Constants for CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1."""

from __future__ import annotations

from pathlib import Path

CAPABILITY_ID = "CAPABILITY_6_3_DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1"
SCHEMA_VERSION = "decision_config_ownership_and_consumer_closure.v1"
PRODUCER_VERSION = "decision_config_ownership_and_consumer_closure.v1"
PACKAGE_MARKER = "DECISION_CONFIG_OWNERSHIP_AND_CONSUMER_CLOSURE_V1=true"
OWNER = "ops.decision_config_ownership_and_consumer_closure_v1"
AUTHORITY_OWNER = OWNER
CONFIG_VERSION = "v1"
CONFIG_SCHEMA_VERSION = "canonical_decision_runtime_config.v1"
STATE_VERSION = "v1"

CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = False
RUNTIME_ACTIVATED = False
LIVE_PATH_CHANGED = False
TESTNET_PATH_CHANGED = False
ORDER_PATH_CHANGED = False
EXCHANGE_CREDENTIAL_PATH_CHANGED = False
NETWORK_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
NO_SILENT_FALLBACK = True
ONE_CONFIG_OWNER_PER_RUNTIME_VALUE = True
NO_PARALLEL_CONFIG_AUTHORITY = True

# Frozen productive effective values (must remain unchanged through ownership migration).
EXPECTED_CONFIRMATION_EPOCHS = 2
EXPECTED_UP_DISTANCE = 200.0
EXPECTED_ADVERSE_EXIT_DISTANCE = 80.0
EXPECTED_REVERSAL_DISTANCE = 120.0

# Review-only values (not migrated unless productive ownership gap proven).
REVIEW_PRICE_PATH_MAX_LEN = 64
REVIEW_FEE_RATE_BPS = 2.0
REVIEW_SLIPPAGE_BPS = 1.0

PRODUCTIVE_HOST = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
    "decision_economics_cycle_bridge_v1.py"
)
PRODUCTIVE_DECISION_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
PREDECESSOR_CAPABILITY = "CAPABILITY_6_2_DYNAMIC_SCOPE_PERSISTENCE_BINDING_V1"
PREDECESSOR_CONFIRMATION_CAPABILITY = (
    "CAPABILITY_6_1_STATEFUL_CONFIRMATION_AND_C1_PRODUCTIVE_BINDING_V1"
)

CONFIG_RELATIVE_PATH = "config/ops/canonical_decision_runtime_config_v1.toml"
CONFIG_TOML_SECTION = "canonical_decision_runtime_config_v1"

REQUIRED_CONFIG_KEYS = (
    "config_version",
    "schema_version",
    "confirmation_epochs",
    "up_distance",
    "adverse_exit_distance",
    "reversal_distance",
)

CALL_GRAPH_CONFIG_BIND_STEP = "canonical_decision_runtime_config_bind"

DEFAULT_VENUE = "OKX"
CONFIG_STATE_FILENAME = "decision_runtime_config_state_v1.json"
COMMIT_MARKER_FILENAME = "decision_runtime_config_commit_marker_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
EVIDENCE_FILENAME = "decision_config_ownership_and_consumer_closure_evidence_v1.json"
RESULT_FILENAME = "decision_config_ownership_and_consumer_closure_result_v1.json"
GATE_FILENAME = "decision_config_gate_results_v1.json"
FAILURE_INJECTION_FILENAME = "failure_injection_results.json"
AUTHORITY_MATRIX_FILENAME = "config_authority_matrix_v1.json"
STAGING_DIRNAME_PREFIX = ".cap63_decision_config_staging_"

CALL_GRAPH_BEFORE = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
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
    CALL_GRAPH_CONFIG_BIND_STEP,
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

OWNERSHIP_GRAPH_BEFORE = (
    "bridge_local_hardcode_confirmation_epochs",
    "cap62_frozen_up_distance",
    "cap62_frozen_adverse_exit_distance",
    "cap62_frozen_reversal_distance",
)

OWNERSHIP_GRAPH_AFTER = (
    "canonical_decision_runtime_config_v1_owner",
    "productive_bridge_consumer",
    "cap61_digest_consumer",
    "cap62_digest_consumer",
)

REQUIRED_GATE_FLAGS = (
    "CONFIG_RUNTIME_DRIFT_FALSE",
    "EFFECTIVE_NUMERIC_VALUES_UNCHANGED",
    "NO_SILENT_FALLBACK",
    "CONFIG_CONSUMER_TRACE_COMPLETE",
    "ONE_CONFIG_OWNER_PER_RUNTIME_VALUE",
    "NO_PARALLEL_CONFIG_AUTHORITY",
    "CONFIG_VERSION_EXPLICIT",
    "CONFIG_DIGEST_BOUND",
    "PREDECESSOR_DIGEST_BOUND",
    "SUCCESSOR_CONSUMER_IDENTIFIED",
    "CONFIG_HANDOFF_PROVEN",
    "CORE_LOGIC_UNCHANGED",
    "GOLDEN_VECTOR_PARITY_PASS",
    "CALL_ORDER_PARITY_PROVEN",
    "INPUT_OUTPUT_PARITY_PROVEN",
    "STATE_TRANSITION_PARITY_PROVEN",
    "DECISION_REASON_PARITY_PROVEN",
    "RISK_PARITY_PROVEN",
    "SAFETY_PARITY_PROVEN",
    "EXIT_PRECEDENCE_PARITY_PROVEN",
    "CONFIRMATION_STATE_COMPATIBLE",
    "DYNAMIC_SCOPE_STATE_COMPATIBLE",
    "CONFIG_DIGEST_RESTART_PROVEN",
    "CONFIG_DIGEST_MISMATCH_FAIL_CLOSED",
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


def canonical_config_path_v1(repo_root: Path | None = None) -> Path:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    return root / CONFIG_RELATIVE_PATH
