"""Frozen constants for Bollinger/MR midband reentry-cooldown DEVELOPMENT evaluation v7.

Fees/params/hashes/seeds identical to V6. Wiring-only surfaces; does not mutate the
DEFINITION_ONLY preregistration contract. Digest must match HEAD preregistration.
"""

from __future__ import annotations

SCOPE_ID = "bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7"
EVALUATION_RUN_ID = "evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7"
HYPOTHESIS_ID = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7"
OWNER_SURFACE = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V7"
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

MAX_HOLDING_BARS = 48
MAX_HOLDING_HORIZON_HOURS = 48
MAX_HOLDING_FREQUENCY = "PT1H"
MAX_HOLDING_SOURCE_FIELD = "splits.max_holding_horizon_hours"
MAX_HOLDING_EXIT_RULE = "bars_since_entry_fill_gte_max_holding_bars"
COMPOSITE_TRIGGER_POLICY = "first_of_midband_cross_or_max_holding"

COOLDOWN_BARS = 24
COOLDOWN_HOURS = 24
COOLDOWN_FREQUENCY = "PT1H"
COOLDOWN_SCOPE = ("instrument_id", "direction")
COOLDOWN_ARMS_ON_TRIGGERS = ("midband", "midband_and_max_holding")
COOLDOWN_DOES_NOT_ARM_ON = ("max_holding",)

MINIMUM_TRADE_COUNT = 20
MAX_TRADE_COUNT_REDUCTION_FRACTION = 0.5
INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX = 0.35

SLEEVE_INITIAL_CASH = 10_000.0
SHARED_INITIAL_CAPITAL = 10_000.0

CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v7.json"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7/"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V7.md"
)
CLI_REL_PATH = (
    "scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7.py"
)
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
BINDING_FIX_SURFACE = "MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX"
OBSERVABILITY_SURFACE = "EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1"
LIFECYCLE_CHECKPOINT_SURFACE = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5"
)
MECHANISM_ID = (
    "canonical_bollinger_side_aware_midband_exit_with_frozen_max_holding_"
    "and_same_side_reentry_cooldown_v1"
)
BASE_MECHANISM_ID = (
    "canonical_bollinger_side_aware_middle_band_exit_with_frozen_max_holding_horizon_v1"
)
# Must match DEFINITION_ONLY preregistration on HEAD (do not mutate).
DEVELOPMENT_PREREGISTRATION_DIGEST = (
    "4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680"
)

AUTHORIZATION_FLAG = "--authorize-single-development-evaluation"
# B3 clarification: incomplete slot-consuming runs use INCONCLUSIVE_INFRASTRUCTURE_FAILURE.
RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE = "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
INFRASTRUCTURE_DIAGNOSTIC_CLASS_DEFAULT = "PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL"
LIFECYCLE_TERMINAL_INCONCLUSIVE_INFRA = (
    "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
)
OPERATOR_CLARIFICATION_AUTHORITY_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7.json"
)
OPERATOR_CLARIFICATION_AUTHORITY_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7"
)
# Legacy alias retained only for static import safety in older test drafts; do not emit.
RESULT_CLASS_INFRASTRUCTURE_UNRESOLVED_BLOCKER = RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE

REQUIRED_FROZEN_EXIT_PARAMETERS = {
    "bb_period": BB_PERIOD,
    "bb_std": BB_STD,
    "exit_level": EXIT_LEVEL,
    "exit_threshold_binding_value": EXIT_THRESHOLD_BINDING_VALUE,
    "long_exit_rule": "close_crosses_middle_from_below_to_at_or_above",
    "short_exit_rule": "close_crosses_middle_from_above_to_at_or_below",
    "stop_loss_remains_active_if_hit_first": True,
    "max_holding_horizon_hours": MAX_HOLDING_HORIZON_HOURS,
    "max_holding_bars": MAX_HOLDING_BARS,
    "max_holding_frequency": MAX_HOLDING_FREQUENCY,
    "max_holding_source_field": MAX_HOLDING_SOURCE_FIELD,
    "max_holding_exit_rule": MAX_HOLDING_EXIT_RULE,
    "composite_trigger_policy": COMPOSITE_TRIGGER_POLICY,
}
