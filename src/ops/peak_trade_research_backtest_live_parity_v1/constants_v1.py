"""Authority-bounded constants for B09 Peak_Trade ranking parity."""

from __future__ import annotations

from src.ops.peak_trade_economic_ranking_runtime_v1.constants_v1 import (
    RANKING_POLICY_ID,
    RANKING_POLICY_VERSION,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    CONTRACT_ID as FEATURE_CONTRACT_ID,
    CONTRACT_VERSION as FEATURE_CONTRACT_VERSION,
    RATIFIED_ECONOMIC_FEATURE_POLICY_IDS,
)

PACKAGE_MARKER = "PEAK_TRADE_RESEARCH_BACKTEST_LIVE_PARITY_V1=true"
PARITY_PACKAGE_ID = "PEAK_TRADE_RESEARCH_BACKTEST_LIVE_PARITY_V1"
PARITY_VERSION = "peak_trade_research_backtest_live_parity.v1"
OWNER_GO_THIS_SLICE = "OWNER_GO_B09_RESEARCH_BACKTEST_LIVE_PARITY_V1"

AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
RESEARCH_BACKTEST_SHADOW_PRODUCTIVE_AUTHORITY_CREATED = False
RANKING_POLICY_CHANGED = False
FEATURE_FORMULA_CHANGED = False
CAP22_RANKING_OWNER = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
CAP23_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
CAP24_BINDING_BOUNDARY = "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"

CAP23_RESCORE_COUNT = 0
CAP23_RERANK_COUNT = 0
CAP23_SOLE_SELECTION_OWNER = True
PROFILE_ONLY_SELECTION_EFFECT = False
CROSS_UNIVERSE_AUTHORITY = "NONE"
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
MAX_POSITIONS_EFFECTIVE = 1
LIVE_EXTERNAL_EFFECT_AUTHORIZED = False
B10_STARTED = False

PARITY_MODES: tuple[str, ...] = ("PRODUCTIVE", "RESEARCH", "BACKTEST", "SHADOW")
PRODUCTIVE_MODE = "PRODUCTIVE"

PARITY_SSOT = (
    "B03 policy + B04 feature contract + B05 "
    "compute_b03_ratified_raw_features_pure_v1 + B06 "
    "build_balanced_movement_scores_v1/classify_and_rank_economic_candidates_v1"
)
AUTHORITATIVE_FEATURE_IMPLEMENTATION = (
    "src.ops.peak_trade_ranking_feature_production_v1.producer_v1."
    "compute_b03_ratified_raw_features_pure_v1"
)
AUTHORITATIVE_RANKING_IMPLEMENTATION = (
    "src.ops.peak_trade_economic_ranking_runtime_v1.economic_rank_v1."
    "classify_and_rank_economic_candidates_v1"
)

REQUIRED_POLICY_IDENTITY: dict[str, object] = {
    "ranking_policy_id": RANKING_POLICY_ID,
    "ranking_policy_version": RANKING_POLICY_VERSION,
    "feature_contract_id": FEATURE_CONTRACT_ID,
    "feature_contract_version": FEATURE_CONTRACT_VERSION,
    "ratified_economic_feature_policy_ids": list(RATIFIED_ECONOMIC_FEATURE_POLICY_IDS),
}

CURRENT_PATH_CLASSIFICATION_V1: tuple[dict[str, str], ...] = (
    {
        "path": "src/ops/peak_trade_ranking_matrix_policy_v1.py",
        "classification": "AUTHORITATIVE_SHARED",
        "reason": "B03 ratified policy semantics and digest identity.",
    },
    {
        "path": "src/ops/peak_trade_ranking_feature_contract_v1.py",
        "classification": "AUTHORITATIVE_SHARED",
        "reason": "B04 versioned feature/explainability contract.",
    },
    {
        "path": "src/ops/peak_trade_ranking_feature_production_v1/",
        "classification": "AUTHORITATIVE_SHARED",
        "reason": "B05 canonical raw feature production and pure compute seam.",
    },
    {
        "path": "src/ops/peak_trade_economic_ranking_runtime_v1/",
        "classification": "AUTHORITATIVE_SHARED",
        "reason": "B06 canonical score construction and rank/order semantics.",
    },
    {
        "path": "src/ops/productive_futures_ranking_producer_v1/",
        "classification": "SHARED_CONSUMER",
        "reason": "Productive Cap 2.2 producer delegates ranking to B06 runtime seam.",
    },
    {
        "path": "src/ops/future_profile_snapshot_v1/",
        "classification": "SHARED_CONSUMER",
        "reason": "B07 observes existing B05/B06 witnesses; no recomputation authority.",
    },
    {
        "path": "src/ops/single_selected_future_policy_v1/",
        "classification": "SHARED_CONSUMER",
        "reason": "B08 proves Cap 2.3 consumes upstream rank without rescore/rerank.",
    },
    {
        "path": "src/backtest/step29m_current_single_selected_future_dynamic_binding_v1.py",
        "classification": "NOT_APPLICABLE",
        "reason": "STEP29M consumes post-selection identity only; ranking consumption forbidden.",
    },
    {
        "path": "src/research/cross_sectional_*",
        "classification": "LEGACY_NOT_CURRENT",
        "reason": "Offline research archetypes use separate research hypotheses, not CURRENT Cap 2.2.",
    },
    {
        "path": "src/ops/productive_pure_stack_numeric_policy_shadow_campaign_v1/",
        "classification": "NOT_APPLICABLE",
        "reason": "Shadow campaign numeric policy is not CURRENT Cap 2.2 ranking authority.",
    },
)
