"""Frozen constants for CS short-horizon return reversal v1 DEVELOPMENT evaluation.

Infrastructure-only. Does not authorize or execute evaluation. Measurement-contract
thresholds and strategy score/selection semantics remain unchanged.
"""

from __future__ import annotations

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1=true"
)

SCOPE_ID = (
    "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1"
)
PACKAGE_SCOPE_ID = "cross_sectional_short_horizon_return_reversal_v1_development_evaluation_v1"
OWNER_SURFACE = (
    "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1"
)
EVALUATION_RUN_ID = "evaluate_cross_sectional_short_horizon_return_reversal_development_v1"
STRATEGY_ID = "cross_sectional_short_horizon_return_reversal"
STRATEGY_IDENTITY = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1"
STRATEGY_VERSION = "v1"
SIGNAL_FAMILY = "CROSS_SECTIONAL_RETURN_REVERSAL"
HYPOTHESIS_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1"
PROGRAM_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"

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

MINIMUM_REBALANCE_OBSERVATIONS = 30
MINIMUM_PASSING_SEGMENTS = 2
TIME_SEGMENT_ROBUSTNESS_PASS_RATIO = 0.5

DEVELOPMENT_RUN_LIMIT = 1
RETRY_FORBIDDEN = True

FROZEN_MEASUREMENT_CONTRACT_DIGEST = (
    "3ee997a95d2d9ea4de9597b39a816ddbdc9e06d587941334b8d04507e9945b2a"
)
SCORE_FORMULA_VERSION = "negated_raw_trailing_log_return_fixed_lookback_v1"
DEFAULT_LOOKBACK_N = 24
DEFAULT_REBALANCE_INTERVAL_BARS = 4
DEFAULT_SIGNAL_LAG_BARS = 1
DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK = 5
PREREGISTRATION_ORIGINAL_DIGEST = "3d983bbfa1db6c319f6c4399549679a5b7fd2d635d8e72d4452330da9059729a"

FEE_BPS_PER_SIDE = 10.0
SLIPPAGE_BPS_PER_SIDE = 5.0
HALF_SPREAD_BPS = 5.0
EFFECTIVE_ENTRY_COST_BPS = 20.0
EFFECTIVE_EXIT_COST_BPS = 20.0
ROUNDTRIP_COST_BPS = 40.0

MEASUREMENT_CONTRACT_REL_PATH = (
    "config/research/"
    "cross_sectional_short_horizon_return_reversal_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
IMPLEMENTATION_BINDING_REL_PATH = (
    "config/research/"
    "cross_sectional_short_horizon_return_reversal_v1_strategy_implementation_binding_v1.json"
)
ENTRY_POINT_BINDING_REL_PATH = (
    "config/research/"
    "cross_sectional_short_horizon_return_reversal_v1_development_evaluation_"
    "entry_point_binding_v1.json"
)
LIFECYCLE_AUTHORITY_REL_PATH = (
    "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
)
PROGRAM_REL_PATH = (
    "config/research/cross_sectional_short_horizon_return_reversal_research_program_v1.json"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/evaluate_cross_sectional_short_horizon_return_reversal_development_v1/"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_DEVELOPMENT_EVALUATION_ENTRY_POINT_V1.md"
)
CLI_REL_PATH = (
    "scripts/research/run_evaluate_cross_sectional_short_horizon_return_reversal_development_v1.py"
)
SCORE_REL_PATH = "src/research/cross_sectional_short_horizon_return_reversal_v1_score_v1.py"
SELECTION_REL_PATH = "src/research/cross_sectional_short_horizon_return_reversal_v1_selection_v1.py"

CANONICAL_BACKTEST_WIRING_OWNER = "src.research.cross_sectional_single_slot_backtest_wiring_v0"
CANONICAL_STATS_OWNER = "src.backtest.stats"
CANONICAL_ECONOMIC_VALIDITY_OWNER = "src.backtest.economic_validity_policy_v1"

AUTHORIZATION_FLAG = "--authorize-single-development-evaluation"
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"

REQUIRED_EVIDENCE_METRIC_KEYS = (
    "gross_return",
    "net_return",
    "gross_profit_factor",
    "net_profit_factor",
    "sharpe",
    "max_drawdown",
    "turnover",
    "fees",
    "slippage",
    "total_cost_drag",
    "trade_count",
    "valid_rebalance_observations",
    "segment_boundaries",
    "segment_results",
    "passing_segments",
    "time_segment_robustness_pass_ratio",
    "config_digest",
    "strategy_params_digest",
    "dataset_id",
    "dataset_digest",
)
