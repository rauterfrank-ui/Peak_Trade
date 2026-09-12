"""Cap 2.2 offline policy-candidate and evidence contract V1.

Persists the Owner-ratified offline challenger set and the evidence
contract required before any Cap 2.2 ranking policy may be ratified.
Does not implement the Economic-MD producer, does not wire productive
economic ranking, does not ratify score formula or weights, does not
close PDF Step 5, does not authorize rotation apply, does not allow
PDF Step 7, and does not grant multi-future runtime authority.
"""

from __future__ import annotations

from typing import Any, Mapping

CONTRACT_ID = "CAP22_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_V1"
SCHEMA_VERSION = "cap22_offline_policy_candidates_and_evidence.v1"
OWNER_GO_THIS_SLICE = (
    "PEAK_TRADE_CAP_2_2_OFFLINE_POLICY_CANDIDATES_AND_EVIDENCE_CONTRACT_DOCS_ONLY_V1"
)
BOUND_ORIGIN_MAIN_SHA = "a9fd39d0fcaeb6bd202a5bd3e47aec87e0951b01"
AUTHORITY_EFFECT = "OFFLINE_POLICY_CANDIDATE_AND_EVIDENCE_CONTRACT_PERSIST_ONLY"
PRODUCTIVE_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"

CAP22_TARGET_RANK_MEANING = "TRADABLE_ECONOMIC_OPPORTUNITY_FOR_PEAK_TRADE"
CURRENT_PRODUCTIVE_ECONOMIC_RANKING = "NONE"
CURRENT_PRODUCTIVE_RANKING_POLICY = "productive_futures_universe_structural_ranking_v1"
CURRENT_STRUCTURAL_RANKING_IS_ECONOMIC_POLICY = False
AUTHORIZED_MVR_INPUTS = "FINALIZED_PT1M_MARK_PRICE_HISTORY+SAME_COLLECTION_CYCLE_BIDPX_ASKPX"
MVR_DATA_SUFFICIENT_FOR_POLICY_COMPARISON = True
CURRENT_PERSISTED_CAP22_ECONOMIC_MD_AVAILABLE = False
NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY = True

RECOMMENDED_PRIMARY_BASELINE = "VOLATILITY_RANK_ONLY"
VOLATILITY_RANK_ONLY_VERDICT = "BASELINE_ONLY"
VOLATILITY_RANK_ONLY = "OPPORTUNITY_BASELINE_NOT_TRADABILITY_COMPLETE"
NEGATIVE_STATUS_QUO_BASELINE = "CURRENT_STRUCTURAL_THEN_VENUE_ID_ASC"
CURRENT_ALPHABETICAL_BASELINE_VERDICT = "BASELINE_ONLY"
RECOMMENDED_OFFLINE_CHALLENGERS: tuple[str, ...] = (
    "HARD_SPREAD_GATE_THEN_VOLATILITY_RANK",
    "VOLATILITY_TO_SPREAD_RATIO",
    "LEXICOGRAPHIC_SPREAD_THEN_VOL",
)
HARD_SPREAD_GATE_THEN_VOLATILITY_RANK_VERDICT = "RECOMMENDED_OFFLINE_CHALLENGER"
VOLATILITY_TO_SPREAD_RATIO_VERDICT = "RECOMMENDED_OFFLINE_CHALLENGER"
LEXICOGRAPHIC_SPREAD_THEN_VOL_VERDICT = "RECOMMENDED_OFFLINE_CHALLENGER"
HARD_SPREAD_GATE_THEN_VOLATILITY_RANK = "FAIL_CLOSED_TRADABILITY_GATE_THEN_OPPORTUNITY"
VOLATILITY_TO_SPREAD_RATIO = "DIRECT_OPPORTUNITY_RELATIVE_TO_OBSERVED_FRICTION_CANDIDATE"
LEXICOGRAPHIC_SPREAD_THEN_VOL = "NO_ARTIFICIAL_WEIGHT_TOTAL_ORDER_CANDIDATE"
MULTIPLICATIVE_OPPORTUNITY_X_TRADABILITY_VERDICT = "DEFER"
WEIGHTED_ADDITIVE_COMPOSITE_VERDICT = "DEFER"
PARETO_VOL_AND_TRADABILITY_VERDICT = "REJECT_AS_TOP20_POLICY"
PARETO_DIAGNOSTIC_USE_ALLOWED = True

