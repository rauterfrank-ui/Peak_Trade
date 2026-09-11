"""Cap 2.2 economic-MD dual-input architecture contract V1.

Persists the Owner-ratified architecture decision that a separate persisted
multi-instrument Economic Market Data Input Capability is the future input
owner, and that Cap 2.2 may later consume two authoritative inputs with
separate roles. Does not implement that producer, does not wire productive
economic ranking, does not ratify score formula or weights, does not close
PDF Step 5, does not authorize rotation apply, does not allow PDF Step 7,
and does not grant multi-future runtime authority.
"""

from __future__ import annotations

from typing import Any, Mapping

CONTRACT_ID = "CAP22_ECONOMIC_MD_INPUT_AND_DUAL_INPUT_CONTRACT_V1"
SCHEMA_VERSION = "cap22_economic_md_dual_input.v1"
OWNER_GO_THIS_SLICE = (
    "PEAK_TRADE_CAP_2_2_SEPARATE_ECONOMIC_MD_INPUT_CAPABILITY_AND_DUAL_INPUT_CONTRACT_SPEC_ONLY_V1"
)
BOUND_ORIGIN_MAIN_SHA = "8b7369f5f25466c0d57893cbac141382d7b6ec18"
CAPABILITY_ID_CAP22 = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
CAPABILITY_ID_CAP21 = "CAPABILITY_2_1_GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1"
CAPABILITY_ID_ECONOMIC_MD = "CAPABILITY_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_V1"
PRODUCTIVE_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"
AUTHORITATIVE_ACTIVE_SET_OWNER = "ops.mf_membership_rotation_controller_v1"

CAP22_ECONOMIC_MD_ARCHITECTURE_DECISION = (
    "AUTHORIZE_SEPARATE_PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MD_INPUT_CAPABILITY"
)
CAP22_INPUT_MODEL = "DUAL_AUTHORITATIVE_INPUTS_WITH_SEPARATE_ROLES"
CAP22_INPUT_1 = "CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT"
CAP22_INPUT_1_ROLE = "STRUCTURAL_AND_SAFETY_ELIGIBILITY_ONLY"
CAP22_INPUT_2 = "PERSISTED_MULTI_INSTRUMENT_ECONOMIC_MARKET_INPUT_SNAPSHOT"
CAP22_INPUT_2_ROLE = "ECONOMIC_RANKING_FEATURE_INPUT_ONLY"

CAP21_BOUNDARY_PRESERVED = True
CAP21_RANKING_AUTHORITY_ADDED = False
CAP21_ECONOMIC_MD_AUTHORITY_ADDED = False
CAP_2_1_ROLE = "STRUCTURAL_AND_SAFETY_ELIGIBILITY_ONLY"

CAP22_REMAINS_RANKING_OWNER = True
CAP22_BECOMES_NETWORK_OWNER = False
CAP22_DIRECT_LIVE_VENUE_DEPENDENCY = False
CAP22_CURRENT_PRODUCTIVE_INPUT = "CAP21_GOVERNED_FUTURES_UNIVERSE_SNAPSHOT_ONLY"
CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED = False

ECONOMIC_MD_INPUT_CAPABILITY_AUTHORIZED = True
ECONOMIC_MD_DATA_OWNER = "SEPARATE_ECONOMIC_MD_INPUT_PRODUCER"
ECONOMIC_MD_NETWORK_IO_OWNER = "SEPARATE_ECONOMIC_MD_INPUT_PRODUCER"
ECONOMIC_MD_PERSISTENCE_OWNER = "SEPARATE_ECONOMIC_MD_INPUT_PRODUCER"
ECONOMIC_MD_SCHEMA_OWNER = "SEPARATE_ECONOMIC_MD_INPUT_PRODUCER"
ECONOMIC_MD_PRODUCER_IMPLEMENTED = False
REPLAY_FROM_PERSISTED_INPUT_REQUIRED = True

LIBRARY_REUSE_AUTHORITY_TRANSFER = False
CMC_AUTHORITY_TRANSFERRED = False
SELECTED_FUTURE_MD_AUTHORITY_TRANSFERRED = False
CAP52_AUTHORITY_TRANSFERRED = False
DASHBOARD_AUTHORITY_TRANSFERRED = False
RESEARCH_AUTHORITY_TRANSFERRED = False
CANARY_AUTHORITY_TRANSFERRED = False
CAP21_AUTHORITY_TRANSFERRED_TO_ECONOMIC_MD = False
CAN_REUSE_CANONICAL_VOLATILITY_FORMULA = True
CAP22_MVR_VOLATILITY_SEMANTICS_REFERENCE = "CANONICAL_VOLATILITY_ESTIMATE_CONTRACT"

