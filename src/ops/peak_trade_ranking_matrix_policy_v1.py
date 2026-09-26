"""Peak Trade Ranking Matrix Policy V1 (B03 Owner-ratified).

Persists the Owner-ratified Cap 2.2 productive ranking policy matrix
(PEAK_TRADE_RANKING_MATRIX_POLICY_V1). Grants CAP22_RANKING_POLICY_AUTHORITY
only. Does not wire productive Cap 2.2 economic ranking runtime (B06), does
not activate economic rank, and does not grant selection, execution, live,
testnet, or multi-future authority. B04/B05 are separate bounded slices.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    canonical_digest_v1,
)

POLICY_ID = "PEAK_TRADE_RANKING_MATRIX_POLICY_V1"
POLICY_VERSION = "v1"
CONTRACT_ID = POLICY_ID
SCHEMA_VERSION = "peak_trade_ranking_matrix_policy.v1"
OWNER_GO_THIS_SLICE = "PEAK_TRADE_B03_GOVERNANCE_PERSISTENCE_V1"
BOUND_ORIGIN_MAIN_SHA = "9911495cb95776be55d32f2628cbd1c8dd702b59"
AUTHORITY_EFFECT = "CAP22_RANKING_POLICY_AUTHORITY_PERSIST_ONLY"

CAPABILITY_ID_CAP22 = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
PRODUCTIVE_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"

B03_RATIFIED = True
RANKING_OBJECTIVE_RATIFIED = True
VOLATILITY_POLICY_RATIFIED = True
AMPLITUDE_POLICY_RATIFIED = True
SCORE_CONSTRUCTION_RATIFIED = True
CROSS_SECTIONAL_NORMALIZATION_RATIFIED = True
INCOMPLETE_FEATURE_POLICY_RATIFIED = True
PROFILE_PROMOTION_V1_RATIFIED = True

RANKING_OBJECTIVE = "BALANCED_MOVEMENT_STRUCTURE"
EQUAL_IMPORTANCE_POLICY_AXIOM = True
AUTHORITY_SCOPE = "CAP22_RANKING_ONLY"

VOLATILITY_POLICY_ID = "CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1"
VOLATILITY_INPUT = "61_CONTIGUOUS_FINALIZED_PT1M_MARK_PRICES"
RETURN_COUNT = 60
MARK_COUNT = 61
DDOF = 0
ANNUALIZED = False
VOLATILITY_UNITS = "PER_BAR_DECIMAL_RETURN_VOLATILITY"
VOLATILITY_DIRECTION = "HIGHER_IS_BETTER"
VOLATILITY_RAW_FEATURE_NORMALIZATION = "NONE"

AMPLITUDE_POLICY_ID = "CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1"
AMPLITUDE_INPUT = "SAME_61_CONTIGUOUS_FINALIZED_PT1M_MARK_PRICES"
AMPLITUDE_FORMULA = "(MAX_MARK-MIN_MARK)/((MAX_MARK+MIN_MARK)/2)"
AMPLITUDE_UNITS = "DIMENSIONLESS_FRACTION"
AMPLITUDE_DIRECTION = "HIGHER_IS_BETTER"
AMPLITUDE_RAW_FEATURE_NORMALIZATION = "NONE"
AMPLITUDE_REQUIRES_P_MIN_GT_ZERO = True
AMPLITUDE_REQUIRES_MID_GT_ZERO = True

STRUCTURAL_ECONOMIC_SEPARATION = "HARD_INVARIANT"
COMPLETE_ECONOMIC_RANK_SET_SYMBOL = "S_STAR"

SCORE_CONSTRUCTION = "EQUAL_WEIGHT_CROSS_SECTIONAL_MIDRANK_PERCENTILE_COMPOSITE_V1"
TIE_RANK_METHOD = "MIDRANK_DETERMINISTIC"
FEATURE_PERCENTILE_FORMULA_N_GT_1 = "(N-FEATURE_MIDRANK)/(N-1)"
VOLATILITY_WEIGHT = 0.5
AMPLITUDE_WEIGHT = 0.5
NORMATIVE_EQUAL_IMPORTANCE_WEIGHTS = True
EMPIRICALLY_ESTIMATED = False

ORDER_PRIMARY = "BALANCED_MOVEMENT_SCORE_DESC"
ORDER_SECONDARY = "VENUE_NATIVE_ID_ASC"
ORDER_TERTIARY = "CANONICAL_INSTRUMENT_ID_ASC"
VENUE_NATIVE_ORDER_IS_NOT_MARKET_ATTRACTIVENESS = True

ECONOMIC_RANK_STATE_N0 = "NO_COMPLETE_ECONOMIC_CANDIDATES"
SINGLETON_CROSS_SECTION_STATE = "NEUTRAL"
SINGLETON_VOLATILITY_PERCENTILE = 0.5
SINGLETON_AMPLITUDE_PERCENTILE = 0.5
SINGLETON_BALANCED_MOVEMENT_SCORE = 0.5

CROSS_SECTIONAL_DEPENDENCY = "EXPECTED_AND_AUTHORIZED"

FC_ECON_POLICY = "INCOMPLETE_FEATURE_CANDIDATE_EXPLICIT_EXCLUSION_V1"
INSUFFICIENT_WARMUP_THRESHOLD_MARKS = 61
INSUFFICIENT_WARMUP_REASON = "INCOMPLETE_FEATURE_CANDIDATE"
INSUFFICIENT_WARMUP_SUBCODE = "INSUFFICIENT_PT1M_MARK_WARMUP"

STALE_INPUT2_BEHAVIOR = "SNAPSHOT_LEVEL_FAIL_CLOSED"

PROFILE_PROMOTION_V1 = "NONE_ADDITIONAL"
PROFILE_AUTHORITY_EFFECT = "NONE"

PRODUCTIVE_INPUT2_VENUE = "OKX_EEA"
PRODUCTIVE_INPUT2_HOST = "eea.okx.com"
WWW_OKX_PRODUCTIVE_INPUT2_AUTHORITY = "NONE"

CAP22_RANKING_POLICY_AUTHORITY = True
CAP23_SELECTION_AUTHORITY_ADDED = False
SOLE_PRODUCTIVE_SELECTION_OWNER = True
CROSS_UNIVERSE_AUTHORITY = "NONE"

INPUT2_MAX_AGE_SECONDS_RATIFIED = False
INPUT2_MAX_AGE_SECONDS = "UNRATIFIED"
OWNER_THRESHOLD_REQUIRED = True

POLICY_RATIFIED = True
RUNTIME_ACTIVATED = False
PRODUCTIVE_ECONOMIC_RANK_ACTIVATION = False
ECONOMIC_RANK_ACTIVATED = False
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED = False

FINAL_SCORE_FORMULA_RATIFIED = True
FINAL_WEIGHTS_RATIFIED = True

RUNTIME_WIRING_ADDED_BY_THIS_SLICE = False
B04_IMPLEMENTED = True
B05_IMPLEMENTED = True
B06_IMPLEMENTED = False

RESIDUAL_TIE_BREAK: tuple[str, ...] = (
    "venue_native_id ASC",
    "canonical_instrument_id ASC",
)

FALSE_REQUIRED_FLAGS: tuple[str, ...] = (
    "b06_implemented",
    "cap22_productive_economic_runtime_wired",
    "cap23_selection_authority_added",
    "economic_rank_activated",
    "empirically_estimated",
    "input2_max_age_seconds_ratified",
    "productive_economic_rank_activation",
    "runtime_activated",
    "runtime_wiring_added_by_this_slice",
)

TRUE_REQUIRED_FLAGS: tuple[str, ...] = (
    "b04_implemented",
    "b05_implemented",
    "b03_ratified",
    "cap22_ranking_policy_authority",
    "cross_sectional_normalization_ratified",
    "equal_importance_policy_axiom",
    "final_score_formula_ratified",
    "final_weights_ratified",
    "incomplete_feature_policy_ratified",
    "normative_equal_importance_weights",
    "policy_ratified",
    "ranking_objective_ratified",
    "score_construction_ratified",
    "sole_productive_selection_owner",
    "structural_economic_separation",
    "volatility_policy_ratified",
    "amplitude_policy_ratified",
    "profile_promotion_v1_ratified",
)


class PeakTradeRankingMatrixPolicyError(ValueError):
    """Fail-closed ranking matrix policy contract error."""


def _require_mapping(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise PeakTradeRankingMatrixPolicyError("RANKING_MATRIX_DECLARATION_NOT_A_MAPPING")
    return payload


def _require_false_flags(raw: Mapping[str, Any]) -> None:
    for key in FALSE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not False:
            raise PeakTradeRankingMatrixPolicyError("RANKING_MATRIX_FALSE_FLAG_VIOLATION", key)


def _require_true_flags(raw: Mapping[str, Any]) -> None:
    for key in TRUE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not True:
            raise PeakTradeRankingMatrixPolicyError("RANKING_MATRIX_TRUE_FLAG_VIOLATION", key)


def build_ranking_matrix_policy_semantic_payload_v1() -> dict[str, Any]:
    """Canonical semantic payload bound by policy_digest (excludes digest field)."""
    return {
        "amplitude_direction": AMPLITUDE_DIRECTION,
        "amplitude_formula": AMPLITUDE_FORMULA,
        "amplitude_input": AMPLITUDE_INPUT,
        "amplitude_policy_id": AMPLITUDE_POLICY_ID,
        "amplitude_raw_feature_normalization": AMPLITUDE_RAW_FEATURE_NORMALIZATION,
        "amplitude_units": AMPLITUDE_UNITS,
        "amplitude_weight": AMPLITUDE_WEIGHT,
        "authority_scope": AUTHORITY_SCOPE,
        "cross_sectional_dependency": CROSS_SECTIONAL_DEPENDENCY,
        "cross_sectional_normalization_ratified": CROSS_SECTIONAL_NORMALIZATION_RATIFIED,
        "ddof": DDOF,
        "economic_rank_state_n0": ECONOMIC_RANK_STATE_N0,
        "empirically_estimated": EMPIRICALLY_ESTIMATED,
        "equal_importance_policy_axiom": EQUAL_IMPORTANCE_POLICY_AXIOM,
        "fc_econ_policy": FC_ECON_POLICY,
        "feature_percentile_formula_n_gt_1": FEATURE_PERCENTILE_FORMULA_N_GT_1,
        "input2_max_age_seconds": INPUT2_MAX_AGE_SECONDS,
        "input2_max_age_seconds_ratified": INPUT2_MAX_AGE_SECONDS_RATIFIED,
        "insufficient_warmup_reason": INSUFFICIENT_WARMUP_REASON,
        "insufficient_warmup_subcode": INSUFFICIENT_WARMUP_SUBCODE,
        "insufficient_warmup_threshold_marks": INSUFFICIENT_WARMUP_THRESHOLD_MARKS,
        "mark_count": MARK_COUNT,
        "normative_equal_importance_weights": NORMATIVE_EQUAL_IMPORTANCE_WEIGHTS,
        "order_primary": ORDER_PRIMARY,
        "order_secondary": ORDER_SECONDARY,
        "order_tertiary": ORDER_TERTIARY,
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "productive_input2_host": PRODUCTIVE_INPUT2_HOST,
        "productive_input2_venue": PRODUCTIVE_INPUT2_VENUE,
        "profile_authority_effect": PROFILE_AUTHORITY_EFFECT,
        "profile_promotion_v1": PROFILE_PROMOTION_V1,
        "ranking_objective": RANKING_OBJECTIVE,
        "return_count": RETURN_COUNT,
        "score_construction": SCORE_CONSTRUCTION,
        "singleton_amplitude_percentile": SINGLETON_AMPLITUDE_PERCENTILE,
        "singleton_balanced_movement_score": SINGLETON_BALANCED_MOVEMENT_SCORE,
        "singleton_cross_section_state": SINGLETON_CROSS_SECTION_STATE,
        "singleton_volatility_percentile": SINGLETON_VOLATILITY_PERCENTILE,
        "stale_input2_behavior": STALE_INPUT2_BEHAVIOR,
        "structural_economic_separation": STRUCTURAL_ECONOMIC_SEPARATION,
        "tie_rank_method": TIE_RANK_METHOD,
        "volatility_annualized": ANNUALIZED,
        "volatility_direction": VOLATILITY_DIRECTION,
        "volatility_input": VOLATILITY_INPUT,
        "volatility_policy_id": VOLATILITY_POLICY_ID,
        "volatility_raw_feature_normalization": VOLATILITY_RAW_FEATURE_NORMALIZATION,
        "volatility_units": VOLATILITY_UNITS,
        "volatility_weight": VOLATILITY_WEIGHT,
        "www_okx_productive_input2_authority": WWW_OKX_PRODUCTIVE_INPUT2_AUTHORITY,
    }


def compute_ranking_matrix_policy_digest_v1() -> str:
    return canonical_digest_v1(build_ranking_matrix_policy_semantic_payload_v1())


def classify_peak_trade_ranking_matrix_policy_v1() -> dict[str, Any]:
    return {
        "amplitude_policy_id": AMPLITUDE_POLICY_ID,
        "authority_scope": AUTHORITY_SCOPE,
        "b03_ratified": B03_RATIFIED,
        "cap22_ranking_policy_authority": CAP22_RANKING_POLICY_AUTHORITY,
        "cap23_selection_authority_added": CAP23_SELECTION_AUTHORITY_ADDED,
        "contract_id": CONTRACT_ID,
        "cross_universe_authority": CROSS_UNIVERSE_AUTHORITY,
        "economic_rank_activated": ECONOMIC_RANK_ACTIVATED,
        "fc_econ_policy": FC_ECON_POLICY,
        "input2_max_age_seconds": INPUT2_MAX_AGE_SECONDS,
        "input2_max_age_seconds_ratified": INPUT2_MAX_AGE_SECONDS_RATIFIED,
        "owner_threshold_required": OWNER_THRESHOLD_REQUIRED,
        "policy_digest": compute_ranking_matrix_policy_digest_v1(),
        "policy_id": POLICY_ID,
        "policy_ratified": POLICY_RATIFIED,
        "policy_version": POLICY_VERSION,
        "productive_economic_rank_activation": PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
        "productive_selection_owner": PRODUCTIVE_SELECTION_OWNER,
        "ranking_objective": RANKING_OBJECTIVE,
        "runtime_activated": RUNTIME_ACTIVATED,
        "runtime_wiring_added_by_this_slice": RUNTIME_WIRING_ADDED_BY_THIS_SLICE,
        "schema_version": SCHEMA_VERSION,
        "score_construction": SCORE_CONSTRUCTION,
        "sole_productive_selection_owner": SOLE_PRODUCTIVE_SELECTION_OWNER,
        "volatility_policy_id": VOLATILITY_POLICY_ID,
    }


def validate_peak_trade_ranking_matrix_policy_declaration_v1(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw = _require_mapping(payload)
    _require_false_flags(raw)
    _require_true_flags(raw)
    if raw.get("policy_id") not in (None, POLICY_ID):
        raise PeakTradeRankingMatrixPolicyError("POLICY_ID_MISMATCH")
    if raw.get("input2_max_age_seconds") not in (None, INPUT2_MAX_AGE_SECONDS):
        raise PeakTradeRankingMatrixPolicyError("INPUT2_MAX_AGE_MUST_REMAIN_UNRATIFIED")
    if raw.get("productive_selection_owner") not in (None, PRODUCTIVE_SELECTION_OWNER):
        raise PeakTradeRankingMatrixPolicyError("CAP23_REMAINS_SOLE_SELECTION_OWNER")
    expected_digest = compute_ranking_matrix_policy_digest_v1()
    declared = raw.get("policy_digest")
    if declared is not None and declared != expected_digest:
        raise PeakTradeRankingMatrixPolicyError("POLICY_DIGEST_MISMATCH")
    return {
        "contract_id": CONTRACT_ID,
        "policy_digest": expected_digest,
        "policy_id": POLICY_ID,
        "policy_version": POLICY_VERSION,
        "valid": True,
    }
