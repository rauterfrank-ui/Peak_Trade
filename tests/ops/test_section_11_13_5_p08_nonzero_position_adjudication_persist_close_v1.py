"""P08 CASE_A nonzero adjudication unit tests. Offline only. No GET. No POST."""

from __future__ import annotations

import pytest

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
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.adjudicate_v1 import (
    P08NonzeroAdjudicationError,
    adjudicate_captured_nonzero_position_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.captured_payload_v1 import (
    AUTHORIZED_TARGET_ROW,
    P08CapturedPayloadError,
    captured_envelope_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.constants_v1 import (
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EMPTY_DATA_IS_ZERO,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ALLOWED,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_CLOSED,
    POST_ALLOWED,
    TARGET_INSTRUMENT_ID,
    TARGET_POSITION_NONZERO_PROVEN,
    THIS_GO_GET_COUNT,
    THIS_SLICE,
)
from src.ops.section_11_13_5_p08_position_observation_v1.constants_v1 import (
    CASE_A_TARGET_NONZERO,
)


def test_owner_go_is_forbidden_flatten_and_does_not_authorize_runtime() -> None:
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert POST_ALLOWED is False
    assert GET_ALLOWED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert EMPTY_DATA_IS_ZERO is False
    assert THIS_SLICE == "11.13.5.P08"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_13_5_P08"
    assert P08_CLOSED is True
    assert TARGET_POSITION_NONZERO_PROVEN is True
    assert THIS_GO_GET_COUNT == 0


def test_captured_row_adjudicates_case_a_and_closes_p08() -> None:
    verdict = adjudicate_captured_nonzero_position_v1(origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA)
    assert verdict["POSITION_OBSERVATION_CLASS"] == CASE_A_TARGET_NONZERO
    assert verdict["P08_CLOSED"] is True
    assert verdict["TARGET_POSITION_NONZERO_PROVEN"] is True
    assert verdict["TARGET_POSITION_ZERO_PROVEN"] is False
    assert verdict["EMPTY_DATA_IS_ZERO"] is False
    assert verdict["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert verdict["classifier_state"] == "TARGET_POSITION_NONZERO_PROVEN"
    assert verdict["signed_pos"] == "1"
    assert verdict["query_completeness_proven"] is False
    assert verdict["TARGET_POSITION_QTY_NUMERIC"] == "PASS"
    assert verdict["TARGET_POSITION_QTY_UNIT"] == "UNPROVEN"
    assert verdict["EARLIEST_UNRESOLVED_DEPENDENCY"] == EARLIEST_UNRESOLVED_DEPENDENCY
    assert verdict["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY
    assert "EXECUTION_PREREQUISITE_10" in verdict["NEXT_AUTHORITY_BOUNDARY"]
    assert verdict["THIS_GO_GET_COUNT"] == 0
    assert verdict["POST_PERFORMED"] is False
    assert verdict["SECOND_GET_PERFORMED"] is False
    assert verdict["ORIGINAL_WIRE_BODY_BYTES_AVAILABLE"] is False
    assert verdict["LIVE_EXECUTION"] is False
    assert verdict["CAPTURED_ENVELOPE"]["data"][0]["instId"] == TARGET_INSTRUMENT_ID
    assert verdict["CAPTURED_ENVELOPE"]["data"][0]["pos"] == "1"
    assert verdict["CAPTURED_ENVELOPE"]["data"][0] == AUTHORIZED_TARGET_ROW


def test_wrong_origin_sha_fail_closed() -> None:
    with pytest.raises(P08NonzeroAdjudicationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        adjudicate_captured_nonzero_position_v1(origin_main_sha="deadbeef")


def test_zero_pos_is_rejected_without_normalization() -> None:
    payload = captured_envelope_v1()
    payload["data"][0]["pos"] = "0"
    with pytest.raises((P08CapturedPayloadError, P08NonzeroAdjudicationError)):
        adjudicate_captured_nonzero_position_v1(
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            payload=payload,
        )


def test_empty_data_is_rejected() -> None:
    with pytest.raises((P08CapturedPayloadError, P08NonzeroAdjudicationError)):
        adjudicate_captured_nonzero_position_v1(
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            payload={"code": "0", "msg": "", "data": []},
        )
