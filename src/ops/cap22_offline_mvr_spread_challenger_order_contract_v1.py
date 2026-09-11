"""Cap 2.2 offline MVR spread definition, zero handling, and comparison keys V1.

Persists the Owner-ratified offline calculation semantics required to
compute the already-authorized Cap 2.2 MVR challenger classes on
identical PIT inputs. Does not implement ranking, does not implement an
evidence harness, does not wire productive economic ranking, does not
ratify score formula or weights, does not close PDF Step 5, does not
authorize rotation apply, does not allow PDF Step 7, and does not grant
multi-future runtime authority.
"""

from __future__ import annotations

from typing import Any, Mapping

CONTRACT_ID = "CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_COMPARISON_KEYS_V1"
DECISION_ID = "CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_COMPARISON_KEYS_V1"
SCHEMA_VERSION = "cap22_offline_mvr_spread_challenger_order.v1"
OWNER_GO_THIS_SLICE = (
    "PEAK_TRADE_CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_COMPARISON_KEYS_V1"
)
BOUND_ORIGIN_MAIN_SHA = "577ebca3a95f962b2d3ab388071d258170e79a5b"
AUTHORITY_EFFECT = "OFFLINE_MVR_SPREAD_AND_COMPARISON_KEYS_PERSIST_ONLY"
PRODUCTIVE_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"

SPREAD_RAW_FIELDS: tuple[str, ...] = ("bidPx", "askPx")
SPREAD_FORMULA_RATIFIED = True
SPREAD_FORMULA_ID = "RELATIVE_BID_ASK_SPREAD_OVER_MID_V1"
SPREAD_FORMULA_AUTHORITY_SCOPE = "OFFLINE_MVR_COMPARISON_ONLY"
SPREAD_UNITS = "DIMENSIONLESS_DECIMAL_FRACTION"
SPREAD_DISPLAY_BPS_IS_NOT_CANONICAL_FEATURE = True
SPREAD_AGGREGATOR_RATIFIED = True
SPREAD_AGGREGATOR = "IDENTITY_SINGLE_SAME_CYCLE_QUOTE_V1"

ZERO_SPREAD_RAW_OBSERVATION_VALID = True
LOCKED_MARKET_IS_EXACT_ZERO_SPREAD = True
ZERO_SPREAD_MUST_NOT_PRODUCE_INFINITY = True
ZERO_SPREAD_MUST_NOT_PRODUCE_ARTIFICIAL_MAX_RATIO = True
POLICY_C_ZERO_SPREAD_RESULT = "NOT_RANKABLE_FOR_POLICY_C"
ZERO_SPREAD_DOES_NOT_MAKE_INSTRUMENT_GLOBALLY_INELIGIBLE = True

NEAR_ZERO_THRESHOLD_RATIFIED = False
NEAR_ZERO_SPREAD_SPECIAL_HANDLING = "NONE_UNTIL_SEPARATELY_RATIFIED"

OFFLINE_CHALLENGER_A_CANDIDATE_ID = "VOLATILITY_RANK_ONLY"
OFFLINE_CHALLENGER_B_CANDIDATE_ID = "HARD_SPREAD_GATE_THEN_VOLATILITY_RANK"
OFFLINE_CHALLENGER_C_CANDIDATE_ID = "VOLATILITY_TO_SPREAD_RATIO"
OFFLINE_CHALLENGER_D_CANDIDATE_ID = "LEXICOGRAPHIC_SPREAD_THEN_VOL"
NEGATIVE_CONTROL_ID = "CURRENT_STRUCTURAL_THEN_VENUE_ID_ASC"
OFFLINE_CHALLENGER_A_IS_NOT_ANTI_CHURN_POLICY_A = True
ANTI_CHURN_POLICY_A_UNCHANGED = True
POLICY_A_ROLE = "ANTI_CHURN_ADMISSION_ONLY"

