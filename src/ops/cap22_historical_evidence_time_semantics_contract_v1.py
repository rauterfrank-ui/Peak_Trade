"""Cap 2.2 historical evidence time semantics contract V1.

Persists the Owner-ratified offline historical ranking cadence,
forward-label horizons, walk-forward modes, and replay-horizon floor.
Does not run historical collection, does not run walk-forward, does
not wire productive economic ranking, does not close PDF Step 5, and
does not grant runtime authority.
"""

from __future__ import annotations

from typing import Any, Mapping

CONTRACT_ID = "CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1"
DECISION_ID = "CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1"
SCHEMA_VERSION = "cap22_historical_evidence_time_semantics.v1"
OWNER_GO_THIS_SLICE = "PEAK_TRADE_CAP22_HISTORICAL_EVIDENCE_TIME_SEMANTICS_V1"
BOUND_ORIGIN_MAIN_SHA = "d8cbee19cf8318eca0ac23febc61289b4272aaff"
AUTHORITY_EFFECT = "OFFLINE_HISTORICAL_EVIDENCE_TIME_SEMANTICS_ONLY"
AUTHORITY_SCOPE = "OFFLINE_HISTORICAL_EVIDENCE_ONLY"
PRODUCTIVE_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"

RANKING_CADENCE_RATIFIED = True
RANKING_CADENCE_ID = "PT1M_15_MINUTE_ANCHORS_V1"
CAP22_OFFLINE_HISTORICAL_RANKING_CADENCE = "PT1M_15_MINUTE_ANCHORS_V1"
ANCHOR_GRID = "UTC_MINUTE_MOD_15_EQUALS_0"
ANCHOR_MINUTE_MODULUS = 15
PIT_AVAILABLE_OR_FINALIZED_AT_ANCHOR_ONLY = True
NO_FUTURE_DATA = True
NO_INTRABAR_RECOMPUTE_BETWEEN_ANCHORS = True
PRODUCTIVE_RUNTIME_CADENCE_AUTHORIZED = False

FORWARD_LABEL_HORIZON_RATIFIED = True
FORWARD_LABEL_HORIZON_SET_ID = "CAP22_MVR_FORWARD_LABEL_HORIZONS_V1"
FORWARD_LABEL_HORIZON_MINUTES: tuple[int, ...] = (15, 30, 60, 120)
FORWARD_LABEL_HORIZONS: tuple[str, ...] = ("15m", "30m", "60m", "120m")
FORWARD_LABEL_WINDOW_STRICTLY_AFTER_FEATURE_TIME = True
FEATURE_BAR_MUST_NOT_ENTER_FORWARD_WINDOW = True
LABELS_ARE_EVALUATION_HORIZONS_NOT_HOLD_DURATION = True

FORWARD_ABS_RETURN_DEFINITION_RATIFIED = True
FORWARD_ABS_RETURN_ID = "ABS_LOG_FUTURE_OVER_ANCHOR"
ANCHOR_PRICE = "LAST_FINALIZED_PT1M_MARK_PRICE_AT_OR_AS_OF_ANCHOR_PIT"
FUTURE_PRICE = "FINALIZED_PT1M_MARK_PRICE_AT_HORIZON_END"

FORWARD_REALIZED_VOL_DEFINITION_RATIFIED = True
FORWARD_REALIZED_VOL_INPUT = "FINALIZED_PT1M_MARKS_STRICTLY_AFTER_ANCHOR_THROUGH_HORIZON_END"
FORWARD_REALIZED_VOL_ESTIMATOR = "POPULATION_SIGMA_DDOF_0"
FORWARD_REALIZED_VOL_DDOF = 0
FEATURE_RETURN_WINDOW_OVERLAP_FORBIDDEN = True

FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED = False
FRICTION_ADJUSTED_OPPORTUNITY_METRIC_STATUS = "BLOCKED_UNTIL_SEPARATE_OWNER_GO"

WALK_FORWARD_REQUIRED = True
WALK_FORWARD_PRIMARY_MODE = "ALL_VALID_15M_ANCHORS"
WALK_FORWARD_ROBUSTNESS_MODE = "NON_OVERLAPPING_BY_HORIZON"
OVERLAPPING_FORWARD_LABEL_WINDOWS_ALLOWED_IN_PRIMARY = True
NON_OVERLAPPING_ROBUSTNESS_VIEW_REQUIRED = True
NO_FUTURE_WINDOW_DATA_IN_FEATURE_COMPUTATION = True

