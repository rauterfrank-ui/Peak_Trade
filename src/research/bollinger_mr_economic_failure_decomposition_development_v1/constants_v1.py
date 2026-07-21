"""Frozen constants for Bollinger/MR economic failure decomposition on DEVELOPMENT_ONLY panel."""

from __future__ import annotations

SCOPE_ID = "bollinger_mr_economic_failure_decomposition_development_v1"
EVIDENCE_CLASS_ID = "BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_EVIDENCE_V1"
EXECUTION_ID = "BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_EXECUTION_V1"
PROCESS_CLASSIFICATION = EXECUTION_ID
SCOPE_CLASSIFICATION = (
    "READ_ONLY_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_ONLY_BOLLINGER_MR_BASELINE_V1"
)

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
PRIMARY_SEED = 20220601

DECISION_START = "2023-05-20T00:00:00Z"
DECISION_END_EXCLUSIVE = "2023-08-16T05:55:00Z"
DEVELOPMENT_SPLIT_DIGEST = "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
EXPECTED_MANIFEST_SHA256 = "be953c559ac3dd797961bdda8cbc190076353c91d3299b9031ae1ee767d4b594"
EXPECTED_CONTENT_HASH = "4a1978fe0e69a6cd7b19b32f5f95882cfdc3e36397aaec87bce2c4139ab1cfca"
MAX_FEATURE_LOOKBACK_HOURS = 168

# Parent sealed DEVELOPMENT baseline metrics (ADX DI control arm) — binding reference.
PARENT_BASELINE_EVIDENCE_REF = (
    "docs/evidence/evaluate_adx_di_direction_confirmation_mr_eligibility_development_v1/"
)
PARENT_BASELINE_METRICS = {
    "trade_count": 117,
    "long_trades": 21,
    "short_trades": 96,
    "gross_pnl": -890.3483239437896,
    "fees": 459.42545240128703,
    "slippage": 229.71272620064352,
    "net_pnl": -1579.4865025457202,
    "profit_factor": 0.7324360833782796,
}

COST_STRESS_MULTIPLIERS = (0.5, 1.0, 1.5, 2.0)

DIAGNOSTIC_CLASSES = (
    "ENTRY_HAS_NO_GROSS_EDGE",
    "ENTRY_EDGE_LOST_AT_EXIT",
    "SHORT_SIDE_STRUCTURAL_DRAG",
    "COSTS_DESTROY_MARGINAL_EDGE",
    "INSTRUMENT_CONCENTRATION_ONLY",
    "MIXED_OR_INCONCLUSIVE",
)

SLEEVE_INITIAL_CASH = 10_000.0
SHARED_INITIAL_CAPITAL = 10_000.0

CONTRACT_REL_PATH = (
    "config/research/bollinger_mr_economic_failure_decomposition_development_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/BOLLINGER_MR_ECONOMIC_FAILURE_DECOMPOSITION_DEVELOPMENT_V1.md"
)
EVIDENCE_REL_PATH = "docs/evidence/bollinger_mr_economic_failure_decomposition_development_v1/"

HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