VOLATILITY_RANK_ONLY_ORDER_RATIFIED = True
VOLATILITY_UNITS = "PER_BAR_DECIMAL_RETURN_VOLATILITY"
AUTHORIZED_VOLATILITY_WARMUP = "61_PT1M_MARKS_60_LOG_RETURNS"
VOLATILITY_RANK_ONLY_RESIDUAL_TIE_BREAK_RATIFIED = True
RESIDUAL_TIE_BREAK: tuple[str, ...] = (
    "venue_native_id ASC",
    "canonical_instrument_id ASC",
)
RESIDUAL_TIE_BREAK_IS_NOT_ECONOMIC_SIGNAL = True

HARD_SPREAD_GATE_THEN_VOL_STRUCTURE_RATIFIED = True
POLICY_B_THRESHOLD_MODE = "VERSIONED_OFFLINE_THRESHOLD_SET_REQUIRED"
POLICY_B_SINGLE_THRESHOLD_RATIFIED = False
POLICY_B_THRESHOLD_SET_RATIFIED = False

POLICY_C_RATIO_ORIENTATION_RATIFIED = True
POLICY_C_ZERO_HANDLING_RATIFIED = True
POLICY_C_RATIO_ORIENTATION = "VOLATILITY_DIVIDED_BY_RELATIVE_SPREAD_DESC"

POLICY_D_LEXICOGRAPHIC_KEYS_RATIFIED = True
POLICY_D_PRIMARY_SORT_DIRECTION_RATIFIED = True
POLICY_D_PRIMARY_KEY = "relative_spread ASC"
POLICY_D_SECONDARY_KEY = "volatility DESC"

NO_CHALLENGER_WINS_BY_THIS_SLICE = True
NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY = True
FINAL_SCORE_FORMULA_RATIFIED = False
FINAL_WEIGHTS_RATIFIED = False
CROSS_SECTIONAL_NORMALIZATION_RATIFIED = False
STALE_SECONDS_RATIFIED = False
COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED = False
RANKING_CADENCE_RATIFIED = False
FORWARD_LABEL_HORIZON_RATIFIED = False
HISTORICAL_REPLAY_HORIZON_RATIFIED = False
ECONOMIC_RANK_ACTIVATED = False
ECONOMIC_MD_PRODUCER_IMPLEMENTED = True
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED = False
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED = False
CAP21_BOUNDARY_PRESERVED = True
CAP21_RANKING_AUTHORITY_ADDED = False
CAP21_ECONOMIC_MD_AUTHORITY_ADDED = False
CAP22_REMAINS_RANKING_OWNER = True
CAP22_DIRECT_LIVE_VENUE_DEPENDENCY = False
DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK = True
SECOND_SELECTION_DECISION_DOWNSTREAM = False
PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION = "UNRESOLVED"
PDF_STEP_5_STATUS = "UNRESOLVED"
ROTATION_POLICY_STATUS = "FAIL_CLOSED_UNTIL_PDF_STEP_5"
APPLY_ROTATION_STATUS = "FAIL_CLOSED"
PDF_STEP_7_STATUS = "FORBIDDEN"
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED = False
RUNTIME_AUTHORITY_GRANTED = False
PRODUCTIVE_MF_HOST_JOIN = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
NEXT_CANONICAL_DECISION = "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION"
NEXT_CAP22_DEPENDENCY = (
    "SEPARATE_OWNER_GO_REQUIRED_TO_DEFINE_POLICY_B_VERSIONED_OFFLINE_THRESHOLD_SET_"
    "THEN_RUN_OFFLINE_MVR_EVIDENCE_WITHOUT_WIRING"
)

FALSE_REQUIRED_FLAGS: tuple[str, ...] = (
    "cap21_economic_md_authority_added",
    "cap21_ranking_authority_added",
    "cap22_direct_live_venue_dependency",
    "cap22_productive_economic_runtime_wired",
    "collection_skew_numeric_bound_ratified",
    "cross_sectional_normalization_ratified",
    "economic_md_producer_productively_scheduled",
    "economic_rank_activated",
    "final_score_formula_ratified",
    "final_weights_ratified",
    "forward_label_horizon_ratified",
    "historical_replay_horizon_ratified",
    "multi_future_runtime_authorized",
    "near_zero_threshold_ratified",
    "pdf_step_7_runtime_implementation_allowed",
    "policy_b_single_threshold_ratified",
    "policy_b_threshold_set_ratified",
    "productive_mf_host_join",
    "ranking_cadence_ratified",
    "runtime_authority_granted",
    "second_selection_decision_downstream",
    "stale_seconds_ratified",
)

