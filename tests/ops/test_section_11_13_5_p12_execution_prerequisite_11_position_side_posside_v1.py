"""P12 EXECUTION_PREREQUISITE_11 position-side / posSide contract tests. Offline only."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.prerequisite_08_fresh_position_observation_v1 import (
    adjudicate_prerequisite_08_window_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.captured_payload_v1 import (
    AUTHORIZED_TARGET_ROW,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.adjudicate_v1 import (
    P12PositionSideAdjudicationError,
    adjudicate_execution_prerequisite_11_position_side_posside_v1,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    P10_CLOSED,
    P11_CLOSED_VALUE,
    P11_PROVEN_VALUE,
    POST_ALLOWED,
    PRIVATE_AUTH_USED,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.contract_v1 import (
    ORDER_SIDE_BUY,
    ORDER_SIDE_SELL,
    PositionSidePossideError,
    assert_flatten_order_side_matches_signed_pos_v1,
    assert_no_long_short_buy_sell_conflation_v1,
    assert_pos_mode_not_rewritten_to_request_pos_side_v1,
    assert_request_pos_side_omitted_v1,
    assert_row_pos_side_not_copied_to_request_v1,
    flatten_order_side_from_signed_pos_v1,
)


def _flatten_body(*, side: str = "SELL", extra: dict[str, str] | None = None) -> dict[str, object]:
    body = build_venue_native_order_body_v1(
        client_order_id="p12test",
        instrument="SUI-USD_UM_XPERP-310404",
        order_type="limit",
        side=side,
        quantity="1",
        td_mode="cross",
        px="1",
        reduce_only=True,
    )
    if extra:
        body.update(extra)
    return body


def test_owner_go_is_forbidden_flatten_and_does_not_authorize_runtime() -> None:
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert POST_ALLOWED is False
    assert GET_ALLOWED is False
    assert PRIVATE_AUTH_USED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert THIS_SLICE == "11.13.5.P12"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_P12"
    assert P08_CLOSED is True
    assert P10_CLOSED is True
    assert P11_PROVEN_VALUE is True
    assert P11_CLOSED_VALUE is True
    assert THIS_GO_GET_COUNT == 0
    assert EARLIEST_UNRESOLVED_DEPENDENCY == (
        "EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION"
    )
    assert NEXT_AUTHORITY_BOUNDARY == (
        "SEPARATE_OWNER_GO_FOR_EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD"
    )


def test_long_signed_pos_flattens_sell_short_flattens_buy() -> None:
    assert flatten_order_side_from_signed_pos_v1(Decimal("1")) == ORDER_SIDE_SELL
    assert flatten_order_side_from_signed_pos_v1(Decimal("-1")) == ORDER_SIDE_BUY
    assert_flatten_order_side_matches_signed_pos_v1(side="SELL", signed_pos=Decimal("1"))
    assert_flatten_order_side_matches_signed_pos_v1(side="BUY", signed_pos=Decimal("-2"))


def test_zero_pos_has_no_flatten_order_side() -> None:
    with pytest.raises(PositionSidePossideError, match="ZERO_POS_HAS_NO_FLATTEN_ORDER_SIDE"):
        flatten_order_side_from_signed_pos_v1(Decimal("0"))


def test_missing_and_invalid_order_side_fail_closed() -> None:
    with pytest.raises(PositionSidePossideError, match="INVALID_FLATTEN_ORDER_SIDE:MISSING"):
        assert_flatten_order_side_matches_signed_pos_v1(side="", signed_pos=Decimal("1"))
    with pytest.raises(PositionSidePossideError, match="INVALID_FLATTEN_ORDER_SIDE:NET"):
        assert_flatten_order_side_matches_signed_pos_v1(side="net", signed_pos=Decimal("1"))
    with pytest.raises(PositionSidePossideError, match="FLATTEN_ORDER_SIDE_SIGNED_POS_MISMATCH"):
        assert_flatten_order_side_matches_signed_pos_v1(side="BUY", signed_pos=Decimal("1"))


def test_request_pos_side_present_on_flatten_body_fails_closed() -> None:
    body = _flatten_body()
    assert "posSide" not in body
    assert_request_pos_side_omitted_v1(body)
    with pytest.raises(PositionSidePossideError, match="REQUEST_POS_SIDE_PRESENT_ON_FLATTEN_BODY"):
        assert_request_pos_side_omitted_v1({**body, "posSide": "net"})
    with pytest.raises(PositionSidePossideError, match="REQUEST_POS_SIDE_PRESENT_ON_FLATTEN_BODY"):
        assert_request_pos_side_omitted_v1({**body, "posside": "long"})


def test_row_pos_side_net_is_not_copied_onto_request() -> None:
    body = _flatten_body()
    assert AUTHORIZED_TARGET_ROW["posSide"] == "net"
    assert_row_pos_side_not_copied_to_request_v1(
        row_pos_side=str(AUTHORIZED_TARGET_ROW["posSide"]),
        body=body,
    )
    with pytest.raises(PositionSidePossideError, match="REQUEST_POS_SIDE_PRESENT_ON_FLATTEN_BODY"):
        assert_row_pos_side_not_copied_to_request_v1(
            row_pos_side="net",
            body={**body, "posSide": "net"},
        )


def test_pos_mode_net_mode_does_not_imply_request_pos_side_net() -> None:
    body = _flatten_body()
    assert_pos_mode_not_rewritten_to_request_pos_side_v1(pos_mode="net_mode", body=body)
    with pytest.raises(PositionSidePossideError, match="REQUEST_POS_SIDE_PRESENT_ON_FLATTEN_BODY"):
        assert_pos_mode_not_rewritten_to_request_pos_side_v1(
            pos_mode="net_mode",
            body={**body, "posSide": "net"},
        )


def test_long_short_must_not_be_used_as_order_side() -> None:
    with pytest.raises(PositionSidePossideError, match="POSITION_TOKEN_USED_AS_ORDER_SIDE:long"):
        assert_no_long_short_buy_sell_conflation_v1("long")
    with pytest.raises(PositionSidePossideError, match="POSITION_TOKEN_USED_AS_ORDER_SIDE:short"):
        assert_no_long_short_buy_sell_conflation_v1("short")
    with pytest.raises(PositionSidePossideError, match="POSITION_TOKEN_USED_AS_ORDER_SIDE:net"):
        assert_no_long_short_buy_sell_conflation_v1("net")
    assert_no_long_short_buy_sell_conflation_v1("BUY")
    assert_no_long_short_buy_sell_conflation_v1("SELL")


def test_instrument_mismatch_fails_adjudication() -> None:
    payload = {
        "code": "0",
        "msg": "",
        "data": [{"instId": "BTC-USD_UM_XPERP-000000", "pos": "1", "posSide": "net"}],
    }
    with pytest.raises(P12PositionSideAdjudicationError):
        adjudicate_execution_prerequisite_11_position_side_posside_v1(
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            positions_payload=payload,
        )


def test_origin_main_mismatch_fails_closed() -> None:
    with pytest.raises(P12PositionSideAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        adjudicate_execution_prerequisite_11_position_side_posside_v1(origin_main_sha="deadbeef")


def test_live_window_nonzero_advances_past_prerequisite_12() -> None:
    result = adjudicate_prerequisite_08_window_v1(
        positions_payload={"code": "0", "data": [{"instId": "SUI-USD_UM_XPERP-310404", "pos": "1"}]}
    )
    assert result["EXECUTION_PREREQUISITE_11_STATUS"] == "PASS"
    assert result["EXECUTION_PREREQUISITE_12_STATUS"] == "PASS"
    assert result["EARLIEST_UNRESOLVED_DEPENDENCY"] == "BOUNDED_RUNTIME_PERMIT_ISSUANCE"
    assert result["EXECUTION_READY"] is False


def test_adjudication_closes_prerequisite_11_without_runtime() -> None:
    verdict = adjudicate_execution_prerequisite_11_position_side_posside_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA
    )
    assert verdict["CASE"] == "CASE_B_OFFLINE_CLOSABLE"
    assert verdict["EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE"] == "PASS"
    assert verdict["P11_CLOSED"] is True
    assert verdict["FLATTEN_ORDER_SIDE"] == "SELL"
    assert verdict["REQUEST_POS_SIDE"] == "OMITTED"
    assert "posSide" not in verdict["VENUE_NATIVE_BODY_KEYS"]
    assert verdict["HISTORICAL_EVIDENCE_PROMOTED_TO_CURRENT_AUTHORITY"] is False
    assert verdict["PRIVATE_AUTH_USED"] is False
    assert verdict["POST_PERFORMED"] is False
    assert verdict["LIVE_EXECUTION"] is False
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