CAP22_MVR_VOLATILITY_INPUT_AUTHORIZED = True
CAP22_MVR_VOLATILITY_RAW_INPUT = "FINALIZED_PT1M_MARK_PRICE_HISTORY"
MINIMUM_VOLATILITY_WARMUP = "61_PT1M_MARKS_60_LOG_RETURNS"
NO_IMPLICIT_FILL = True
FINALIZED_ONLY = True
FUTURE_LEAKAGE_FORBIDDEN = True

CAP22_MVR_SPREAD_INPUT_AUTHORIZED = True
CAP22_MVR_SPREAD_RAW_INPUT = "SAME_COLLECTION_CYCLE_BIDPX_ASKPX"
SPREAD_MUST_BE_DERIVABLE_FROM_PERSISTED_RAW_INPUT = True
SPREAD_FORMULA_RATIFIED = False
SPREAD_AGGREGATOR_RATIFIED = False
SPREAD_STALE_SECONDS_RATIFIED = False
SPREAD_MAX_COLLECTION_SKEW_RATIFIED = False
STALE_SECONDS_RATIFIED = False
COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED = False

CAP_2_2_TARGET_RANK_MEANING = "TRADABLE_ECONOMIC_OPPORTUNITY_FOR_PEAK_TRADE"
TARGET_SEMANTICS_STATUS = "ARCHITECTURALLY_ADMISSIBLE_NOT_EMPIRICALLY_PROVEN"
STRUCTURAL_ELIGIBILITY_IS_NOT_ECONOMIC_SCORE = True
POLICY_A_MAY_RECOMPUTE_ECONOMIC_SCORE = False
ACTIVE_SET_MAY_RECOMPUTE_ECONOMIC_SCORE = False
EXECUTION_MAY_RECOMPUTE_ECONOMIC_SCORE = False
EXECUTION_MAY_RERANK = False
DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK = True
SECOND_SELECTION_DECISION_DOWNSTREAM = False

FINAL_SCORE_FORMULA_RATIFIED = False
FINAL_WEIGHTS_RATIFIED = False
CROSS_SECTIONAL_NORMALIZATION_RATIFIED = False
ECONOMIC_RANK_ACTIVATED = False

RAW_CONTRACT_VOLUME_MVR_VERDICT = "DEFER"
TURNOVER_MVR_VERDICT = "DEFER"
OPEN_INTEREST_MVR_VERDICT = "DEFER"
FUNDING_MVR_VERDICT = "DEFER"
ORDERBOOK_DEPTH_MVR_VERDICT = "DEFER"
PRICE_IMPACT_MVR_VERDICT = "DEFER"
MOMENTUM_MVR_VERDICT = "DEFER"
TREND_MVR_VERDICT = "DEFER"
ATR_MVR_VERDICT = "DEFER"
LISTING_AGE_MVR_VERDICT = "DEFER"
FEES_MVR_VERDICT = "DEFER"
STATIC_SLIPPAGE_MVR_VERDICT = "DEFER"

POLICY_A_ROLE = "ANTI_CHURN_ADMISSION_ONLY"
RUNTIME_AUTHORITY_GRANTED = False
PRODUCTIVE_MF_HOST_JOIN = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION = "UNRESOLVED"
PDF_STEP_5_STATUS = "UNRESOLVED"
ROTATION_POLICY_STATUS = "FAIL_CLOSED_UNTIL_PDF_STEP_5"
APPLY_ROTATION_STATUS = "FAIL_CLOSED"
PDF_STEP_7_STATUS = "FORBIDDEN"
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED = False
AS05_D01_STATUS = "CLOSED"
AS05_D02_STATUS = "CLOSED"
AS05_D03_STATUS = "CLOSED"
NEXT_CANONICAL_DECISION = "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION"