TRUE_REQUIRED_FLAGS: tuple[str, ...] = (
    "anti_churn_policy_a_unchanged",
    "cap21_boundary_preserved",
    "cap22_remains_ranking_owner",
    "downstream_execution_must_not_re_rank",
    "economic_md_producer_implemented",
    "hard_spread_gate_then_vol_structure_ratified",
    "no_challenger_wins_by_this_slice",
    "no_offline_policy_class_has_productive_authority",
    "offline_challenger_a_is_not_anti_churn_policy_a",
    "policy_c_ratio_orientation_ratified",
    "policy_c_zero_handling_ratified",
    "policy_d_lexicographic_keys_ratified",
    "policy_d_primary_sort_direction_ratified",
    "spread_aggregator_ratified",
    "spread_formula_ratified",
    "volatility_rank_only_order_ratified",
    "volatility_rank_only_residual_tie_break_ratified",
    "zero_spread_does_not_make_instrument_globally_ineligible",
    "zero_spread_raw_observation_valid",
)


class Cap22OfflineMvrSpreadComparisonKeysError(ValueError):
    """Fail-closed offline MVR spread comparison-keys contract error."""


def _require_mapping(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise Cap22OfflineMvrSpreadComparisonKeysError(
            "SPREAD_COMPARISON_KEYS_DECLARATION_NOT_A_MAPPING"
        )
    return payload


def _require_false_flags(raw: Mapping[str, Any]) -> None:
    for key in FALSE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not False:
            raise Cap22OfflineMvrSpreadComparisonKeysError(
                "SPREAD_COMPARISON_KEYS_FALSE_FLAG_VIOLATION", key
            )


def _require_true_flags(raw: Mapping[str, Any]) -> None:
    for key in TRUE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not True:
            raise Cap22OfflineMvrSpreadComparisonKeysError(
                "SPREAD_COMPARISON_KEYS_TRUE_FLAG_VIOLATION", key
            )


def classify_cap22_offline_mvr_spread_formula_v1() -> dict[str, Any]:
    return {
        "near_zero_spread_special_handling": NEAR_ZERO_SPREAD_SPECIAL_HANDLING,
        "near_zero_threshold_ratified": NEAR_ZERO_THRESHOLD_RATIFIED,
        "policy_c_zero_spread_result": POLICY_C_ZERO_SPREAD_RESULT,
        "spread_aggregator": SPREAD_AGGREGATOR,
        "spread_aggregator_ratified": SPREAD_AGGREGATOR_RATIFIED,
        "spread_display_bps_is_not_canonical_feature": (
            SPREAD_DISPLAY_BPS_IS_NOT_CANONICAL_FEATURE
        ),
        "spread_formula_authority_scope": SPREAD_FORMULA_AUTHORITY_SCOPE,
        "spread_formula_id": SPREAD_FORMULA_ID,
        "spread_formula_ratified": SPREAD_FORMULA_RATIFIED,
        "spread_raw_fields": SPREAD_RAW_FIELDS,
        "spread_units": SPREAD_UNITS,
        "zero_spread_does_not_make_instrument_globally_ineligible": (
            ZERO_SPREAD_DOES_NOT_MAKE_INSTRUMENT_GLOBALLY_INELIGIBLE
        ),
        "zero_spread_must_not_produce_artificial_max_ratio": (
            ZERO_SPREAD_MUST_NOT_PRODUCE_ARTIFICIAL_MAX_RATIO
        ),
        "zero_spread_must_not_produce_infinity": ZERO_SPREAD_MUST_NOT_PRODUCE_INFINITY,
        "zero_spread_raw_observation_valid": ZERO_SPREAD_RAW_OBSERVATION_VALID,
    }


def classify_cap22_offline_mvr_comparison_keys_v1() -> dict[str, Any]:
    return {
        "hard_spread_gate_then_vol_structure_ratified": (
            HARD_SPREAD_GATE_THEN_VOL_STRUCTURE_RATIFIED
        ),
        "negative_control_id": NEGATIVE_CONTROL_ID,
        "offline_challenger_a_candidate_id": OFFLINE_CHALLENGER_A_CANDIDATE_ID,
        "offline_challenger_a_is_not_anti_churn_policy_a": (
            OFFLINE_CHALLENGER_A_IS_NOT_ANTI_CHURN_POLICY_A
        ),
        "offline_challenger_b_candidate_id": OFFLINE_CHALLENGER_B_CANDIDATE_ID,
        "offline_challenger_c_candidate_id": OFFLINE_CHALLENGER_C_CANDIDATE_ID,
        "offline_challenger_d_candidate_id": OFFLINE_CHALLENGER_D_CANDIDATE_ID,
        "policy_b_single_threshold_ratified": POLICY_B_SINGLE_THRESHOLD_RATIFIED,
        "policy_b_threshold_mode": POLICY_B_THRESHOLD_MODE,
        "policy_b_threshold_set_ratified": POLICY_B_THRESHOLD_SET_RATIFIED,
        "policy_c_ratio_orientation": POLICY_C_RATIO_ORIENTATION,
        "policy_c_ratio_orientation_ratified": POLICY_C_RATIO_ORIENTATION_RATIFIED,
        "policy_c_zero_handling_ratified": POLICY_C_ZERO_HANDLING_RATIFIED,
        "policy_d_lexicographic_keys_ratified": POLICY_D_LEXICOGRAPHIC_KEYS_RATIFIED,
        "policy_d_primary_key": POLICY_D_PRIMARY_KEY,
        "policy_d_primary_sort_direction_ratified": (POLICY_D_PRIMARY_SORT_DIRECTION_RATIFIED),
        "policy_d_secondary_key": POLICY_D_SECONDARY_KEY,
        "residual_tie_break": RESIDUAL_TIE_BREAK,
        "residual_tie_break_is_not_economic_signal": (RESIDUAL_TIE_BREAK_IS_NOT_ECONOMIC_SIGNAL),
        "volatility_rank_only_order_ratified": VOLATILITY_RANK_ONLY_ORDER_RATIFIED,
        "volatility_rank_only_residual_tie_break_ratified": (
            VOLATILITY_RANK_ONLY_RESIDUAL_TIE_BREAK_RATIFIED
        ),
        "volatility_units": VOLATILITY_UNITS,
    }


def classify_preserved_program_invariants_v1() -> dict[str, Any]:
    return {
        "anti_churn_policy_a_unchanged": ANTI_CHURN_POLICY_A_UNCHANGED,
        "cap21_boundary_preserved": CAP21_BOUNDARY_PRESERVED,
        "cap21_economic_md_authority_added": CAP21_ECONOMIC_MD_AUTHORITY_ADDED,
        "cap21_ranking_authority_added": CAP21_RANKING_AUTHORITY_ADDED,
        "cap22_direct_live_venue_dependency": CAP22_DIRECT_LIVE_VENUE_DEPENDENCY,
        "cap22_productive_economic_runtime_wired": CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
        "cap22_remains_ranking_owner": CAP22_REMAINS_RANKING_OWNER,
        "downstream_execution_must_not_re_rank": DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK,
        "economic_md_producer_implemented": ECONOMIC_MD_PRODUCER_IMPLEMENTED,
        "economic_md_producer_productively_scheduled": (
            ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED
        ),
        "economic_rank_activated": ECONOMIC_RANK_ACTIVATED,
        "final_score_formula_ratified": FINAL_SCORE_FORMULA_RATIFIED,
        "final_weights_ratified": FINAL_WEIGHTS_RATIFIED,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "next_canonical_decision": NEXT_CANONICAL_DECISION,
        "next_cap22_dependency": NEXT_CAP22_DEPENDENCY,
        "no_challenger_wins_by_this_slice": NO_CHALLENGER_WINS_BY_THIS_SLICE,
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_runtime_implementation_allowed": PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED,
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "policy_a_role": POLICY_A_ROLE,
        "productive_mf_host_join": PRODUCTIVE_MF_HOST_JOIN,
        "productive_selection_owner": PRODUCTIVE_SELECTION_OWNER,
        "rotation_policy_status": ROTATION_POLICY_STATUS,
        "runtime_authority_granted": RUNTIME_AUTHORITY_GRANTED,
        "second_selection_decision_downstream": SECOND_SELECTION_DECISION_DOWNSTREAM,
    }


def validate_cap22_offline_mvr_spread_comparison_keys_declaration_v1(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw = _require_mapping(payload)
    _require_false_flags(raw)
    _require_true_flags(raw)
    if raw.get("spread_formula_id") not in (None, SPREAD_FORMULA_ID):
        raise Cap22OfflineMvrSpreadComparisonKeysError("SPREAD_FORMULA_ID_MISMATCH")
    if raw.get("spread_aggregator") not in (None, SPREAD_AGGREGATOR):
        raise Cap22OfflineMvrSpreadComparisonKeysError("SPREAD_AGGREGATOR_MISMATCH")
    if raw.get("spread_units") not in (None, SPREAD_UNITS):
        raise Cap22OfflineMvrSpreadComparisonKeysError("SPREAD_UNITS_MISMATCH")
    if raw.get("policy_c_zero_spread_result") not in (None, POLICY_C_ZERO_SPREAD_RESULT):
        raise Cap22OfflineMvrSpreadComparisonKeysError("POLICY_C_ZERO_SPREAD_RESULT_MISMATCH")
    if raw.get("policy_b_threshold_mode") not in (None, POLICY_B_THRESHOLD_MODE):
        raise Cap22OfflineMvrSpreadComparisonKeysError("POLICY_B_THRESHOLD_MODE_MISMATCH")
    if raw.get("offline_challenger_a_candidate_id") not in (
        None,
        OFFLINE_CHALLENGER_A_CANDIDATE_ID,
    ):
        raise Cap22OfflineMvrSpreadComparisonKeysError(
            "OFFLINE_CHALLENGER_A_MUST_REMAIN_VOLATILITY_RANK_ONLY"
        )
    if raw.get("policy_a_role") not in (None, POLICY_A_ROLE):
        raise Cap22OfflineMvrSpreadComparisonKeysError("ANTI_CHURN_POLICY_A_MUST_REMAIN_UNCHANGED")
    if raw.get("pdf_step_5_status") not in (None, PDF_STEP_5_STATUS):
        raise Cap22OfflineMvrSpreadComparisonKeysError("PDF_STEP_5_MUST_REMAIN_UNRESOLVED")
    if raw.get("rotation_policy_status") not in (None, ROTATION_POLICY_STATUS):
        raise Cap22OfflineMvrSpreadComparisonKeysError("ROTATION_MUST_REMAIN_FAIL_CLOSED")
    if raw.get("pdf_step_7_status") not in (None, PDF_STEP_7_STATUS):
        raise Cap22OfflineMvrSpreadComparisonKeysError("PDF_STEP_7_MUST_REMAIN_FORBIDDEN")
    if raw.get("productive_selection_owner") not in (None, PRODUCTIVE_SELECTION_OWNER):
        raise Cap22OfflineMvrSpreadComparisonKeysError("CAP23_REMAINS_PRODUCTIVE_SELECTION_OWNER")
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "contract_id": CONTRACT_ID,
        "decision_id": DECISION_ID,
        "schema_version": SCHEMA_VERSION,
        "spread_formula_id": SPREAD_FORMULA_ID,
        "valid": True,
    }