HISTORICAL_REPLAY_HORIZON_RATIFIED = True
HISTORICAL_REPLAY_HORIZON_MODE = "MINIMUM_COVERAGE_PLUS_AVAILABLE_HISTORY"
HISTORICAL_REPLAY_HORIZON_ID = "MIN_90D_PLUS_AVAILABLE_VALID_HISTORY_V1"
MINIMUM_HISTORICAL_COVERAGE_DAYS = 90
STRONGER_CANONICAL_MINIMUM_COVERAGE_DAYS_FOUND = False
USE_ALL_AVAILABLE_VALID_LONGER_HISTORY = True
TIME_SEGMENT_REPORTING_REQUIRED = True
CHERRY_PICKING_FAVORABLE_WINDOW_FORBIDDEN = True
NO_SINGLE_SHORT_WINDOW_RATIFIED_AS_TRUTH = True

CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_AT_T_REQUIRED = True
NO_TODAY_UNIVERSE_MEMBERSHIP_RETROACTIVE = True
IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_REQUIRED = True

NEW_LISTING_WARMUP_FAIL_CLOSED = True
NEW_LISTING_WITHOUT_WARMUP = "NOT_RANKABLE_AT_T"
MINIMUM_VOLATILITY_WARMUP = "61_PT1M_MARKS_60_LOG_RETURNS"
NO_IMPLICIT_FILL = True
FINALIZED_ONLY = True
FUTURE_LEAKAGE_FORBIDDEN = True
NO_RETROACTIVE_FILL = True

STALE_SECONDS_RATIFIED = False
COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED = False
HISTORICAL_EVIDENCE_MAY_USE_ONLY_VALID_PERSISTED_SNAPSHOTS = True

AUTHORITATIVE_POLICY_B_THRESHOLD_SCALE_FOUND = False
POLICY_B_THRESHOLD_SET_RATIFIED = False
POLICY_B_SINGLE_THRESHOLD_RATIFIED = False
INJECTED_TEST_ONLY_THRESHOLD_SETS_MAY_BE_EVALUATED_LATER = True
INJECTED_THRESHOLD_EVALUATION_DOES_NOT_RATIFY_THRESHOLD = True

FINAL_SCORE_FORMULA_RATIFIED = False
FINAL_WEIGHTS_RATIFIED = False
CROSS_SECTIONAL_NORMALIZATION_RATIFIED = False
NEAR_ZERO_THRESHOLD_RATIFIED = False
POLICY_RATIFICATION_JUSTIFIED = False
NO_CHALLENGER_WINS_BY_THIS_SLICE = True
NO_OFFLINE_POLICY_CLASS_HAS_PRODUCTIVE_AUTHORITY = True
SPEARMAN_RANK_ASSOCIATION_FORMULA_RATIFIED = False
HISTORICAL_EVIDENCE_GENERATED = False

CAP21_BOUNDARY_PRESERVED = True
CAP21_RANKING_AUTHORITY_ADDED = False
CAP21_ECONOMIC_MD_AUTHORITY_ADDED = False
CAP22_REMAINS_RANKING_OWNER = True
CAP22_DIRECT_LIVE_VENUE_DEPENDENCY = False
DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK = True
SECOND_SELECTION_DECISION_DOWNSTREAM = False
ANTI_CHURN_POLICY_A_UNCHANGED = True
POLICY_A_ROLE = "ANTI_CHURN_ADMISSION_ONLY"

ECONOMIC_MD_PRODUCER_IMPLEMENTED = True
ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED = False
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED = False
ECONOMIC_RANK_ACTIVATED = False
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
    "friction_adjusted_opportunity_formula_ratified",
    "historical_evidence_generated",
    "multi_future_runtime_authorized",
    "near_zero_threshold_ratified",
    "pdf_step_7_runtime_implementation_allowed",
    "policy_b_single_threshold_ratified",
    "policy_b_threshold_set_ratified",
    "policy_ratification_justified",
    "productive_mf_host_join",
    "productive_runtime_cadence_authorized",
    "runtime_authority_granted",
    "second_selection_decision_downstream",
    "stale_seconds_ratified",
)

