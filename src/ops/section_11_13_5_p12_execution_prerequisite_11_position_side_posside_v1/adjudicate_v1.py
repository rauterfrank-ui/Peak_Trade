"""Offline EXECUTION_PREREQUISITE_11 adjudication. No GET. No POST."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_consumer_v1 import (
    LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    POS_MODE_REQUIRED_VALUE,
    POSSIDE_NET_IS_NOT_POS_MODE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.captured_payload_v1 import (
    AUTHORIZED_TARGET_ROW,
    captured_envelope_v1,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.constants_v1 import (
    CASE_VALUE,
    CONFLICT_COUNT,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT,
    EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE,
    EXPECTED_ORIGIN_MAIN_SHA,
    FLATTEN_ORDER_SIDE_RULE,
    HISTORICAL_EVIDENCE_PROMOTED_TO_CURRENT_AUTHORITY,
    HISTORICAL_POSMODE_NET_STATUS,
    HISTORICAL_POSSIDE_NET_STATUS,
    LAST_CANONICALLY_CLOSED_STEP,
    LONG_SHORT_IS_NOT_BUY_SELL_VALUE,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    P11_CLOSED_VALUE,
    P11_POS_TO_SZ_CLOSED,
    P11_PROVEN_VALUE,
    P11_TEXT_REWRITTEN,
    P12_DOES_NOT_AUTHORIZE_FLATTEN,
    P12_DOES_NOT_GRANT_EXECUTION_READINESS,
    POS_MODE_IS_NOT_POSITION_SIDE_VALUE,
    POS_MODE_NET_MODE_DOES_NOT_IMPLY_REQUEST_POS_SIDE_NET_VALUE,
    POS_TO_SZ_UNIT_IDENTITY,
    POSITION_ROW_POS_SIDE_IS_NOT_REQUEST_POS_SIDE_VALUE,
    POSITION_ROW_POS_SIDE_OBSERVED_P08_VALUE,
    PREDECESSOR_SLICE,
    PRIOR_OWNER_GO,
    PRIVATE_AUTH_USED,
    PUBLIC_SPEC_RETRIEVAL_PERFORMED,
    REQUEST_POS_SIDE_POLICY_VALUE,
    REQUEST_POS_SIDE_VALUE_CURRENT,
    RUNTIME_GET_PERFORMED,
    RUNTIME_GET_REQUIRED,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_QTY_NUMERIC,
    TARGET_POSITION_QTY_UNIT,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.contract_v1 import (
    ORDER_SIDE_SELL,
    assert_no_long_short_buy_sell_conflation_v1,
    assert_pos_mode_not_rewritten_to_request_pos_side_v1,
    assert_request_pos_side_omitted_v1,
    assert_row_pos_side_not_copied_to_request_v1,
    flatten_order_side_from_signed_pos_v1,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.lineage_v1 import (
    lineage_census_summary_v1,
    position_side_lineage_v1,
)


class P12PositionSideAdjudicationError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_11 adjudication violation."""