FALSE_REQUIRED_FLAGS: tuple[str, ...] = (
    "active_set_may_recompute_economic_score",
    "cap21_economic_md_authority_added",
    "cap21_ranking_authority_added",
    "cap22_becomes_network_owner",
    "cap22_direct_live_venue_dependency",
    "cap22_productive_economic_runtime_wired",
    "cmc_authority_transferred",
    "collection_skew_numeric_bound_ratified",
    "cross_sectional_normalization_ratified",
    "economic_md_producer_implemented",
    "economic_rank_activated",
    "execution_may_recompute_economic_score",
    "execution_may_rerank",
    "final_score_formula_ratified",
    "final_weights_ratified",
    "library_reuse_authority_transfer",
    "multi_future_runtime_authorized",
    "pdf_step_7_runtime_implementation_allowed",
    "policy_a_may_recompute_economic_score",
    "productive_mf_host_join",
    "runtime_authority_granted",
    "second_selection_decision_downstream",
    "spread_aggregator_ratified",
    "spread_formula_ratified",
    "stale_seconds_ratified",
)

TRUE_REQUIRED_FLAGS: tuple[str, ...] = (
    "cap21_boundary_preserved",
    "cap22_mvr_spread_input_authorized",
    "cap22_mvr_volatility_input_authorized",
    "cap22_remains_ranking_owner",
    "can_reuse_canonical_volatility_formula",
    "downstream_execution_must_not_re_rank",
    "economic_md_input_capability_authorized",
    "finalized_only",
    "future_leakage_forbidden",
    "no_implicit_fill",
    "replay_from_persisted_input_required",
    "spread_must_be_derivable_from_persisted_raw_input",
    "structural_eligibility_is_not_economic_score",
)


class Cap22EconomicMdDualInputError(ValueError):
    """Fail-closed dual-input architecture contract error."""