TRUE_REQUIRED_FLAGS: tuple[str, ...] = (
    "anti_churn_policy_a_unchanged",
    "cap21_boundary_preserved",
    "cap21_governed_futures_universe_snapshot_at_t_required",
    "cap22_remains_ranking_owner",
    "downstream_execution_must_not_re_rank",
    "forward_abs_return_definition_ratified",
    "forward_label_horizon_ratified",
    "forward_label_window_strictly_after_feature_time",
    "forward_realized_vol_definition_ratified",
    "historical_replay_horizon_ratified",
    "identical_candidate_universe_per_policy_required",
    "new_listing_warmup_fail_closed",
    "no_challenger_wins_by_this_slice",
    "no_offline_policy_class_has_productive_authority",
    "ranking_cadence_ratified",
    "walk_forward_required",
)


class Cap22HistoricalEvidenceTimeSemanticsError(ValueError):
    """Fail-closed Cap 2.2 historical evidence time-semantics error."""


def is_valid_pt1m_15m_anchor_utc(*, minute: int, second: int = 0, microsecond: int = 0) -> bool:
    """Return True when the UTC clock lies on a 15-minute PT1M anchor."""
    if not isinstance(minute, int) or minute < 0 or minute > 59:
        return False
    if second != 0 or microsecond != 0:
        return False
    return minute % ANCHOR_MINUTE_MODULUS == 0


def non_overlapping_anchor_stride_for_horizon_minutes(horizon_minutes: int) -> int:
    """Return the robustness-view stride for a ratified forward horizon."""
    if horizon_minutes not in FORWARD_LABEL_HORIZON_MINUTES:
        raise Cap22HistoricalEvidenceTimeSemanticsError("UNRATIFIED_FORWARD_LABEL_HORIZON")
    stride, remainder = divmod(horizon_minutes, ANCHOR_MINUTE_MODULUS)
    if remainder != 0 or stride < 1:
        raise Cap22HistoricalEvidenceTimeSemanticsError("HORIZON_NOT_ALIGNED_TO_ANCHOR_GRID")
    return stride


def _require_mapping(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise Cap22HistoricalEvidenceTimeSemanticsError("TIME_SEMANTICS_DECLARATION_NOT_A_MAPPING")
    return payload


def _require_false_flags(raw: Mapping[str, Any]) -> None:
    for key in FALSE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not False:
            raise Cap22HistoricalEvidenceTimeSemanticsError(
                "TIME_SEMANTICS_FALSE_FLAG_VIOLATION", key
            )


def _require_true_flags(raw: Mapping[str, Any]) -> None:
    for key in TRUE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not True:
            raise Cap22HistoricalEvidenceTimeSemanticsError(
                "TIME_SEMANTICS_TRUE_FLAG_VIOLATION", key
            )


def classify_cap22_historical_evidence_time_semantics_v1() -> dict[str, Any]:
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "authority_scope": AUTHORITY_SCOPE,
        "cap21_governed_futures_universe_snapshot_at_t_required": (
            CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_AT_T_REQUIRED
        ),
        "forward_abs_return_definition_ratified": FORWARD_ABS_RETURN_DEFINITION_RATIFIED,
        "forward_label_horizon_ratified": FORWARD_LABEL_HORIZON_RATIFIED,
        "forward_label_horizon_set_id": FORWARD_LABEL_HORIZON_SET_ID,
        "forward_label_horizons": list(FORWARD_LABEL_HORIZONS),
        "forward_realized_vol_definition_ratified": FORWARD_REALIZED_VOL_DEFINITION_RATIFIED,
        "friction_adjusted_opportunity_formula_ratified": (
            FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED
        ),
        "historical_replay_horizon_id": HISTORICAL_REPLAY_HORIZON_ID,
        "historical_replay_horizon_ratified": HISTORICAL_REPLAY_HORIZON_RATIFIED,
        "identical_candidate_universe_per_policy_required": (
            IDENTICAL_CANDIDATE_UNIVERSE_PER_POLICY_REQUIRED
        ),
        "minimum_historical_coverage_days": MINIMUM_HISTORICAL_COVERAGE_DAYS,
        "new_listing_warmup_fail_closed": NEW_LISTING_WARMUP_FAIL_CLOSED,
        "ranking_cadence_id": RANKING_CADENCE_ID,
        "ranking_cadence_ratified": RANKING_CADENCE_RATIFIED,
        "walk_forward_primary_mode": WALK_FORWARD_PRIMARY_MODE,
        "walk_forward_robustness_mode": WALK_FORWARD_ROBUSTNESS_MODE,
    }