PIT_REPLAY_REQUIRED = True
FINALIZED_ONLY_REQUIRED = True
NO_LOOKAHEAD_REQUIRED = True
DETERMINISTIC_REPLAY_REQUIRED = True
WALK_FORWARD_REQUIRED = True
UNIVERSE_MEMBERSHIP_AT_HISTORICAL_T_REQUIRED = True
IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_COMPARISON = True
ECONOMIC_MD_SNAPSHOT_PROVENANCE_REQUIRED = True
RAW_INPUT_DIGEST_REQUIRED = True
FEATURE_DIGEST_REQUIRED = True
POLICY_ID_AND_VERSION_REQUIRED = True
RANKING_OUTPUT_DIGEST_REQUIRED = True
FORWARD_LABEL_WINDOW_STRICTLY_AFTER_FEATURE_TIME = True
RANK_STABILITY_TEST_REQUIRED = True
TOP20_TURNOVER_TEST_REQUIRED = True
FRICTION_SENSITIVITY_REQUIRED = True
NEW_LISTING_WARMUP_TEST_REQUIRED = True
MISSING_STALE_INPUT_STRESS_REQUIRED = True
VOLATILITY_LOOKBACK_VARIANT_IS_NEW_FEATURE_SEMANTICS = True
AUTHORIZED_VOLATILITY_BASE_GRID = "FINALIZED_PT1M"
AUTHORIZED_VOLATILITY_WARMUP = "61_PT1M_MARKS_60_LOG_RETURNS"

RANKING_OBJECTIVE_METRICS: tuple[str, ...] = (
    "FORWARD_ABS_RETURN",
    "FORWARD_REALIZED_VOL",
    "FRICTION_ADJUSTED_OPPORTUNITY",
    "CROSS_SECTIONAL_CAPTURE_TOP20",
    "SPEARMAN_RANK_ASSOCIATION_IF_DEFINED",
    "TOP20_TURNOVER",
    "RANK_STABILITY_TO_SMALL_INPUT_PERTURBATION",
)
SECONDARY_STRATEGY_METRICS: tuple[str, ...] = (
    "PNL",
    "SHARPE",
    "MAX_DRAWDOWN",
    "PROFIT_FACTOR",
    "TRADE_COUNT",
    "STRATEGY_TURNOVER",
    "FEE_SLIPPAGE_SENSITIVITY",
)
RANKING_OBJECTIVE_IS_NOT_DOWNSTREAM_PNL = True
STRATEGY_OUTCOME_METRICS_ARE_SECONDARY_CONFIRMATION = True

PER_INSTRUMENT_REQUIRED_RAW_INPUTS: tuple[str, ...] = (
    "canonical_instrument_id",
    "venue_native_id",
    "finalized_pt1m_mark_price_series",
    "mark_event_timestamp",
    "mark_receive_or_capture_timestamp",
    "same_cycle_bidPx",
    "same_cycle_askPx",
    "ticker_event_timestamp_if_available",
    "ticker_capture_timestamp",
    "collection_cycle_or_snapshot_identity",
    "universe_snapshot_reference",
    "economic_input_snapshot_id",
    "payload_digest",
    "provenance",
)
SPREAD_RAW_QUOTES_MUST_BE_PERSISTED = True
SPREAD_DERIVED_VALUE_ALONE_IS_INSUFFICIENT = True
ADDITIONAL_RAW_INPUT_REQUIRED = False
ADDITIONAL_RAW_INPUT_LIST = "NONE"

ROBUSTNESS_STRESS_CASES_REQUIRED: tuple[str, ...] = (
    "spread_spike",
    "stale_quote",
    "crossed_market",
    "locked_market",
    "zero_or_near_zero_spread",
    "missing_bars",
    "non_finalized_last_bar",
    "newly_listed_insufficient_warmup",
    "outlier_volatility",
    "outlier_spread",
    "instrument_drop_in_drop_out",
    "top20_boundary_instability",
)
MISSING_OR_INVALID_INPUT_SEMANTICS = "FAIL_CLOSED_NOT_RANKABLE"
NO_IMPLICIT_IMPUTATION_RATIFIED = True

DEFERRED_FEATURES: tuple[str, ...] = (
    "CONTRACT_VOLUME",
    "TURNOVER",
    "OPEN_INTEREST",
    "FUNDING",
    "ORDERBOOK_DEPTH",
    "PRICE_IMPACT",
    "MOMENTUM",
    "TREND",
    "ATR",
    "LISTING_AGE",
    "FEE_MODEL",
    "STATIC_SLIPPAGE_MODEL",
)

