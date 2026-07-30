"""Constants for WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_HARDENING_V2."""

from __future__ import annotations

CAPABILITY_ID = (
    "WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_HARDENING_V2"
)
PACKAGE_MARKER = (
    "WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_HARDENING_V2=true"
)
SCHEMA_VERSION = "v2"
PRODUCER_FAMILY = (
    "ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
)
OWNER = PRODUCER_FAMILY

HARDENS_CAPABILITY = "WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1"

SESSION_RESTART_POLICY = "NO_IMPLICIT_RESUME"
DEFAULT_REGIME_FALLBACK_ACTIVE = False
SYNTHETIC_BID_ASK_FALLBACK_ACTIVE = False
ECONOMICS_PLACEHOLDER_WRITERS_ACTIVE = False
HARDCODED_HOLD_PRESENT = False
DEFAULT_HOLD_FALLBACK_ACTIVE = False
DEFAULT_ZERO_QUANTITY_FALLBACK_ACTIVE = False

PRICE_BASIS_CONTRACT_VERSION = "wallclock_bridge_price_basis_explicit_mid_v2"
FEATURE_PRICE_SOURCE = "explicit_mid_price"
FILL_REFERENCE_PRICE_SOURCE = "explicit_mid_price"
MARK_TO_MARKET_PRICE_SOURCE = "explicit_mid_price"
BID_ASK_POLICY = "COLLAPSED_TO_EXPLICIT_MID_DOCUMENTED"
REQUIRED_TICKER_PRICE_FIELD = "markPx"

FEATURE_CONFIG_VERSION = "bridge_feature_regime_pipeline_v2"
REGIME_CONFIG_VERSION = "bridge_regime_classifier_v2"
FEATURE_WINDOW_MIN = 3
PRICE_PATH_MAX_LEN = 64

ORDERS_AUTHORIZED = False
TESTNET_AUTHORIZED = False
LIVE_AUTHORIZED = False
PAPER_EXECUTION_AUTHORIZED = False
CREDENTIALS_AUTHORIZED = False
ECONOMIC_VALIDITY_PASS = False
PROMOTION_PASS = False
RUNTIME_BRIDGE_LIVE_ACTIVATED = False
FORCED_FIXTURE_WALLCLOCK_REACHABLE = False

EXECUTION_CLASS_ANALYTICAL = "ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION"
DECISION_AUTHORITY_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "run_integrated_offline_trading_logic_replay_v1"
)

REQUIRED_EVIDENCE_STREAMS: tuple[str, ...] = (
    "session_manifest.json",
    "market_data_sequence.jsonl",
    "feature_trace.jsonl",
    "regime_trace.jsonl",
    "decision_trace.jsonl",
    "risk_sizing_trace.jsonl",
    "order_intent_trace.jsonl",
    "simulated_fill_trace.jsonl",
    "portfolio_snapshots.jsonl",
    "equity_curve.jsonl",
    "runtime_events.jsonl",
    "killstate_events.jsonl",
    "authorization_consumption.json",
    "economic_metrics.json",
    "completion_verdict.json",
    "integrity_manifest.json",
)

CANONICAL_FILL_LEDGER_ATTR = "fill_ledger"
