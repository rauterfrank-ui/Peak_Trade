"""Constants for Stage-2 Shadow Campaign Input Authority v1 (Surface B).

SHADOW_ONLY=true
PRODUCTIVE_ACTIVATION=false
INPUT_AUTHORITY=false
RUNTIME_IMPLEMENTED=false
O4_UNCHANGED=true
DASHBOARD_AUTHORITY_EFFECT=NONE
ORDERS=false
TESTNET=false
LIVE=false
"""

from __future__ import annotations

CAPABILITY_ID = "CAPABILITY_PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_V1"
PACKAGE_MARKER = "PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_V1=true"
OWNER = "ops.productive_pure_stack_stage2_shadow_campaign_input_authority_v1"
PRODUCER_VERSION = "productive_pure_stack_stage2_shadow_campaign_input_authority/v1"
SOURCE_ID = "sta_pt1m_finalized_ohlcv_shadow_calibration_producer_v1"

SOLE_TRADING_AUTHORITY = "run_integrated_offline_trading_logic_replay_v1"
AUTHORITY_SURFACE = "B"
PRODUCER_CLASS = "sole_trading_authority_shadow_calibration_producer"
BAR_INTERVAL = "PT1M"
PT1M_SECONDS = 60
OBSERVATION_FAMILY = "PUBLIC_MARKET_FINALIZED_BARS"

OHLCV_SOURCE = "VENUE_NATIVE_FINALIZED_CANDLES"
MARK_PRICE_POLICY = "REQUIRED_SEPARATE_FIELD"
CANDLE_MARK_TRADE_EQUIVALENCE = "FORBIDDEN"

DASHBOARD_ROLE = "READ_ONLY_CONSUMER"
DASHBOARD_AUTHORITY_EFFECT = "NONE"
O4_UNCHANGED = True

PRODUCTIVE_ACTIVATION = False
INPUT_AUTHORITY = False
RUNTIME_IMPLEMENTED = False
OWNER_RATIFIED_INPUT_AUTHORITY = False
PRODUCTIVE_NUMERIC_VALUES_SET = 0
PRODUCTIVE_CALIBRATION_AUTHORIZED = False
RESULTV1_MAPPING_AUTHORIZED = False
CORE_LOGIC_CHANGE = False

LIVE_ORDERS = False
TESTNET_ORDERS = False
PAPER_EXCHANGE_ORDERS = False
EXCHANGE_CREDENTIAL_USE = False
REAL_CAPITAL_MOVEMENT = False

ARITHMETIC_KERNEL_PATH = "src/execution/paper/futures_accounting.py"
SEQUENCE_SURVIVAL_METRICS_SHAPE = "trading.master_v2.double_play_survival.SequenceSurvivalMetrics"
SEQUENCE_SURVIVAL_METRICS_PRODUCER = "SequenceSurvivalMetricsProducerV1_FUTURE_BOUNDED_UNDER_STA"

OWNER_RATIFICATION_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_OWNER_RATIFICATION_V1.md"
)
IMPLEMENTATION_PLAN_REL = "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_IMPLEMENTATION_PLAN_V1.md"
DECISIONS_MANIFEST_REL = (
    "docs/ops/PRODUCTIVE_PURE_STACK_STAGE2_SHADOW_CAMPAIGN_INPUT_AUTHORITY_DECISIONS_V1.json"
)

CORRECTION_REVISION_POLICY = (
    "LATE_EVENTS_REQUIRE_EXPLICIT_CORRECTED_REVISION_OR_REJECT_INVALIDATE_SEGMENT;"
    "SILENT_REWRITES_FORBIDDEN;SNAPSHOTS_IMMUTABLE;"
    "REBUILD_REQUIRES_NEW_DATASET_ID_AND_DIGEST"
)

STRESS_STRUCTURAL_FAMILIES: tuple[str, ...] = (
    "gaps_missing_bars",
    "staleness",
    "spread_expansion_crossed_book",
    "volatility_shocks",
    "liquidation_near_miss_paths",
    "chop_switch_clusters",
    "fees",
    "slippage",
    "latency",
    "sequence_path_disruption",
)

PARTITION_SEGMENTS: tuple[str, ...] = (
    "train",
    "calibration",
    "validation",
    "holdout",
)

REGIME_COVERAGE_LABELS: tuple[str, ...] = (
    "low",
    "mid",
    "high",
    "unknown",
    "missing",
)

FORBIDDEN_AUTHORITY_SOURCES: tuple[str, ...] = (
    "dashboard_readmodel",
    "webui",
    "fixture",
    "scenario_scalar",
    "cmc_volatility",
    "research_panel",
    "ResultV1",
    "SurvivalResultV1",
    "SuitabilityResultV1",
    "o4_pt1h_as_pt1m_authority",
    "parallel_arithmetic_kernel",
    "parallel_survival_kernel",
)

REQUIRED_INSTRUMENT_FIELDS: tuple[str, ...] = (
    "venue",
    "canonical_instrument_id",
    "venue_instrument_id",
    "contract_type",
    "market_type",
    "quote_currency",
    "settlement_currency",
)