FINAL_SCORE_FORMULA_RATIFIED = False
FINAL_WEIGHTS_RATIFIED = False
CROSS_SECTIONAL_NORMALIZATION_RATIFIED = False
SPREAD_FORMULA_RATIFIED = True
SPREAD_FORMULA_ID = "RELATIVE_BID_ASK_SPREAD_OVER_MID_V1"
SPREAD_FORMULA_AUTHORITY = (
    "CAP22_OFFLINE_MVR_SPREAD_DEFINITION_ZERO_HANDLING_AND_COMPARISON_KEYS_V1"
)
SPREAD_AGGREGATOR_RATIFIED = True
SPREAD_AGGREGATOR = "IDENTITY_SINGLE_SAME_CYCLE_QUOTE_V1"
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
POLICY_A_ROLE = "ANTI_CHURN_ADMISSION_ONLY"
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
    "SEPARATE_OWNER_GO_REQUIRED_TO_RUN_HISTORICAL_PIT_WALK_FORWARD_WITHOUT_WIRING"
)

FALSE_REQUIRED_FLAGS: tuple[str, ...] = (
    "additional_raw_input_required",
    "cap21_economic_md_authority_added",
    "cap21_ranking_authority_added",
    "cap22_direct_live_venue_dependency",
    "cap22_productive_economic_runtime_wired",
    "collection_skew_numeric_bound_ratified",
    "cross_sectional_normalization_ratified",
    "current_structural_ranking_is_economic_policy",
    "economic_md_producer_productively_scheduled",
    "economic_rank_activated",
    "final_score_formula_ratified",
    "final_weights_ratified",
    "forward_label_horizon_ratified",
    "historical_replay_horizon_ratified",
    "multi_future_runtime_authorized",
    "pdf_step_7_runtime_implementation_allowed",
    "productive_mf_host_join",
    "ranking_cadence_ratified",
    "runtime_authority_granted",
    "second_selection_decision_downstream",
    "stale_seconds_ratified",
)

TRUE_REQUIRED_FLAGS: tuple[str, ...] = (
    "cap21_boundary_preserved",
    "cap22_remains_ranking_owner",
    "downstream_execution_must_not_re_rank",
    "economic_md_producer_implemented",
    "friction_sensitivity_required",
    "identical_candidate_universe_per_policy_comparison",
    "mvr_data_sufficient_for_policy_comparison",
    "new_listing_warmup_test_required",
    "no_lookahead_required",
    "no_offline_policy_class_has_productive_authority",
    "missing_stale_input_stress_required",
    "pit_replay_required",
    "rank_stability_test_required",
    "ranking_objective_is_not_downstream_pnl",
    "spread_aggregator_ratified",
    "spread_formula_ratified",
    "spread_raw_quotes_must_be_persisted",
    "top20_turnover_test_required",
    "walk_forward_required",
)


class Cap22OfflinePolicyCandidatesAndEvidenceError(ValueError):
    """Fail-closed offline policy-candidate and evidence contract error."""


