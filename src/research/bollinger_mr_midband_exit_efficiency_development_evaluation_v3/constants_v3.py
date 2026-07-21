"""Frozen constants for Bollinger/MR midband exit-efficiency DEVELOPMENT evaluation v3.

Identical fees/params/hashes/seeds to v1/v2. Only scope/run/hypothesis/path identity
is versioned. V3 is a new independently preregistered measurement; not a V1 or V2 rerun.
"""

from __future__ import annotations

SCOPE_ID = "bollinger_mr_midband_exit_efficiency_development_evaluation_v3"
EVALUATION_RUN_ID = "evaluate_bollinger_mr_midband_exit_efficiency_development_v3"
HYPOTHESIS_ID = "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
DATASET_CLASS = "DEVELOPMENT_ONLY"
BASELINE_CONFIG_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
STRATEGY_ID = "bollinger_bands"
STRATEGY_VERSION = "v2"
PORTFOLIO_AGGREGATION_ID = "RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1"

FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
HALF_SPREAD_BPS = 5.0
STOP_PCT = 0.025
COST_MULTIPLIER = 1.0
PRIMARY_SEED = 20220601

DECISION_START = "2023-05-20T00:00:00Z"
DECISION_END_EXCLUSIVE = "2023-08-16T05:55:00Z"
DEVELOPMENT_SPLIT_DIGEST = "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
EXPECTED_MANIFEST_SHA256 = "be953c559ac3dd797961bdda8cbc190076353c91d3299b9031ae1ee767d4b594"
EXPECTED_CONTENT_HASH = "4a1978fe0e69a6cd7b19b32f5f95882cfdc3e36397aaec87bce2c4139ab1cfca"
MAX_FEATURE_LOOKBACK_HOURS = 20

BB_PERIOD = 20
BB_STD = 2.0
EXIT_LEVEL = "middle_band"
EXIT_THRESHOLD_BINDING_VALUE = 0.5

MINIMUM_TRADE_COUNT = 20
MAX_TRADE_COUNT_REDUCTION_FRACTION = 0.5
INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX = 0.35

SLEEVE_INITIAL_CASH = 10_000.0
SHARED_INITIAL_CAPITAL = 10_000.0

CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v3.json"
)
EVIDENCE_REL_PATH = "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v3/"
GOVERNANCE_REL_PATH = (
    "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V3.md"
)
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"

REQUIRED_FROZEN_EXIT_PARAMETERS = {
    "bb_period": BB_PERIOD,
    "bb_std": BB_STD,
    "exit_level": EXIT_LEVEL,
    "exit_threshold_binding_value": EXIT_THRESHOLD_BINDING_VALUE,
    "long_exit_rule": "close_crosses_middle_from_below_to_at_or_above",
    "short_exit_rule": "close_crosses_middle_from_above_to_at_or_below",
    "stop_loss_remains_active_if_hit_first": True,
}
