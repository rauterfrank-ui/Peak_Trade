"""Frozen constants for Momentum V2 vol-scaled DEVELOPMENT evaluation entry point."""

from __future__ import annotations

PACKAGE_MARKER = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "DEVELOPMENT_EVALUATION_ENTRY_POINT_V1=true"
)

SCOPE_ID = "momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_v1"
OWNER_SURFACE = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "DEVELOPMENT_EVALUATION_ENTRY_POINT_V1"
)
EVALUATION_RUN_ID = (
    "evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1"
)
STRATEGY_ID = "momentum_v2_volatility_scaled_own_instrument_continuation"
STRATEGY_IDENTITY = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1"
STRATEGY_VERSION = "v1"
SIGNAL_FAMILY = "OWN_INSTRUMENT_VOLATILITY_SCALED_MOMENTUM"
HYPOTHESIS_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
PROGRAM_ID = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1"
BASELINE_ID = "FROZEN_RAW_RETURN_MOMENTUM_1H_ENTRY_EXIT_EVENT_V1"

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
DEVELOPMENT_START = "2022-06-01T03:55:17Z"
DEVELOPMENT_END_EXCLUSIVE = "2023-08-16T05:55:00Z"

DEVELOPMENT_RUN_LIMIT = 1
RETRY_FORBIDDEN = True

# Preregistered measurement-contract thresholds.
MIN_EXECUTED_TREATMENT_TRADES = 50
MIN_TRADES_PER_TIME_SEGMENT = 10
TIME_SEGMENT_ROBUSTNESS_PASS_RATIO = 0.5
MINIMUM_PASSING_SEGMENTS = 2
GROSS_PROFIT_FACTOR_MIN = 1.0
NET_PROFIT_FACTOR_MIN = 1.3
COST_STRESS_1_5X_NET_PROFIT_FACTOR_MIN = 1.0
MAXIMUM_MAX_DRAWDOWN = 0.25
MINIMUM_NET_EXPECTANCY = 0.0
MAX_SINGLE_INSTRUMENT_POSITIVE_GROSS_PNL_SHARE_MAX = 0.35

FROZEN_MEASUREMENT_CONTRACT_DIGEST = (
    "0820d94b306cf7b3240bccc2eee06484debdcd7ae1eb77d4a683425247a4c4ce"
)

FEE_BPS_PER_SIDE = 10.0
SLIPPAGE_BPS_PER_SIDE = 5.0
HALF_SPREAD_BPS = 5.0

MEASUREMENT_CONTRACT_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_v1_preregistered_"
    "economic_hypothesis_measurement_contract_v1.json"
)
IMPLEMENTATION_BINDING_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "strategy_implementation_binding_v1.json"
)
ENTRY_POINT_BINDING_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "development_evaluation_entry_point_binding_v1.json"
)
LIFECYCLE_AUTHORITY_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_hypothesis_backlog_v1.json"
)
PROGRAM_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_research_program_v1.json"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/"
    "evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1/"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "DEVELOPMENT_EVALUATION_ENTRY_POINT_V1.md"
)
CLI_REL_PATH = (
    "scripts/research/"
    "run_evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1.py"
)
STRATEGY_SIGNAL_REL_PATH = (
    "src/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_signal_v1.py"
)
PRODUCTIVE_PNL_EVALUATOR_REL_PATH = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)

AUTHORIZATION_FLAG = "--authorize-single-development-evaluation"
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
PORTFOLIO_AGGREGATION_ID = "RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1"

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