def _require_mapping(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError(
            "OFFLINE_POLICY_DECLARATION_NOT_A_MAPPING"
        )
    return payload


def _require_false_flags(raw: Mapping[str, Any]) -> None:
    for key in FALSE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not False:
            raise Cap22OfflinePolicyCandidatesAndEvidenceError(
                "OFFLINE_POLICY_FALSE_FLAG_VIOLATION", key
            )


def _require_true_flags(raw: Mapping[str, Any]) -> None:
    for key in TRUE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not True:
            raise Cap22OfflinePolicyCandidatesAndEvidenceError(
                "OFFLINE_POLICY_TRUE_FLAG_VIOLATION", key
            )


def classify_cap22_offline_policy_candidates_v1() -> dict[str, Any]:
    return {
        "current_alphabetical_baseline_verdict": CURRENT_ALPHABETICAL_BASELINE_VERDICT,
        "current_productive_economic_ranking": CURRENT_PRODUCTIVE_ECONOMIC_RANKING,
        "current_productive_ranking_policy": CURRENT_PRODUCTIVE_RANKING_POLICY,
        "current_structural_ranking_is_economic_policy": (
            CURRENT_STRUCTURAL_RANKING_IS_ECONOMIC_POLICY
        ),
        "hard_spread_gate_then_volatility_rank_verdict": (
            HARD_SPREAD_GATE_THEN_VOLATILITY_RANK_VERDICT
        ),
        "lexicographic_spread_then_vol_verdict": LEXICOGRAPHIC_SPREAD_THEN_VOL_VERDICT,
        "multiplicative_opportunity_x_tradability_verdict": (
            MULTIPLICATIVE_OPPORTUNITY_X_TRADABILITY_VERDICT
        ),
        "negative_status_quo_baseline": NEGATIVE_STATUS_QUO_BASELINE,
        "no_offline_policy_class_has_productive_authority": (
            NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY
        ),
        "pareto_diagnostic_use_allowed": PARETO_DIAGNOSTIC_USE_ALLOWED,
        "pareto_vol_and_tradability_verdict": PARETO_VOL_AND_TRADABILITY_VERDICT,
        "recommended_offline_challengers": RECOMMENDED_OFFLINE_CHALLENGERS,
        "recommended_primary_baseline": RECOMMENDED_PRIMARY_BASELINE,
        "volatility_rank_only_verdict": VOLATILITY_RANK_ONLY_VERDICT,
        "volatility_to_spread_ratio_verdict": VOLATILITY_TO_SPREAD_RATIO_VERDICT,
        "weighted_additive_composite_verdict": WEIGHTED_ADDITIVE_COMPOSITE_VERDICT,
    }


def classify_cap22_offline_evidence_contract_v1() -> dict[str, Any]:
    return {
        "additional_raw_input_list": ADDITIONAL_RAW_INPUT_LIST,
        "additional_raw_input_required": ADDITIONAL_RAW_INPUT_REQUIRED,
        "authorized_mvr_inputs": AUTHORIZED_MVR_INPUTS,
        "authorized_volatility_base_grid": AUTHORIZED_VOLATILITY_BASE_GRID,
        "authorized_volatility_warmup": AUTHORIZED_VOLATILITY_WARMUP,
        "current_persisted_cap22_economic_md_available": (
            CURRENT_PERSISTED_CAP22_ECONOMIC_MD_AVAILABLE
        ),
        "deferred_features": DEFERRED_FEATURES,
        "deterministic_replay_required": DETERMINISTIC_REPLAY_REQUIRED,
        "forward_label_horizon_ratified": FORWARD_LABEL_HORIZON_RATIFIED,
        "forward_label_window_strictly_after_feature_time": (
            FORWARD_LABEL_WINDOW_STRICTLY_AFTER_FEATURE_TIME
        ),
        "friction_sensitivity_required": FRICTION_SENSITIVITY_REQUIRED,
        "historical_replay_horizon_ratified": HISTORICAL_REPLAY_HORIZON_RATIFIED,
        "identical_candidate_universe_per_policy_comparison": (
            IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_COMPARISON
        ),
        "missing_or_invalid_input_semantics": MISSING_OR_INVALID_INPUT_SEMANTICS,
        "missing_stale_input_stress_required": MISSING_STALE_INPUT_STRESS_REQUIRED,
        "mvr_data_sufficient_for_policy_comparison": (MVR_DATA_SUFFICIENT_FOR_POLICY_COMPARISON),
        "new_listing_warmup_test_required": NEW_LISTING_WARMUP_TEST_REQUIRED,
        "no_implicit_imputation_ratified": NO_IMPLICIT_IMPUTATION_RATIFIED,
        "no_lookahead_required": NO_LOOKAHEAD_REQUIRED,
        "per_instrument_required_raw_inputs": PER_INSTRUMENT_REQUIRED_RAW_INPUTS,
        "pit_replay_required": PIT_REPLAY_REQUIRED,
        "rank_stability_test_required": RANK_STABILITY_TEST_REQUIRED,
        "ranking_cadence_ratified": RANKING_CADENCE_RATIFIED,
        "ranking_objective_is_not_downstream_pnl": (RANKING_OBJECTIVE_IS_NOT_DOWNSTREAM_PNL),
        "ranking_objective_metrics": RANKING_OBJECTIVE_METRICS,
        "robustness_stress_cases_required": ROBUSTNESS_STRESS_CASES_REQUIRED,
        "secondary_strategy_metrics": SECONDARY_STRATEGY_METRICS,
        "spread_derived_value_alone_is_insufficient": (SPREAD_DERIVED_VALUE_ALONE_IS_INSUFFICIENT),
        "spread_raw_quotes_must_be_persisted": SPREAD_RAW_QUOTES_MUST_BE_PERSISTED,
        "top20_turnover_test_required": TOP20_TURNOVER_TEST_REQUIRED,
        "volatility_lookback_variant_is_new_feature_semantics": (
            VOLATILITY_LOOKBACK_VARIANT_IS_NEW_FEATURE_SEMANTICS
        ),
        "walk_forward_required": WALK_FORWARD_REQUIRED,
    }


def classify_preserved_program_invariants_v1() -> dict[str, Any]:
    return {
        "cap21_boundary_preserved": CAP21_BOUNDARY_PRESERVED,
        "cap21_economic_md_authority_added": CAP21_ECONOMIC_MD_AUTHORITY_ADDED,
        "cap21_ranking_authority_added": CAP21_RANKING_AUTHORITY_ADDED,
        "cap22_direct_live_venue_dependency": CAP22_DIRECT_LIVE_VENUE_DEPENDENCY,
        "cap22_productive_economic_runtime_wired": (CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED),
        "cap22_remains_ranking_owner": CAP22_REMAINS_RANKING_OWNER,
        "collection_skew_numeric_bound_ratified": (COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED),
        "cross_sectional_normalization_ratified": (CROSS_SECTIONAL_NORMALIZATION_RATIFIED),
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
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_runtime_implementation_allowed": (PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED),
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "policy_a_role": POLICY_A_ROLE,
        "productive_mf_host_join": PRODUCTIVE_MF_HOST_JOIN,
        "productive_selection_owner": PRODUCTIVE_SELECTION_OWNER,
        "rotation_policy_status": ROTATION_POLICY_STATUS,
        "runtime_authority_granted": RUNTIME_AUTHORITY_GRANTED,
        "second_selection_decision_downstream": SECOND_SELECTION_DECISION_DOWNSTREAM,
        "spread_aggregator_ratified": SPREAD_AGGREGATOR_RATIFIED,
        "spread_formula_ratified": SPREAD_FORMULA_RATIFIED,
        "stale_seconds_ratified": STALE_SECONDS_RATIFIED,
    }


def validate_cap22_offline_policy_candidates_and_evidence_declaration_v1(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw = _require_mapping(payload)
    _require_false_flags(raw)
    _require_true_flags(raw)
    if raw.get("recommended_primary_baseline") not in (
        None,
        RECOMMENDED_PRIMARY_BASELINE,
    ):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError("PRIMARY_BASELINE_MISMATCH")
    if raw.get("recommended_offline_challengers") not in (
        None,
        RECOMMENDED_OFFLINE_CHALLENGERS,
        list(RECOMMENDED_OFFLINE_CHALLENGERS),
    ):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError("CHALLENGER_SET_MISMATCH")
    if raw.get("volatility_rank_only_verdict") not in (
        None,
        VOLATILITY_RANK_ONLY_VERDICT,
    ):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError("VOL_ONLY_MUST_REMAIN_BASELINE_ONLY")
    if raw.get("pareto_vol_and_tradability_verdict") not in (
        None,
        PARETO_VOL_AND_TRADABILITY_VERDICT,
    ):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError(
            "PARETO_MUST_REMAIN_REJECT_AS_TOP20_POLICY"
        )
    if raw.get("additional_raw_input_list") not in (None, ADDITIONAL_RAW_INPUT_LIST):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError("ADDITIONAL_RAW_INPUT_MUST_REMAIN_NONE")
    if raw.get("pdf_step_5_status") not in (None, PDF_STEP_5_STATUS):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError("PDF_STEP_5_MUST_REMAIN_UNRESOLVED")
    if raw.get("rotation_policy_status") not in (None, ROTATION_POLICY_STATUS):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError("ROTATION_MUST_REMAIN_FAIL_CLOSED")
    if raw.get("pdf_step_7_status") not in (None, PDF_STEP_7_STATUS):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError("PDF_STEP_7_MUST_REMAIN_FORBIDDEN")
    if raw.get("productive_selection_owner") not in (
        None,
        PRODUCTIVE_SELECTION_OWNER,
    ):
        raise Cap22OfflinePolicyCandidatesAndEvidenceError(
            "CAP23_REMAINS_PRODUCTIVE_SELECTION_OWNER"
        )
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "contract_id": CONTRACT_ID,
        "recommended_offline_challengers": RECOMMENDED_OFFLINE_CHALLENGERS,
        "recommended_primary_baseline": RECOMMENDED_PRIMARY_BASELINE,
        "schema_version": SCHEMA_VERSION,
        "valid": True,
    }