def classify_preserved_program_invariants_v1() -> dict[str, Any]:
    return {
        "economic_md_producer_productively_scheduled": (
            ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED
        ),
        "economic_rank_activated": ECONOMIC_RANK_ACTIVATED,
        "friction_adjusted_opportunity_formula_ratified": (
            FRICTION_ADJUSTED_OPPORTUNITY_FORMULA_RATIFIED
        ),
        "historical_evidence_generated": HISTORICAL_EVIDENCE_GENERATED,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "next_cap22_dependency": NEXT_CAP22_DEPENDENCY,
        "pdf_step_5_status": PDF_STEP_5_STATUS,
        "pdf_step_7_status": PDF_STEP_7_STATUS,
        "policy_b_threshold_set_ratified": POLICY_B_THRESHOLD_SET_RATIFIED,
        "policy_ratification_justified": POLICY_RATIFICATION_JUSTIFIED,
        "productive_runtime_cadence_authorized": PRODUCTIVE_RUNTIME_CADENCE_AUTHORIZED,
        "runtime_authority_granted": RUNTIME_AUTHORITY_GRANTED,
    }


def validate_cap22_historical_evidence_time_semantics_declaration_v1(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw = _require_mapping(payload)
    _require_false_flags(raw)
    _require_true_flags(raw)
    if raw.get("ranking_cadence_id") not in (None, RANKING_CADENCE_ID):
        raise Cap22HistoricalEvidenceTimeSemanticsError("RANKING_CADENCE_ID_MISMATCH")
    if raw.get("forward_label_horizon_set_id") not in (None, FORWARD_LABEL_HORIZON_SET_ID):
        raise Cap22HistoricalEvidenceTimeSemanticsError("FORWARD_LABEL_HORIZON_SET_ID_MISMATCH")
    if raw.get("historical_replay_horizon_id") not in (None, HISTORICAL_REPLAY_HORIZON_ID):
        raise Cap22HistoricalEvidenceTimeSemanticsError("HISTORICAL_REPLAY_HORIZON_ID_MISMATCH")
    if raw.get("walk_forward_primary_mode") not in (None, WALK_FORWARD_PRIMARY_MODE):
        raise Cap22HistoricalEvidenceTimeSemanticsError("WALK_FORWARD_PRIMARY_MODE_MISMATCH")
    if raw.get("walk_forward_robustness_mode") not in (None, WALK_FORWARD_ROBUSTNESS_MODE):
        raise Cap22HistoricalEvidenceTimeSemanticsError("WALK_FORWARD_ROBUSTNESS_MODE_MISMATCH")
    if raw.get("minimum_historical_coverage_days") not in (
        None,
        MINIMUM_HISTORICAL_COVERAGE_DAYS,
    ):
        raise Cap22HistoricalEvidenceTimeSemanticsError("MINIMUM_HISTORICAL_COVERAGE_DAYS_MISMATCH")
    if raw.get("pdf_step_5_status") not in (None, PDF_STEP_5_STATUS):
        raise Cap22HistoricalEvidenceTimeSemanticsError("PDF_STEP_5_MUST_REMAIN_UNRESOLVED")
    if raw.get("pdf_step_7_status") not in (None, PDF_STEP_7_STATUS):
        raise Cap22HistoricalEvidenceTimeSemanticsError("PDF_STEP_7_MUST_REMAIN_FORBIDDEN")
    if raw.get("rotation_policy_status") not in (None, ROTATION_POLICY_STATUS):
        raise Cap22HistoricalEvidenceTimeSemanticsError("ROTATION_MUST_REMAIN_FAIL_CLOSED")
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "contract_id": CONTRACT_ID,
        "ranking_cadence_id": RANKING_CADENCE_ID,
        "schema_version": SCHEMA_VERSION,
        "valid": True,
    }