def adjudicate_execution_prerequisite_11_position_side_posside_v1(
    *,
    origin_main_sha: str,
    positions_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P12PositionSideAdjudicationError("ORIGIN_MAIN_SHA_MISMATCH")
    if AUTHORIZED_TARGET_ROW.get("pos") != "1":
        raise P12PositionSideAdjudicationError("CAPTURED_POS_DRIFT")
    if AUTHORIZED_TARGET_ROW.get("posSide") != POSITION_ROW_POS_SIDE_OBSERVED_P08_VALUE:
        raise P12PositionSideAdjudicationError("CAPTURED_ROW_POS_SIDE_DRIFT")
    if AUTHORIZED_TARGET_ROW.get("instId") != TARGET_INSTRUMENT_ID:
        raise P12PositionSideAdjudicationError("INSTRUMENT_MISMATCH")
    if POSSIDE_NET_IS_NOT_POS_MODE is not True:
        raise P12PositionSideAdjudicationError("POSSIDE_NET_COLLAPSED_INTO_POS_MODE")
    if LEVERAGE_POSSIDE_NET_REUSED_AS_POS_MODE_PROOF is not False:
        raise P12PositionSideAdjudicationError("ROW_POSSIDE_REUSED_AS_POS_MODE")
    if POS_MODE_REQUIRED_VALUE != "net_mode":
        raise P12PositionSideAdjudicationError("POS_MODE_REQUIRED_VALUE_DRIFT")

    envelope = captured_envelope_v1() if positions_payload is None else dict(positions_payload)
    window = adjudicate_prerequisite_08_window_v1(
        positions_payload=envelope,
        instrument_id=TARGET_INSTRUMENT_ID,
    )
    if window.get("TARGET_POSITION_QTY_UNIT") != "PROVEN":
        raise P12PositionSideAdjudicationError("PRODUCER_UNIT_NOT_PROVEN")
    if window.get("TARGET_POSITION_QTY_NUMERIC") != "PASS":
        raise P12PositionSideAdjudicationError("QTY_NUMERIC_NOT_PASS")
    signed_raw = window.get("signed_pos")
    if signed_raw is None:
        raise P12PositionSideAdjudicationError("SIGNED_POS_PRODUCER_ABSENT")
    signed = Decimal(str(signed_raw))
    order_side = flatten_order_side_from_signed_pos_v1(signed)
    if order_side != ORDER_SIDE_SELL:
        raise P12PositionSideAdjudicationError("P08_LONG_POS_MUST_FLATTEN_SELL")
    assert_no_long_short_buy_sell_conflation_v1(order_side)

    body = build_venue_native_order_body_v1(
        client_order_id="p12prereq11",
        instrument=TARGET_INSTRUMENT_ID,
        order_type="limit",
        side=order_side,
        quantity="1",
        td_mode="cross",
        px="1",
        reduce_only=True,
    )
    assert_request_pos_side_omitted_v1(body)
    assert_row_pos_side_not_copied_to_request_v1(
        row_pos_side=str(AUTHORIZED_TARGET_ROW.get("posSide")),
        body=body,
    )
    assert_pos_mode_not_rewritten_to_request_pos_side_v1(
        pos_mode=POS_MODE_REQUIRED_VALUE,
        body=body,
    )
    if str(body.get("side") or "") != order_side.lower():
        raise P12PositionSideAdjudicationError("MAPPER_ORDER_SIDE_DRIFT")
    if window.get("EARLIEST_UNRESOLVED_DEPENDENCY") != EARLIEST_UNRESOLVED_DEPENDENCY:
        raise P12PositionSideAdjudicationError("WINDOW_EARLIEST_DEPENDENCY_DRIFT")
    if window.get("EXECUTION_PREREQUISITE_11_STATUS") != (
        EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE
    ):
        raise P12PositionSideAdjudicationError("WINDOW_PREREQUISITE_11_STATUS_DRIFT")

    lineage = position_side_lineage_v1()
    census = lineage_census_summary_v1()
    if int(census["SEAM_COUNT"]) != len(lineage):
        raise P12PositionSideAdjudicationError("LINEAGE_CENSUS_DRIFT")

    return {
        "OWNER_GO": OWNER_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
        "CASE": CASE_VALUE,
        "EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE": (
            EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE
        ),
        "P11_PROVEN": P11_PROVEN_VALUE,
        "P11_CLOSED": P11_CLOSED_VALUE,
        "FLATTEN_ORDER_SIDE_RULE": FLATTEN_ORDER_SIDE_RULE,
        "FLATTEN_ORDER_SIDE": order_side,
        "REQUEST_POS_SIDE_POLICY": REQUEST_POS_SIDE_POLICY_VALUE,
        "REQUEST_POS_SIDE": REQUEST_POS_SIDE_VALUE_CURRENT,
        "POSITION_ROW_POS_SIDE_OBSERVED_P08": POSITION_ROW_POS_SIDE_OBSERVED_P08_VALUE,
        "POSITION_ROW_POS_SIDE_IS_NOT_REQUEST_POS_SIDE": (
            POSITION_ROW_POS_SIDE_IS_NOT_REQUEST_POS_SIDE_VALUE
        ),
        "POS_MODE_IS_NOT_POSITION_SIDE": POS_MODE_IS_NOT_POSITION_SIDE_VALUE,
        "POS_MODE_REQUIRED_VALUE": POS_MODE_REQUIRED_VALUE,
        "POS_MODE_NET_MODE_DOES_NOT_IMPLY_REQUEST_POS_SIDE_NET": (
            POS_MODE_NET_MODE_DOES_NOT_IMPLY_REQUEST_POS_SIDE_NET_VALUE
        ),
        "LONG_SHORT_IS_NOT_BUY_SELL": LONG_SHORT_IS_NOT_BUY_SELL_VALUE,
        "HISTORICAL_POSMODE_NET_STATUS": HISTORICAL_POSMODE_NET_STATUS,
        "HISTORICAL_POSSIDE_NET_STATUS": HISTORICAL_POSSIDE_NET_STATUS,
        "HISTORICAL_EVIDENCE_PROMOTED_TO_CURRENT_AUTHORITY": (
            HISTORICAL_EVIDENCE_PROMOTED_TO_CURRENT_AUTHORITY
        ),
        "POSSIDE_NET_IS_NOT_POS_MODE": POSSIDE_NET_IS_NOT_POS_MODE,
        "CONFLICT_COUNT": CONFLICT_COUNT,
        "P08_CLOSED": P08_CLOSED,
        "P10_CLOSED": P10_CLOSED,
        "P11_POS_TO_SZ_CLOSED": P11_POS_TO_SZ_CLOSED,
        "P11_TEXT_REWRITTEN": P11_TEXT_REWRITTEN,
        "TARGET_POSITION_NONZERO_PROVEN": TARGET_POSITION_NONZERO_PROVEN,
        "TARGET_POSITION_QTY_NUMERIC": TARGET_POSITION_QTY_NUMERIC,
        "TARGET_POSITION_QTY_UNIT": TARGET_POSITION_QTY_UNIT,
        "POS_TO_SZ_UNIT_IDENTITY": POS_TO_SZ_UNIT_IDENTITY,
        "signed_pos": str(signed),
        "LAST_CANONICALLY_CLOSED_STEP": LAST_CANONICALLY_CLOSED_STEP,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "NEXT_AUTHORITY_BOUNDARY": NEXT_AUTHORITY_BOUNDARY,
        "EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT": (
            EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT
        ),
        "P12_DOES_NOT_GRANT_EXECUTION_READINESS": P12_DOES_NOT_GRANT_EXECUTION_READINESS,
        "P12_DOES_NOT_AUTHORIZE_FLATTEN": P12_DOES_NOT_AUTHORIZE_FLATTEN,
        "RUNTIME_GET_REQUIRED": RUNTIME_GET_REQUIRED,
        "RUNTIME_GET_PERFORMED": RUNTIME_GET_PERFORMED,
        "PRIVATE_AUTH_USED": PRIVATE_AUTH_USED,
        "PUBLIC_SPEC_RETRIEVAL_PERFORMED": PUBLIC_SPEC_RETRIEVAL_PERFORMED,
        "LIVE_EXECUTION": False,
        "CANARY_EXECUTION": False,
        "MERGE_AUTHORIZED_BY_THIS_PERSIST": False,
        "THIS_GO_GET_COUNT": 0,
        "THIS_GO_POST_COUNT": 0,
        "GET_PERFORMED_THIS_PERSIST": False,
        "POST_PERFORMED": False,
        "LINEAGE": lineage,
        "CENSUS": census,
        "VENUE_NATIVE_BODY_KEYS": sorted(body.keys()),
    }
