"""Constants for CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"
SCHEMA_VERSION = "single_selected_future_runtime_binding.v1"
PRODUCER_VERSION = "single_selected_future_runtime_binding.v1"
PACKAGE_MARKER = "SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1=true"
OWNER = "ops.single_selected_future_runtime_binding_v1"
AUTHORITY_OWNER = OWNER
SELECTION_CONSUMER_IDENTITY = "single_selected_future_runtime_binding_consumer_v1"

# Cap 2.3 is the sole selection authority owner; Cap 2.4 is the sole runtime consumer.
SELECTION_AUTHORITY_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
SELECTION_SINGLE_WRITER = True
SELECTED_FUTURE_COUNT = 1
MAX_POSITIONS_EFFECTIVE = 1
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
SINGLE_SELECTED_FUTURE = True

DASHBOARD_AUTHORITY_EFFECT = False
DASHBOARD_ROLE = "READ_ONLY_CONSUMER"
ALLOWLIST_SELECTION_AUTHORITY = False
DIRECT_INSTRUMENT_OVERRIDE_ALLOWED = False
CORE_LOGIC_CHANGE = False
ACTIVATION_CHANGED = False
LIVE_PATH_CHANGED = False
RUNTIME_ACTIVATION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_AUTHORIZED = False
PAPER_EXECUTION_AUTHORIZED = False
TESTNET_AUTHORIZED = False
NETWORK_TRADING_SESSION_ALLOWED = False
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False
AUTHORIZATION_CONSUMED = False

PRODUCTIVE_RUNTIME_ENTRYPOINT = "scripts/ops/run_single_selected_future_runtime_binding_v1.py"
PRODUCTIVE_BRIDGE_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
)

EVIDENCE_FILENAME = "single_selected_future_runtime_binding_evidence_v1.json"
BINDING_RESULT_FILENAME = "single_selected_future_runtime_binding_result_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
CONSUMER_LOCK_FILENAME = "single_selected_future_runtime_binding_consumer.lock"
STAGING_DIRNAME_PREFIX = ".single_selected_future_runtime_binding_staging_"

STATE_SELECTED_ACTIVE = "SELECTED_ACTIVE"
STATE_SELECTED_DEGRADED = "SELECTED_DEGRADED"
STATE_SELECTED_EXIT_ONLY = "SELECTED_EXIT_ONLY"
STATE_REPLACEMENT_PENDING = "REPLACEMENT_PENDING"
STATE_NO_SELECTION = "NO_SELECTION"

ALPHA_ALLOWED_STATES = frozenset({STATE_SELECTED_ACTIVE})
EXIT_RISK_SAFETY_PRESERVED_STATES = frozenset(
    {
        STATE_SELECTED_DEGRADED,
        STATE_SELECTED_EXIT_ONLY,
        STATE_REPLACEMENT_PENDING,
    }
)

CALL_GRAPH = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
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
)

CALL_GRAPH_BEFORE = (
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
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    "evidence",
    "full_economic_reconstruction_verifier",
)

CALL_GRAPH_BINDING_PREFIX = (
    "persisted_single_selected_future",
    "selection_integrity_freshness_validation",
    "ranking_snapshot_reference_validation",
    "governed_universe_instrument_validation",
    "venue_native_instrument_binding",
)

CALL_GRAPH_STEP = "single_selected_future_runtime_binding"

LIVE_TRADING_STATUS = "live"
SUSPENDED_TRADING_STATUSES = frozenset(
    {"suspend", "suspended", "expired", "settle", "settled", "delisted", "invalid"}
)
