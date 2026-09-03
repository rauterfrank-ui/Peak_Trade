"""Independent POS_TO_SZ unit-identity adjudication. No private GET. No POST."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.venue_contract_count_v1 import (
    ONE_CONTRACT_EQUALS_ONE_SUI,
    ORDER_PLAN_QTY_DOMAIN,
    ORDER_PLAN_QTY_UNIT,
    SUI_OPERATIVE_ORDER_SZ,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.captured_payload_v1 import (
    AUTHORIZED_TARGET_ROW,
    captured_envelope_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.constants_v1 import (
    ALLOWED_UNIT_TOKENS,
    CASE_VALUE,
    CONFLICT_COUNT,
    CONVERSION_FORMULA_VALUE,
    CURRENT_UNIT_CONTRACT_VALUE,
    CTVAL_IS_NOT_POS_TO_SZ_FACTOR,
    EARLIEST_MISSING_QTY_UNIT_PROOF,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_PROMOTION_ALIASES,
    HISTORICAL_BTC_DENOMINATION_IS_NOT_CURRENT_SUI_XPERP_TARGET_POSITION_QTY_UNIT,
    HISTORICAL_ORDER_PLAN_VENUE_CONTRACT_COUNT_IS_NOT_CURRENT_TARGET_POSITION_QTY_UNIT,
    IDENTITY_NOW_INDEPENDENTLY_PROVEN,
    IDENTITY_OR_CONVERSION_VALUE,
    IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF,
    IMPLICIT_PASSTHROUGH_PRESENT,
    INSTRUMENT_SCOPE_VALUE,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF,
    ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT,
    P11_DOES_NOT_AUTHORIZE_FLATTEN,
    P11_DOES_NOT_GRANT_EXECUTION_READINESS,
    PLACE_ORDER_REQUEST_PARAM_NAMES_UNIT,
    POS_TO_SZ_UNIT_IDENTITY,
    POS_UNIT_VALUE,
    POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PRIVATE_AUTH_USED,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    QTY_UNIT_CENSUS_COMPLETE,
    QTY_UNIT_LINEAGE_COMPLETE,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    SZ_UNIT_VALUE,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_QTY_NUMERIC,
    TARGET_POSITION_QTY_UNIT,
    THIS_SLICE,
    UNIT_CHAIN_VERDICT_VALUE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.contract_v1 import (
    NUMBER_OF_CONTRACTS,
    venue_semantic_proof_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.lineage_v1 import (
    lineage_census_summary_v1,
    target_position_qty_lineage_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.official_excerpts_v1 import (
    official_excerpt_inventory_v1,
)


class P11PosToSzAdjudicationError(RuntimeError):
    """Fail-closed POS_TO_SZ identity adjudication violation."""


def _reject_alias(value: Any, *, field: str) -> None:
    text = str(value or "").strip()
    if text in ALLOWED_UNIT_TOKENS:
        return
    lowered = text.lower()
    if lowered in {alias.lower() for alias in FORBIDDEN_PROMOTION_ALIASES}:
        raise P11PosToSzAdjudicationError(f"FORBIDDEN_ALIAS_AS_UNIT:{field}:{text}")


def adjudicate_pos_to_sz_unit_identity_v1(
    *,
    origin_main_sha: str,
    claimed_unit: str | None = None,
    positions_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P11PosToSzAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if ONE_CONTRACT_EQUALS_ONE_SUI is not False:
        raise P11PosToSzAdjudicationError("ONE_CONTRACT_EQUALS_ONE_SUI_MUST_REMAIN_FALSE")
    if ORDER_PLAN_QTY_UNIT == TARGET_POSITION_QTY_UNIT:
        raise P11PosToSzAdjudicationError("ORDER_PLAN_ALIAS_COLLAPSED_INTO_TARGET_POSITION_QTY")
    if claimed_unit is not None:
        _reject_alias(claimed_unit, field="TARGET_POSITION_QTY_UNIT")
        if str(claimed_unit).strip() not in ALLOWED_UNIT_TOKENS:
            raise P11PosToSzAdjudicationError("CLAIMED_UNIT_NOT_ALLOWED")

    proof = venue_semantic_proof_v1()
    if proof["CASE"] != "CASE_1_SAME_QUANTITY_DOMAIN":
        raise P11PosToSzAdjudicationError("CASE_NOT_IDENTITY")
    if proof["POS_UNIT"] != NUMBER_OF_CONTRACTS or proof["SZ_UNIT"] != NUMBER_OF_CONTRACTS:
        raise P11PosToSzAdjudicationError("UNIT_MISMATCH")

    envelope = captured_envelope_v1() if positions_payload is None else dict(positions_payload)
    window = adjudicate_prerequisite_08_window_v1(
        positions_payload=envelope,
        instrument_id=TARGET_INSTRUMENT_ID,
    )
    producer_unit = window.get("TARGET_POSITION_QTY_UNIT")
    if producer_unit != "PROVEN":
        raise P11PosToSzAdjudicationError(f"PRODUCER_UNIT_NOT_PROVEN:{producer_unit}")
    if window.get("TARGET_POSITION_QTY_NUMERIC") != "PASS":
        raise P11PosToSzAdjudicationError("QTY_NUMERIC_NOT_PASS")
    if window.get("UNIT_CHAIN_VERDICT") != UNIT_CHAIN_VERDICT_VALUE:
        raise P11PosToSzAdjudicationError("WINDOW_UNIT_CHAIN_VERDICT_DRIFT")
    if window.get("EARLIEST_UNRESOLVED_DEPENDENCY") != EARLIEST_UNRESOLVED_DEPENDENCY:
        raise P11PosToSzAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    if AUTHORIZED_TARGET_ROW.get("pos") != "1":
        raise P11PosToSzAdjudicationError("CAPTURED_POS_DRIFT")
    if "posCcy" in AUTHORIZED_TARGET_ROW:
        raise P11PosToSzAdjudicationError("POSCCY_UNEXPECTEDLY_PRESENT")

    lineage = target_position_qty_lineage_v1()
    census = lineage_census_summary_v1()
    if "pos" not in census["TARGET_POSITION_QTY_PROVEN_UNITS_FOUND"]:
        raise P11PosToSzAdjudicationError("LINEAGE_MISSING_PROVEN_POS")
    if "sz" not in census["TARGET_POSITION_QTY_PROVEN_UNITS_FOUND"]:
        raise P11PosToSzAdjudicationError("LINEAGE_MISSING_PROVEN_SZ")
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise P11PosToSzAdjudicationError("LINEAGE_CENSUS_DRIFT")
    excerpts = official_excerpt_inventory_v1()

    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "TARGET_POSITION_QTY_UNIT": TARGET_POSITION_QTY_UNIT,
        "CURRENT_UNIT_CONTRACT": CURRENT_UNIT_CONTRACT_VALUE,
        "POS_TO_SZ_UNIT_IDENTITY": POS_TO_SZ_UNIT_IDENTITY,
        "POS_UNIT": POS_UNIT_VALUE,
        "SZ_UNIT": SZ_UNIT_VALUE,
        "IDENTITY_OR_CONVERSION": IDENTITY_OR_CONVERSION_VALUE,
        "CONVERSION_FORMULA": CONVERSION_FORMULA_VALUE,
        "INSTRUMENT_SCOPE": INSTRUMENT_SCOPE_VALUE,
        "CASE": CASE_VALUE,
        "QTY_UNIT_CENSUS_COMPLETE": QTY_UNIT_CENSUS_COMPLETE,
        "QTY_UNIT_LINEAGE_COMPLETE": QTY_UNIT_LINEAGE_COMPLETE,
        "EARLIEST_MISSING_QTY_UNIT_PROOF": EARLIEST_MISSING_QTY_UNIT_PROOF,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT": (
            EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT
        ),
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "UNIT_CHAIN_VERDICT": UNIT_CHAIN_VERDICT_VALUE,
        "ORDER_PLAN_QTY_UNIT": ORDER_PLAN_QTY_UNIT,
        "ORDER_PLAN_QTY_DOMAIN": ORDER_PLAN_QTY_DOMAIN,
        "SUI_OPERATIVE_ORDER_SZ": SUI_OPERATIVE_ORDER_SZ,
        "ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY": ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY,
        "SUI_OPERATIVE_ORDER_SZ_IS_NOT_TARGET_POSITION_QTY": True,
        "ONE_CONTRACT_EQUALS_ONE_SUI": ONE_CONTRACT_EQUALS_ONE_SUI,
        "NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF": NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF,
        "CTVAL_IS_NOT_POS_TO_SZ_FACTOR": CTVAL_IS_NOT_POS_TO_SZ_FACTOR,
        "HISTORICAL_ORDER_PLAN_VENUE_CONTRACT_COUNT_IS_NOT_CURRENT_TARGET_POSITION_QTY_UNIT": (
            HISTORICAL_ORDER_PLAN_VENUE_CONTRACT_COUNT_IS_NOT_CURRENT_TARGET_POSITION_QTY_UNIT
        ),
        "HISTORICAL_BTC_DENOMINATION_IS_NOT_CURRENT_SUI_XPERP_TARGET_POSITION_QTY_UNIT": (
            HISTORICAL_BTC_DENOMINATION_IS_NOT_CURRENT_SUI_XPERP_TARGET_POSITION_QTY_UNIT
        ),
        "IMPLICIT_PASSTHROUGH_PRESENT": IMPLICIT_PASSTHROUGH_PRESENT,
        "IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF": IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF,
        "IDENTITY_NOW_INDEPENDENTLY_PROVEN": IDENTITY_NOW_INDEPENDENTLY_PROVEN,
        "PLACE_ORDER_REQUEST_PARAM_NAMES_UNIT": PLACE_ORDER_REQUEST_PARAM_NAMES_UNIT,
        "POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE": POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE,
        "P08_CLOSED": P08_CLOSED,
        "P10_CLOSED": P10_CLOSED,
        "P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT": P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT,
        "TARGET_POSITION_NONZERO_PROVEN": TARGET_POSITION_NONZERO_PROVEN,
        "TARGET_POSITION_QTY_NUMERIC": TARGET_POSITION_QTY_NUMERIC,
        "signed_pos": window.get("signed_pos"),
        "TARGET_POSITION_QTY_RAW": window.get("TARGET_POSITION_QTY_RAW"),
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "P11_DOES_NOT_GRANT_EXECUTION_READINESS": P11_DOES_NOT_GRANT_EXECUTION_READINESS,
        "P11_DOES_NOT_AUTHORIZE_FLATTEN": P11_DOES_NOT_AUTHORIZE_FLATTEN,
        "RUNTIME_GET_REQUIRED": RUNTIME_GET_REQUIRED,
        "RUNTIME_GET_PERFORMED": RUNTIME_GET_PERFORMED,
        "PRIVATE_AUTH_USED": PRIVATE_AUTH_USED,
        "PUBLIC_SPEC_RETRIEVAL_PERFORMED": PUBLIC_SPEC_RETRIEVAL_PERFORMED,
        "INDEPENDENT_VENUE_SEMANTIC_PROOF": True,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "THIS_GO_GET_COUNT": 0,
        "THIS_GO_POST_COUNT": 0,
        "GET_PERFORMED_THIS_PERSIST": False,
        "POST_PERFORMED": False,
        "SECOND_GET_PERFORMED": False,
        "LINEAGE": lineage,
        "CENSUS": census,
        "OFFICIAL_EXCERPTS": excerpts,
        "VENUE_SEMANTIC_PROOF": proof,
        "FORBIDDEN_PROMOTION_ALIASES": list(FORBIDDEN_PROMOTION_ALIASES),
    }
