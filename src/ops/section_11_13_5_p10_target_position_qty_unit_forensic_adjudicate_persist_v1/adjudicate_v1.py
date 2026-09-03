"""Offline TARGET_POSITION_QTY unit adjudication. No GET. No POST. No unit invention."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.execution_prerequisite_08_cluster_contract_v1 import (
    UNIT_CHAIN_VERDICT,
)
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
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.constants_v1 import (
    CONFLICT_COUNT,
    CURRENT_UNIT_CONTRACT,
    EARLIEST_MISSING_QTY_UNIT_PROOF,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_PROMOTION_ALIASES,
    HISTORICAL_BTC_DENOMINATION_IS_NOT_CURRENT_SUI_XPERP_TARGET_POSITION_QTY_UNIT,
    HISTORICAL_ORDER_PLAN_VENUE_CONTRACT_COUNT_IS_NOT_CURRENT_TARGET_POSITION_QTY_UNIT,
    IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF,
    IMPLICIT_PASSTHROUGH_PRESENT,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF,
    ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY,
    OWNER_GO,
    P08_CLOSED,
    P10_DOES_NOT_GRANT_EXECUTION_READINESS,
    P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT,
    POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PROVEN_UNIT_TOKENS,
    QTY_UNIT_CENSUS_COMPLETE,
    QTY_UNIT_LINEAGE_COMPLETE,
    SIMULATED_EXECUTION_PORT_IS_NOT_TARGET_POSITION_QTY_PRODUCER,
    STEP_29P_IS_NOT_TARGET_POSITION_QTY_PRODUCER,
    STEP_29Q_IS_NOT_TARGET_POSITION_QTY_PRODUCER,
    SUI_OPERATIVE_ORDER_SZ_IS_NOT_TARGET_POSITION_QTY,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_QTY_NUMERIC,
    TARGET_POSITION_QTY_UNIT,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.lineage_v1 import (
    lineage_census_summary_v1,
    target_position_qty_lineage_v1,
)


class P10QtyUnitAdjudicationError(RuntimeError):
    """Fail-closed TARGET_POSITION_QTY unit adjudication violation."""


def _reject_proven_claim(value: Any, *, field: str) -> None:
    text = str(value or "").strip()
    if text in PROVEN_UNIT_TOKENS and text != "UNPROVEN":
        raise P10QtyUnitAdjudicationError(f"FORBIDDEN_UNIT_PROMOTION:{field}:{text}")
    lowered = text.lower()
    if lowered in {alias.lower() for alias in FORBIDDEN_PROMOTION_ALIASES} and field in {
        "TARGET_POSITION_QTY_UNIT",
        "CURRENT_UNIT_CONTRACT",
    }:
        raise P10QtyUnitAdjudicationError(f"FORBIDDEN_ALIAS_AS_UNIT:{field}:{text}")


def adjudicate_target_position_qty_unit_v1(
    *,
    origin_main_sha: str,
    claimed_unit: str | None = None,
    positions_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P10QtyUnitAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if ONE_CONTRACT_EQUALS_ONE_SUI is not False:
        raise P10QtyUnitAdjudicationError("ONE_CONTRACT_EQUALS_ONE_SUI_MUST_REMAIN_FALSE")
    if UNIT_CHAIN_VERDICT != "PASSTHROUGH_POS_TO_SZ_UNIT_IDENTITY_UNPROVEN":
        raise P10QtyUnitAdjudicationError("UNIT_CHAIN_VERDICT_DRIFT")
    if ORDER_PLAN_QTY_UNIT == TARGET_POSITION_QTY_UNIT and TARGET_POSITION_QTY_UNIT != "UNPROVEN":
        raise P10QtyUnitAdjudicationError("ORDER_PLAN_ALIAS_COLLAPSED_INTO_TARGET_POSITION_QTY")
    if claimed_unit is not None:
        _reject_proven_claim(claimed_unit, field="TARGET_POSITION_QTY_UNIT")
        if str(claimed_unit).strip() != "UNPROVEN":
            raise P10QtyUnitAdjudicationError("CLAIMED_UNIT_NOT_UNPROVEN")

    envelope = captured_envelope_v1() if positions_payload is None else dict(positions_payload)
    window = adjudicate_prerequisite_08_window_v1(
        positions_payload=envelope,
        instrument_id=TARGET_INSTRUMENT_ID,
    )
    producer_unit = window.get("TARGET_POSITION_QTY_UNIT")
    if producer_unit != "UNPROVEN":
        raise P10QtyUnitAdjudicationError(f"PRODUCER_UNIT_DRIFT:{producer_unit}")
    if window.get("TARGET_POSITION_QTY_NUMERIC") != "PASS":
        raise P10QtyUnitAdjudicationError("QTY_NUMERIC_NOT_PASS")
    if window.get("UNIT_CHAIN_VERDICT") != UNIT_CHAIN_VERDICT:
        raise P10QtyUnitAdjudicationError("WINDOW_UNIT_CHAIN_VERDICT_DRIFT")
    if AUTHORIZED_TARGET_ROW.get("pos") != "1":
        raise P10QtyUnitAdjudicationError("CAPTURED_POS_DRIFT")
    if "posCcy" in AUTHORIZED_TARGET_ROW:
        raise P10QtyUnitAdjudicationError("POSCCY_UNEXPECTEDLY_PRESENT")

    lineage = target_position_qty_lineage_v1()
    census = lineage_census_summary_v1()
    if census["TARGET_POSITION_QTY_PROVEN_UNITS_FOUND"]:
        raise P10QtyUnitAdjudicationError("LINEAGE_CONTAINS_PROVEN_TARGET_UNIT")
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise P10QtyUnitAdjudicationError("LINEAGE_CENSUS_DRIFT")

    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "TARGET_POSITION_QTY_UNIT": TARGET_POSITION_QTY_UNIT,
        "CURRENT_UNIT_CONTRACT": CURRENT_UNIT_CONTRACT,
        "QTY_UNIT_CENSUS_COMPLETE": QTY_UNIT_CENSUS_COMPLETE,
        "QTY_UNIT_LINEAGE_COMPLETE": QTY_UNIT_LINEAGE_COMPLETE,
        "EARLIEST_MISSING_QTY_UNIT_PROOF": EARLIEST_MISSING_QTY_UNIT_PROOF,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "UNIT_CHAIN_VERDICT": UNIT_CHAIN_VERDICT,
        "ORDER_PLAN_QTY_UNIT": ORDER_PLAN_QTY_UNIT,
        "ORDER_PLAN_QTY_DOMAIN": ORDER_PLAN_QTY_DOMAIN,
        "SUI_OPERATIVE_ORDER_SZ": SUI_OPERATIVE_ORDER_SZ,
        "ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY": ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY,
        "SUI_OPERATIVE_ORDER_SZ_IS_NOT_TARGET_POSITION_QTY": (
            SUI_OPERATIVE_ORDER_SZ_IS_NOT_TARGET_POSITION_QTY
        ),
        "ONE_CONTRACT_EQUALS_ONE_SUI": ONE_CONTRACT_EQUALS_ONE_SUI,
        "NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF": NUMERIC_POS_EQUALS_SZ_IS_NOT_UNIT_PROOF,
        "HISTORICAL_ORDER_PLAN_VENUE_CONTRACT_COUNT_IS_NOT_CURRENT_TARGET_POSITION_QTY_UNIT": (
            HISTORICAL_ORDER_PLAN_VENUE_CONTRACT_COUNT_IS_NOT_CURRENT_TARGET_POSITION_QTY_UNIT
        ),
        "HISTORICAL_BTC_DENOMINATION_IS_NOT_CURRENT_SUI_XPERP_TARGET_POSITION_QTY_UNIT": (
            HISTORICAL_BTC_DENOMINATION_IS_NOT_CURRENT_SUI_XPERP_TARGET_POSITION_QTY_UNIT
        ),
        "STEP_29P_IS_NOT_TARGET_POSITION_QTY_PRODUCER": STEP_29P_IS_NOT_TARGET_POSITION_QTY_PRODUCER,
        "STEP_29Q_IS_NOT_TARGET_POSITION_QTY_PRODUCER": STEP_29Q_IS_NOT_TARGET_POSITION_QTY_PRODUCER,
        "SIMULATED_EXECUTION_PORT_IS_NOT_TARGET_POSITION_QTY_PRODUCER": (
            SIMULATED_EXECUTION_PORT_IS_NOT_TARGET_POSITION_QTY_PRODUCER
        ),
        "IMPLICIT_PASSTHROUGH_PRESENT": IMPLICIT_PASSTHROUGH_PRESENT,
        "IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF": IMPLICIT_PASSTHROUGH_IS_NOT_UNIT_PROOF,
        "POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE": POSCCY_PRESENT_IN_AUTHORIZED_P08_CAPTURE,
        "P08_CLOSED": P08_CLOSED,
        "TARGET_POSITION_NONZERO_PROVEN": TARGET_POSITION_NONZERO_PROVEN,
        "TARGET_POSITION_QTY_NUMERIC": TARGET_POSITION_QTY_NUMERIC,
        "signed_pos": window.get("signed_pos"),
        "TARGET_POSITION_QTY_RAW": window.get("TARGET_POSITION_QTY_RAW"),
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "P10_DOES_NOT_GRANT_EXECUTION_READINESS": P10_DOES_NOT_GRANT_EXECUTION_READINESS,
        "P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT": P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT,
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
        "FORBIDDEN_PROMOTION_ALIASES": list(FORBIDDEN_PROMOTION_ALIASES),
    }
