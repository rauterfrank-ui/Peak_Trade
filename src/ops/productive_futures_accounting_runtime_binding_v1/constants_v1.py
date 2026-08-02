"""Constants for CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1."""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1"
SCHEMA_VERSION = "productive_futures_accounting_runtime_binding.v1"
PRODUCER_VERSION = "productive_futures_accounting_runtime_binding.v1"
PACKAGE_MARKER = "PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1=true"
OWNER = "ops.productive_futures_accounting_runtime_binding_v1"
AUTHORITY_OWNER = OWNER
PRODUCER_FAMILY = OWNER

CANONICAL_KERNEL_OWNER = "src.execution.paper.futures_accounting"
CANONICAL_KERNEL_PATH = "src/execution/paper/futures_accounting.py"
SINGLE_WRITER_IDENTITY = "productive_futures_accounting_portfolio_writer_v1"

FUTURES_ACCOUNTING_RUNTIME_BOUND = True
PRODUCTIVE_CALLER_ADDED = True
CORE_LOGIC_CHANGE = False
ACTIVATION_STATE = "BOUND_NOT_ACTIVATED"
RUNTIME_ACTIVATION_ALLOWED = False
LIVE_AUTHORIZED = False
ORDERS_AUTHORIZED = False
PAPER_EXECUTION_AUTHORIZED = False
TESTNET_AUTHORIZED = False
NETWORK_TRADING_SESSION_ALLOWED = False
AUTHORIZATION_CONSUMED = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
POSITION_FLIP_ALLOWED = False
DASHBOARD_AUTHORITY_EFFECT = False
ALLOWLIST_SELECTION_AUTHORITY = False
DIRECT_INSTRUMENT_OVERRIDE_ALLOWED = False
VOLATILITY_NUMERIC_MAX_AGE_ENFORCING = False

PRODUCTIVE_RUNTIME_ENTRYPOINT = "scripts/ops/run_single_selected_future_runtime_binding_v1.py"
PRODUCTIVE_BRIDGE_OWNER = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
)
SELECTION_AUTHORITY_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
SELECTION_RUNTIME_BINDING_OWNER = "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"
RECONCILIATION_OWNER = "CAPABILITY_1_1_PRODUCTIVE_RECONCILIATION_RUNTIME_BINDING_V1"

EVIDENCE_FILENAME = "productive_futures_accounting_evidence_v1.json"
ACCOUNTING_STATE_FILENAME = "productive_futures_accounting_state_v1.json"
PORTFOLIO_STATE_FILENAME = "productive_portfolio_state_from_accounting_v1.json"
RISK_STATE_FILENAME = "productive_risk_state_from_accounting_v1.json"
FILL_LEDGER_FILENAME = "productive_fill_ledger_v1.jsonl"
RESULT_FILENAME = "productive_futures_accounting_runtime_binding_result_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
WRITER_LOCK_FILENAME = "productive_futures_accounting_writer.lock"
STAGING_DIRNAME_PREFIX = ".productive_futures_accounting_staging_"

CALL_GRAPH_STEP = "canonical_futures_accounting"
CALL_GRAPH_FILL_STEP = "simulated_fill_fee_slippage"
CALL_GRAPH_PORTFOLIO_STEP = "session_persistent_portfolio"
CALL_GRAPH_RISK_STEP = "risk_state_from_accounting"

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
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
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

DEFAULT_FEE_RATE_BPS = "2.0"
DEFAULT_SLIPPAGE_BPS = "1.0"
DEFAULT_INITIAL_EQUITY = "100000"
DEFAULT_INITIAL_MARGIN_RATE = "0.10"
DEFAULT_MAINTENANCE_MARGIN_RATE = "0.05"
DEFAULT_MAX_LEVERAGE = "10"
DEFAULT_CONTRACT_SIZE = "1"
DEFAULT_TICK_SIZE = "0.01"
DEFAULT_MIN_QTY = "0.0001"
DEFAULT_QUOTE_CURRENCY = "USDT"

ROUNDING_MODE_NAME = "ROUND_HALF_EVEN"
