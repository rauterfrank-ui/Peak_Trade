"""Constants for CAPABILITY_4_1_SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_4_1_SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1"
SCHEMA_VERSION = "single_future_canonical_runtime_pre_activation_closure.v1"
PRODUCER_VERSION = "single_future_canonical_runtime_pre_activation_closure.v1"
PACKAGE_MARKER = "SINGLE_FUTURE_CANONICAL_RUNTIME_PRE_ACTIVATION_CLOSURE_V1=true"
OWNER = "ops.single_future_canonical_runtime_pre_activation_closure_v1"
AUTHORITY_OWNER = OWNER
PRODUCER_FAMILY = OWNER

# Status semantics: readiness only — never activation.
CANONICAL_RUNTIME_ENTRYPOINT_STATUS = "READY_FOR_ACTIVATION"
CANONICAL_RUNTIME_ENTRYPOINT_STATUS_BEFORE = "BOUND_NOT_ACTIVATED"
RUNTIME_ACTIVATED = False
ACTIVATED = False
ACTIVATED_NO_LIVE_ORDERS = False
LIVE = False
LIVE_TRADING = False
TESTNET_TRADING = False
NETWORK_SESSION_STARTED = False

CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = False
LIVE_PATH_CHANGED = False
RUNTIME_ACTIVATION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_AUTHORIZED = False
PAPER_EXECUTION_AUTHORIZED = False
TESTNET_AUTHORIZED = False
NETWORK_TRADING_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMPTION_ALLOWED = False
AUTHORIZATION_CONSUMED = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MAX_POSITIONS_EFFECTIVE = 1
SELECTED_FUTURE_COUNT = 1
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False
VOL_MAX_AGE_ENFORCEMENT_DISABLED = True
DASHBOARD_AUTHORITY_EFFECT = False
DASHBOARD_ROLE = "READ_ONLY_CONSUMER"
DASHBOARD_CONSUMER_ONLY = True
ALLOWLIST_SELECTION_AUTHORITY = False
DIRECT_INSTRUMENT_OVERRIDE_ALLOWED = False
ECONOMIC_VALIDITY_OFFLINE_GATE_STATE = False
ECONOMIC_VALIDITY_OFFLINE_GATE_STATE_EXPLICIT = True

# Reuse existing productive host — do not create a second canonical runtime host.
PRODUCTIVE_RUNTIME_HOST = "scripts/ops/run_single_selected_future_runtime_binding_v1.py"
PRODUCTIVE_RUNTIME_ENTRYPOINT = (
    "scripts/ops/run_single_future_canonical_runtime_pre_activation_closure_v1.py"
)
PRODUCTIVE_BRIDGE_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
)
SELECTION_AUTHORITY_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
SELECTION_RUNTIME_BINDING_OWNER = "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"
RECONCILIATION_OWNER = "CAPABILITY_1_1_PRODUCTIVE_RECONCILIATION_RUNTIME_BINDING_V1"
UNIVERSE_OWNER = "CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1"
RANKING_OWNER = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
ACCOUNTING_OWNER = "CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1"
DECISION_AUTHORITY_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)
TYPED_VOLATILITY_PRESENCE_OWNER = (
    "trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1"
)
DOUBLE_PLAY_PARITY_OWNER = (
    "trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0"
)
CONFIG_TRUTH_OWNER = "ops.config_truth_alignment_contract_v1"

EVIDENCE_FILENAME = "single_future_canonical_runtime_pre_activation_evidence_v1.json"
RESULT_FILENAME = "single_future_canonical_runtime_pre_activation_result_v1.json"
GATE_FILENAME = "pre_activation_gate_results_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
SESSION_LOCK_FILENAME = "pre_activation_session.lock"
STAGING_DIRNAME_PREFIX = ".cap41_pre_activation_staging_"
ANALYTICAL_SESSION_LOCK_IDENTITY = "cap41_pre_activation_analytical_session_lock_v1"

REQUIRED_PREDECESSOR_CAPABILITIES = (
    "CAPABILITY_1_1_PRODUCTIVE_RECONCILIATION_RUNTIME_BINDING_V1",
    "CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1",
    "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1",
    "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1",
    "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1",
    "CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1",
)

CALL_GRAPH_BEFORE = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "okx_public_market_data",
    "feature_pipeline",
    "regime_pipeline",
    "master_v2_double_play_integrated_offline_replay",
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
    "authorization_contract_validation",
    "session_lock",
    "governed_futures_universe",
    "productive_futures_ranking",
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
    "single_selected_future_runtime_binding",
    "productive_reconciliation_startup_gate",
    "okx_public_market_data",
    "feature_pipeline",
    "regime_pipeline",
    "typed_volatility_presence",
    "master_v2_double_play_integrated_offline_replay",
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
    "analytical_simulated_execution",
    "simulated_fill_fee_slippage",
    "canonical_futures_accounting",
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    "risk_state_from_accounting",
    "portfolio_risk_state_persistence",
    "simulated_economics_no_order_path",
    "evidence",
    "full_economic_reconstruction_verifier",
)

REQUIRED_GATE_FLAGS = (
    "RUNTIME_TRUTH_MAP_CURRENT",
    "CONFIG_TRUTH_ALIGNED",
    "RECONCILIATION_BOUND",
    "RECONCILIATION_RESTART_PROVEN",
    "UNIVERSE_AUTHORITY_BOUND",
    "RANKING_AUTHORITY_BOUND",
    "SINGLE_SELECTION_PERSISTED",
    "SINGLE_SELECTION_INTEGRITY_VALID",
    "SINGLE_SELECTION_RESTART_PROVEN",
    "FUTURES_ACCOUNTING_BOUND",
    "FUTURES_ACCOUNTING_RESTART_PROVEN",
    "MASTER_V2_RUNTIME_REACHABLE",
    "DOUBLE_PLAY_RUNTIME_REACHABLE",
    "DOUBLE_PLAY_PARITY_PROVEN",
    "RISK_BOUND",
    "SAFETY_BOUND",
    "EXIT_PATH_PROVEN",
    "PORTFOLIO_STATE_PERSISTENCE_PROVEN",
    "EVIDENCE_VERIFIED",
    "PRODUCTIVE_ENTRYPOINT_CALL_GRAPH_PROVEN",
    "CONFIG_EFFECTIVE_VALUES_PROVEN",
    "LEGACY_PARALLEL_AUTHORITY_ABSENT",
    "DASHBOARD_CONSUMER_ONLY",
    "MULTI_FUTURE_DISABLED",
    "MAX_POSITIONS_EFFECTIVE_IS_1",
    "VOL_MAX_AGE_ENFORCEMENT_DISABLED",
    "NO_LIVE_ORDER_PATH",
    "NO_TESTNET_ORDER_PATH",
    "ECONOMIC_VALIDITY_OFFLINE_GATE_STATE_EXPLICIT",
    "NATIVE_INSTRUMENT_BOUND",
    "TYPED_VOLATILITY_PRESENCE_REACHABLE",
    "EXIT_RISK_SAFETY_INDEPENDENCE_PROVEN",
    "RECONCILIATION_BEFORE_ALPHA",
    "RUNTIME_NOT_ACTIVATED",
    "AUTHORIZATION_NOT_CONSUMED",
    "NETWORK_SESSION_NOT_STARTED",
)

FORBIDDEN_STATUS_VALUES = frozenset(
    {
        "ACTIVATED",
        "ACTIVATED_NO_LIVE_ORDERS",
        "LIVE",
        "ACTIVE",
    }
)
