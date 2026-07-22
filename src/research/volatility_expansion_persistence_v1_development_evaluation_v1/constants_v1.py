"""Frozen constants for VEP v1 DEVELOPMENT evaluation entry point.

Development evaluation is authorized on the three authority surfaces; execution still
requires a separate operator GO. Measurement-contract thresholds and strategy/baseline
semantics remain unchanged.
"""

from __future__ import annotations

PACKAGE_MARKER = "VOLATILITY_EXPANSION_PERSISTENCE_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1=true"

SCOPE_ID = "volatility_expansion_persistence_v1_development_evaluation_v1"
OWNER_SURFACE = "VOLATILITY_EXPANSION_PERSISTENCE_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1"
EVALUATION_RUN_ID = "evaluate_volatility_expansion_persistence_development_v1"
STRATEGY_ID = "volatility_expansion_persistence"
STRATEGY_IDENTITY = "VOLATILITY_EXPANSION_PERSISTENCE_V1"
STRATEGY_VERSION = "v1"
SIGNAL_FAMILY = "VOLATILITY_REGIME"
HYPOTHESIS_ID = "VOLATILITY_EXPANSION_PERSISTENCE_NON_BITCOIN_PERPETUALS_V1"
PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
BASELINE_ID = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"

DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
DATASET_CLASS = "DEVELOPMENT_ONLY"
ALLOWED_DATASET_IDS = frozenset({DATASET_ID})
FORBIDDEN_HOLDOUT_IDS = frozenset(
    {
        "offline_economic_reevaluation_sealed_long_panel_v1",
        "any_sealed_holdout_raw_or_derived_artifacts",
    }
)

TIME_SEGMENT_DEFINITION_ID = "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
TIME_SEGMENT_COUNT = 4
TIME_SEGMENT_IDS = (
    "TIME_SEGMENT_Q1",
    "TIME_SEGMENT_Q2",
    "TIME_SEGMENT_Q3",
    "TIME_SEGMENT_Q4",
)
BAR_FREQUENCY = "PT1H"
# Bound from measurement-contract time_segment_definition.development_period.
DEVELOPMENT_START = "2022-06-01T03:55:17Z"
DEVELOPMENT_END_EXCLUSIVE = "2023-08-16T05:55:00Z"

DEVELOPMENT_RUN_LIMIT = 1
RETRY_FORBIDDEN = True

# Preregistered measurement-contract thresholds (economic_admission_contract).
MIN_EVALUABLE_TREATMENT_BREAKOUT_EVENTS = 50
MIN_EVALUABLE_TREATMENT_EVENTS_PER_TIME_SEGMENT = 10
MIN_EXECUTED_TREATMENT_TRADES = 30
TIME_SEGMENT_ROBUSTNESS_PASS_RATIO = 0.5
MINIMUM_PASSING_SEGMENTS = 2
GROSS_PROFIT_FACTOR_MIN = 1.0
NET_PROFIT_FACTOR_MIN = 1.3
COST_STRESS_1_5X_NET_PROFIT_FACTOR_MIN = 1.0
MAXIMUM_MAX_DRAWDOWN = 0.25
MINIMUM_NET_EXPECTANCY = 0.0

FROZEN_MEASUREMENT_CONTRACT_DIGEST = (
    "92e2117ce7e60fe771c4d6e1d6d1aeb8645af80512e21cb9ff21fc4477c7c70e"
)

FEE_BPS_PER_SIDE = 10.0
SLIPPAGE_BPS_PER_SIDE = 5.0
HALF_SPREAD_BPS = 5.0

MEASUREMENT_CONTRACT_REL_PATH = (
    "config/research/"
    "volatility_expansion_persistence_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
IMPLEMENTATION_BINDING_REL_PATH = (
    "config/research/volatility_expansion_persistence_v1_strategy_implementation_binding_v1.json"
)
ENTRY_POINT_BINDING_REL_PATH = (
    "config/research/"
    "volatility_expansion_persistence_v1_development_evaluation_entry_point_binding_v1.json"
)
LIFECYCLE_AUTHORITY_REL_PATH = "config/research/volatility_regime_hypothesis_backlog_v1.json"
PROGRAM_REL_PATH = "config/research/volatility_regime_research_program_v1.json"
EVIDENCE_REL_PATH = "docs/evidence/evaluate_volatility_expansion_persistence_development_v1/"
GOVERNANCE_REL_PATH = (
    "docs/governance/VOLATILITY_EXPANSION_PERSISTENCE_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1.md"
)
CLI_REL_PATH = "scripts/research/run_evaluate_volatility_expansion_persistence_development_v1.py"

SHARED_CHANNEL_CORE_REL_PATH = "src/research/price_channel_breakout_core_v1.py"
STRATEGY_IMPL_REL_PATH = "src/research/volatility_expansion_persistence_v1_strategy_v1.py"
BASELINE_IMPL_REL_PATH = "src/research/unconditional_20_bar_price_channel_breakout_v1.py"
VOL_STATE_REL_PATH = "src/research/volatility_expansion_persistence_v1_vol_state_v1.py"
PRODUCTIVE_PNL_EVALUATOR_REL_PATH = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)

SHARED_CHANNEL_CORE_OWNER = "research.price_channel_breakout_core_v1"
AUTHORIZATION_FLAG = "--authorize-single-development-evaluation"
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"

REQUIRED_EVIDENCE_METRIC_KEYS = (
    "gross_return",
    "net_return",
    "gross_profit_factor",
    "net_profit_factor",
    "max_drawdown",
    "trade_count",
    "evaluable_treatment_breakout_events",
    "segment_boundaries",
    "segment_results",
    "passing_segments",
    "time_segment_robustness_pass_ratio",
    "config_digest",
    "strategy_params_digest",
    "dataset_id",
    "dataset_digest",
)
