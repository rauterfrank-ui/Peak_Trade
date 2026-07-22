"""Frozen identity constants for Exit V8 holdout evaluation wiring v1."""

from __future__ import annotations

EVALUATION_RUN_ID = "evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1"
OWNER_SURFACE = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_EVALUATION_V1"
HYPOTHESIS_ID = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_HOLDOUT_V1"
PREDECESSOR_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8"
)
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1"
PANEL_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
DATASET_CLASS = "SEALED_HOLDOUT_FINAL_AUDIT_ONLY"
HOLDOUT_PREREGISTRATION_DIGEST = "a0658fe3fb883939ed2a2de2c426f2e4edf21eeeb91d1b902d45b4d05a38fd1d"
V8_PREREGISTRATION_DIGEST = "610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c"
HOLDOUT_SPLIT_DIGEST = "e29eeb4e9d264e1529a0c7419d707ce84df7919ee6ed95a833612fca46a7184d"
EXPECTED_CONTENT_HASH = "7bcda794ae2a355c6f36b2ea04703f39078063458f52034add44bec5644206bb"
EXPECTED_MANIFEST_SHA256 = "f4c616c556ff3f2500bb5deff2070c5ee9c4b6a5d5d6ca5da3dc7aca1e8a3e56"
PERIOD_START = "2023-08-16T05:55:00Z"
PERIOD_END_EXCLUSIVE = "2024-09-01T00:00:00Z"
INSTRUMENT_COUNT = 65
SEALED_ARCHIVE_SUBDIR = "sealed_lifecycle_long_panel_v1_d884a000_20260720T1832Z"

REQUIRED_EXIT_LANE_STATUS = "OPEN_BACKLOG"
REQUIRED_ENTRY_LANE_STATUS = "LANE_CLOSED_NO_FURTHER_RESEARCH"
REQUIRED_SUCCESSOR_STATUS = "DEFINITION_ONLY_HOLDOUT_PREREGISTERED"

CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistered_measurement_contract_v1.json"
)
EVIDENCE_REL_PATH = "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1/"
CLI_REL_PATH = (
    "scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1.py"
)
EXIT_BACKLOG_REL_PATH = (
    "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
)
ENTRY_BACKLOG_REL_PATH = (
    "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
)

CONSUMED_MARKER_FILENAME = ".holdout_run_consumed"
LOCK_FILENAME = ".holdout_run.lock"
RUN_SLOT_CLAIM_FILENAME = "run_slot_claim.json"
RUNNER_START_MARKER_FILENAME = ".holdout_runner_started"

FEE_BPS = 10.0
SLIPPAGE_BPS = 5.0
HALF_SPREAD_BPS = 5.0
PRIMARY_SEED = 20220601
BB_PERIOD = 20
MAX_FEATURE_LOOKBACK_HOURS = 20
MINIMUM_TRADE_COUNT = 20
MAX_TRADE_COUNT_REDUCTION_FRACTION = 0.5
INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX = 0.35
COST_MULTIPLIER = 1.0
STRATEGY_ID = "bollinger_bands"
BASELINE_CONFIG_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