def _require_mapping(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(payload, Mapping):
        raise Cap22EconomicMdDualInputError("DUAL_INPUT_DECLARATION_NOT_A_MAPPING")
    return payload


def _require_false_flags(raw: Mapping[str, Any]) -> None:
    for key in FALSE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not False:
            raise Cap22EconomicMdDualInputError("DUAL_INPUT_FALSE_FLAG_VIOLATION", key)


def _require_true_flags(raw: Mapping[str, Any]) -> None:
    for key in TRUE_REQUIRED_FLAGS:
        if key not in raw:
            continue
        if raw[key] is not True:
            raise Cap22EconomicMdDualInputError("DUAL_INPUT_TRUE_FLAG_VIOLATION", key)


def classify_cap22_dual_input_architecture_v1() -> dict[str, Any]:
    return {
        "architecture_decision": CAP22_ECONOMIC_MD_ARCHITECTURE_DECISION,
        "cap21_boundary_preserved": CAP21_BOUNDARY_PRESERVED,
        "cap21_economic_md_authority_added": CAP21_ECONOMIC_MD_AUTHORITY_ADDED,
        "cap21_ranking_authority_added": CAP21_RANKING_AUTHORITY_ADDED,
        "cap22_becomes_network_owner": CAP22_BECOMES_NETWORK_OWNER,
        "cap22_current_productive_input": CAP22_CURRENT_PRODUCTIVE_INPUT,
        "cap22_direct_live_venue_dependency": CAP22_DIRECT_LIVE_VENUE_DEPENDENCY,
        "cap22_input_1": CAP22_INPUT_1,
        "cap22_input_1_role": CAP22_INPUT_1_ROLE,
        "cap22_input_2": CAP22_INPUT_2,
        "cap22_input_2_role": CAP22_INPUT_2_ROLE,
        "cap22_input_model": CAP22_INPUT_MODEL,
        "cap22_productive_economic_runtime_wired": CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
        "cap22_remains_ranking_owner": CAP22_REMAINS_RANKING_OWNER,
        "contract_id": CONTRACT_ID,
        "economic_md_data_owner": ECONOMIC_MD_DATA_OWNER,
        "economic_md_input_capability_authorized": ECONOMIC_MD_INPUT_CAPABILITY_AUTHORIZED,
        "economic_md_network_io_owner": ECONOMIC_MD_NETWORK_IO_OWNER,
        "economic_md_persistence_owner": ECONOMIC_MD_PERSISTENCE_OWNER,
        "economic_md_producer_implemented": ECONOMIC_MD_PRODUCER_IMPLEMENTED,
        "economic_md_schema_owner": ECONOMIC_MD_SCHEMA_OWNER,
        "productive_selection_owner": PRODUCTIVE_SELECTION_OWNER,
        "schema_version": SCHEMA_VERSION,
    }


def classify_cap22_mvr_input_scope_v1() -> dict[str, Any]:
    return {
        "can_reuse_canonical_volatility_formula": CAN_REUSE_CANONICAL_VOLATILITY_FORMULA,
        "collection_skew_numeric_bound_ratified": COLLECTION_SKEW_NUMERIC_BOUND_RATIFIED,
        "cross_sectional_normalization_ratified": CROSS_SECTIONAL_NORMALIZATION_RATIFIED,
        "final_score_formula_ratified": FINAL_SCORE_FORMULA_RATIFIED,
        "final_weights_ratified": FINAL_WEIGHTS_RATIFIED,
        "finalized_only": FINALIZED_ONLY,
        "future_leakage_forbidden": FUTURE_LEAKAGE_FORBIDDEN,
        "library_reuse_authority_transfer": LIBRARY_REUSE_AUTHORITY_TRANSFER,
        "minimum_volatility_warmup": MINIMUM_VOLATILITY_WARMUP,
        "no_implicit_fill": NO_IMPLICIT_FILL,
        "spread_aggregator_ratified": SPREAD_AGGREGATOR_RATIFIED,
        "spread_formula_ratified": SPREAD_FORMULA_RATIFIED,
        "spread_must_be_derivable_from_persisted_raw_input": (
            SPREAD_MUST_BE_DERIVABLE_FROM_PERSISTED_RAW_INPUT
        ),
        "spread_raw_input": CAP22_MVR_SPREAD_RAW_INPUT,
        "stale_seconds_ratified": STALE_SECONDS_RATIFIED,
        "volatility_raw_input": CAP22_MVR_VOLATILITY_RAW_INPUT,
        "volatility_semantics_reference": CAP22_MVR_VOLATILITY_SEMANTICS_REFERENCE,
    }


def classify_preserved_program_invariants_v1() -> dict[str, Any]:
    return {
        "apply_rotation_status": APPLY_ROTATION_STATUS,
        "as05_d01_status": AS05_D01_STATUS,
        "as05_d02_status": AS05_D02_STATUS,
        "as05_d03_status": AS05_D03_STATUS,
        "authoritative_active_set_owner": AUTHORITATIVE_ACTIVE_SET_OWNER,
        "downstream_execution_must_not_re_rank": DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK,
        "multi_future_runtime_authorized": MULTI_FUTURE_RUNTIME_AUTHORIZED,
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


def validate_cap22_economic_md_dual_input_declaration_v1(
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    raw = _require_mapping(payload)
    _require_false_flags(raw)
    _require_true_flags(raw)
    if raw.get("cap22_input_model") not in (None, CAP22_INPUT_MODEL):
        raise Cap22EconomicMdDualInputError("DUAL_INPUT_MODEL_MISMATCH")
    if raw.get("pdf_step_5_status") not in (None, PDF_STEP_5_STATUS):
        raise Cap22EconomicMdDualInputError("PDF_STEP_5_MUST_REMAIN_UNRESOLVED")
    if raw.get("rotation_policy_status") not in (None, ROTATION_POLICY_STATUS):
        raise Cap22EconomicMdDualInputError("ROTATION_MUST_REMAIN_FAIL_CLOSED")
    if raw.get("pdf_step_7_status") not in (None, PDF_STEP_7_STATUS):
        raise Cap22EconomicMdDualInputError("PDF_STEP_7_MUST_REMAIN_FORBIDDEN")
    if raw.get("economic_md_data_owner") not in (None, ECONOMIC_MD_DATA_OWNER):
        raise Cap22EconomicMdDualInputError("ECONOMIC_MD_OWNER_MISMATCH")
    if raw.get("productive_selection_owner") not in (None, PRODUCTIVE_SELECTION_OWNER):
        raise Cap22EconomicMdDualInputError("CAP23_REMAINS_PRODUCTIVE_SELECTION_OWNER")
    return {
        "architecture_decision": CAP22_ECONOMIC_MD_ARCHITECTURE_DECISION,
        "contract_id": CONTRACT_ID,
        "input_model": CAP22_INPUT_MODEL,
        "schema_version": SCHEMA_VERSION,
        "valid": True,
    }
