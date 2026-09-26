"""Authority and package constants for B10 robustness/stress proof."""

from __future__ import annotations

from src.ops.peak_trade_research_backtest_live_parity_v1.constants_v1 import (
    AUTHORITATIVE_FEATURE_IMPLEMENTATION,
    AUTHORITATIVE_RANKING_IMPLEMENTATION,
    CAP23_RERANK_COUNT,
    CAP23_RESCORE_COUNT,
    CAP23_SOLE_SELECTION_OWNER,
    CROSS_UNIVERSE_AUTHORITY,
    LIVE_EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    PROFILE_ONLY_SELECTION_EFFECT,
)

PACKAGE_ID = "PEAK_TRADE_B10_ROBUSTNESS_AND_STRESS_V1"
PACKAGE_VERSION = "peak_trade_b10_robustness_and_stress.v1"
OWNER_GO_THIS_SLICE = "OWNER_GO_B10_ROBUSTNESS_AND_STRESS_V1"

AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
RANKING_POLICY_CHANGED = False
FEATURE_FORMULA_CHANGED = False
FEATURE_SET_CHANGED = False
SELECTION_AUTHORITY_CREATED = False
BINDING_EFFECT = False
B11_STARTED = False

CAP22_RANKING_OWNER = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
CAP23_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
CAP24_BINDING_BOUNDARY = "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1"

ROBUSTNESS_DOMAINS: tuple[str, ...] = (
    "WALK_FORWARD",
    "SENSITIVITY",
    "MISSING_DATA",
    "STALE_INVALID_DATA",
    "OUTLIER_EXTREME_MOVEMENT",
    "DETERMINISM_REPRODUCIBILITY",
    "SINGLE_FEATURE_DOMINANCE",
    "AUTHORITY_PRESERVATION",
)

INFRASTRUCTURE_CENSUS_V1: tuple[dict[str, str], ...] = (
    {
        "surface": "historical/replay market inputs",
        "path": "src.ops.economic_md_input_producer_v1",
        "classification": "AUTHORITATIVE_REUSED",
    },
    {
        "surface": "finalized PT1M marks",
        "path": "src.ops.economic_md_input_producer_v1.validation_v1",
        "classification": "AUTHORITATIVE_REUSED",
    },
    {
        "surface": "ranking feature production",
        "path": AUTHORITATIVE_FEATURE_IMPLEMENTATION,
        "classification": "AUTHORITATIVE_REUSED",
    },
    {
        "surface": "economic ranking",
        "path": AUTHORITATIVE_RANKING_IMPLEMENTATION,
        "classification": "AUTHORITATIVE_REUSED",
    },
    {
        "surface": "B09 parity harness",
        "path": "src.ops.peak_trade_research_backtest_live_parity_v1",
        "classification": "CURRENT_REUSABLE",
    },
    {
        "surface": "deterministic fixtures",
        "path": "tests.ops.test_peak_trade_research_backtest_live_parity_v1",
        "classification": "CURRENT_REUSABLE",
    },
    {
        "surface": "evaluation/report artifacts",
        "path": "docs/evidence/peak_trade_research_backtest_live_parity_v1",
        "classification": "CURRENT_NEEDS_BOUNDED_EXTENSION",
    },
    {
        "surface": "walk-forward/replay windows",
        "path": "B10 deterministic scenario enumeration",
        "classification": "CURRENT_NEEDS_BOUNDED_EXTENSION",
    },
    {
        "surface": "missing/stale/invalid input injection",
        "path": "B10 deterministic scenario enumeration",
        "classification": "CURRENT_NEEDS_BOUNDED_EXTENSION",
    },
    {
        "surface": "stress/perturbation facilities",
        "path": "B10 deterministic scenario enumeration",
        "classification": "CURRENT_NEEDS_BOUNDED_EXTENSION",
    },
)


def authority_block_v1() -> dict[str, object]:
    return {
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "B11_STARTED": B11_STARTED,
        "BINDING_EFFECT": BINDING_EFFECT,
        "CAP22_RANKING_OWNER": CAP22_RANKING_OWNER,
        "CAP23_RERANK_COUNT": CAP23_RERANK_COUNT,
        "CAP23_RESCORE_COUNT": CAP23_RESCORE_COUNT,
        "CAP23_SELECTION_OWNER": CAP23_SELECTION_OWNER,
        "CAP23_SOLE_SELECTION_OWNER": CAP23_SOLE_SELECTION_OWNER,
        "CAP24_BINDING_BOUNDARY": CAP24_BINDING_BOUNDARY,
        "CROSS_UNIVERSE_AUTHORITY": CROSS_UNIVERSE_AUTHORITY,
        "FEATURE_FORMULA_CHANGED": FEATURE_FORMULA_CHANGED,
        "FEATURE_SET_CHANGED": FEATURE_SET_CHANGED,
        "LIVE_EXTERNAL_EFFECT_AUTHORIZED": LIVE_EXTERNAL_EFFECT_AUTHORIZED,
        "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "PROFILE_ONLY_SELECTION_EFFECT": PROFILE_ONLY_SELECTION_EFFECT,
        "RANKING_POLICY_CHANGED": RANKING_POLICY_CHANGED,
        "RUNTIME_AUTHORIZATION_EFFECT": RUNTIME_AUTHORIZATION_EFFECT,
        "SELECTION_AUTHORITY_CREATED": SELECTION_AUTHORITY_CREATED,
    }
