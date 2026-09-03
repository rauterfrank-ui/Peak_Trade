"""P08 empty-data-not-zero GET-package tests. Recording transport only."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    REQUIRED_SECRETREF_URI,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
    sanitize_redirect_location_v1,
)
from src.ops.section_11_13_5_p08_empty_data_not_zero_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_D_TARGET_NOT_OBSERVED,
    CASE_E_HTTP_OR_OKX_ERROR,
    EMPTY_DATA_IS_ZERO,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FALLBACK_REQUEST_ALLOWED,
    FILTERED_EMPTY_IS_ZERO,
    GET_1_ROLE,
    GET_2_ROLE,
    GET_3_ROLE,
    INSTID_FILTER_ALLOWED,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    NEXT_AUTHORITY_BOUNDARY_CASE_C_REMAINS,
    OWNER_GO,
    P09_WORK_ALLOWED,
    POST_ALLOWED,
    REDIRECT_FOLLOW_ALLOWED,
    RESULT_CLASS_200_OKX_0,
    RETRY_ALLOWED,
    SECOND_GET_ALLOWED,
    TARGET_INST_TYPE,
    TARGET_INSTRUMENT_ID,
    THIRD_GET_ALLOWED,
    THIS_SLICE,
    TYPED_EMPTY_IS_ZERO,
    WHITELIST_MUTATION_ALLOWED,
)
from src.ops.section_11_13_5_p08_empty_data_not_zero_v1.execute_v1 import (
    P08EmptyDataNotZeroError,
    execute_p08_empty_data_not_zero_gets_v1,
)
from src.ops.section_11_13_5_p08_empty_data_not_zero_v1.persist_claims_v1 import (
    CLAIMS,
)

EMPTY_BODY = b'{"code":"0","msg":"","data":[]}'
ZERO_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"0","posSide":"net","mgnMode":"isolated"}]}'
)
NONZERO_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"1","posSide":"net","mgnMode":"isolated"}]}'
)
OTHER_INST_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"BTC-USDT-SWAP","pos":"2",'
    b'"posSide":"net","mgnMode":"isolated"}]}'
)
FAIL_50110_BODY = (
    b'{"code":"50110","msg":"Your IP 203.0.113.50 is not included in your API '
    b'key\'s IP whitelist.","data":[]}'
)


@dataclass
class _SequencedRecordingTransportV1:
    """Test-only sequenced bodies. Not a production transport class."""

    bodies: list[bytes]
    status_code: int = 200
    transport_class: str = TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    venue_live_contact: bool = False
    calls: list[LiveCanaryHttpRequestV1] = field(default_factory=list)

    def send(self, request: LiveCanaryHttpRequestV1) -> LiveCanaryHttpResponseV1:
        self.calls.append(request)
        index = len(self.calls) - 1
        if index >= len(self.bodies):
            raise AssertionError("UNEXPECTED_EXTRA_GET")
        body = self.bodies[index]
        return LiveCanaryHttpResponseV1(
            status_code=self.status_code,
            body_bytes=body,
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method=request.method,
            send_attempted=True,
            redirect_followed=False,
            redirect_status=None,
            redirect_location=sanitize_redirect_location_v1(None),
            response_headers_safe={},
        )


def _run(
    tmp_path: Path,
    bodies: list[bytes],
    *,
    status: int = 200,
) -> dict:
    transport = _SequencedRecordingTransportV1(bodies=list(bodies), status_code=status)
    return execute_p08_empty_data_not_zero_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )


def test_standing_flags_remain_fail_closed() -> None:
    assert OWNER_GO == ("PEAK_TRADE_OWNER_GO_P08_EMPTY_DATA_NOT_ZERO_MAXIMUM_SAFE_LEVERAGE_V1")
    assert THIS_SLICE == "11.13.5.P08_EMPTY_DATA_NOT_ZERO"
    assert ENDPOINT == "/api/v5/account/positions"
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert TARGET_INSTRUMENT_ID == DEFAULT_INSTRUMENT_ID
    assert TARGET_INST_TYPE == DEFAULT_INST_TYPE
    assert MAX_NETWORK_REQUEST_COUNT == 3
    assert MAX_HTTP_EXCHANGE_COUNT == 3
    assert RETRY_ALLOWED is False
    assert REDIRECT_FOLLOW_ALLOWED is False
    assert FALLBACK_REQUEST_ALLOWED is False
    assert SECOND_GET_ALLOWED is True
    assert THIRD_GET_ALLOWED is True
    assert INSTID_FILTER_ALLOWED is True
    assert WHITELIST_MUTATION_ALLOWED is False
    assert POST_ALLOWED is False
    assert P09_WORK_ALLOWED is False
    assert EMPTY_DATA_IS_ZERO is False
    assert FILTERED_EMPTY_IS_ZERO is False
    assert TYPED_EMPTY_IS_ZERO is False
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert CLAIMS["EXECUTION_READY"] is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert REQUIRED_SECRETREF_URI == (
        "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
    )
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_wrong_owner_go_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(P08EmptyDataNotZeroError, match="OWNER_GO_MISMATCH"):
        execute_p08_empty_data_not_zero_gets_v1(
            owner_go="PEAK_TRADE_OWNER_GO_P08_POSITION_OBSERVATION_V1",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=_SequencedRecordingTransportV1(bodies=[EMPTY_BODY]),
        )


def test_wrong_origin_main_sha_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(P08EmptyDataNotZeroError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_p08_empty_data_not_zero_gets_v1(
            owner_go=OWNER_GO,
            origin_main_sha="12e2d222e95b78ddc91c642253c6907743495ba9",
            evidence_root=tmp_path,
            transport=_SequencedRecordingTransportV1(bodies=[EMPTY_BODY]),
        )


def test_case_c_remaining_issues_three_empty_gets_and_is_not_zero(tmp_path: Path) -> None:
    result = _run(tmp_path, [EMPTY_BODY, EMPTY_BODY, EMPTY_BODY])
    summary = result["summary"]
    assert summary["RESULT_CLASS"] == RESULT_CLASS_200_OKX_0
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    assert summary["POSITION_STATE_OBSERVED"] is False
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 3
    assert summary["GET_ROLES_PERFORMED"] == [GET_1_ROLE, GET_2_ROLE, GET_3_ROLE]
    assert summary["POST_COUNT"] == 0
    assert summary["RETRY_COUNT"] == 0
    assert summary["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert summary["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY_CASE_C_REMAINS
    pack = Path(result["EVIDENCE_PACK"])
    assert (pack / "GET_01_UNFILTERED.raw.json").is_file()
    assert (pack / "GET_02_INSTID.raw.json").is_file()
    assert (pack / "GET_03_INSTTYPE.raw.json").is_file()
    raw1 = json.loads((pack / "GET_01_UNFILTERED.raw.json").read_text(encoding="utf-8"))
    assert raw1["BODY_WAS_JSON_RESERIALIZED"] is False
    assert raw1["BODY_UTF8_EXACT"] == EMPTY_BODY.decode("utf-8")
    census = (pack / "CENSUS.json").read_text(encoding="utf-8")
    assert "NAVIGATION_INVENTORY_NOT_SSOT_NOT_AUTHORITY" in census


def test_get1_nonzero_stops_after_one_get_and_closes_p08(tmp_path: Path) -> None:
    result = _run(tmp_path, [NONZERO_BODY])
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_A_TARGET_NONZERO
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is True
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is True
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["GET_ROLES_PERFORMED"] == [GET_1_ROLE]
    assert summary["LIVE_EXECUTION"] is False
    assert "EXECUTION_PREREQUISITE_10" in summary["NEXT_AUTHORITY_BOUNDARY"] or (
        "EXECUTION_PREREQUISITE_09" in summary["NEXT_AUTHORITY_BOUNDARY"]
    )


def test_empty_then_zero_row_proves_zero_and_does_not_close_p08(tmp_path: Path) -> None:
    result = _run(tmp_path, [EMPTY_BODY, ZERO_BODY])
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_B_TARGET_ZERO
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is True
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 2
    assert summary["GET_ROLES_PERFORMED"] == [GET_1_ROLE, GET_2_ROLE]


def test_empty_then_nonzero_closes_p08(tmp_path: Path) -> None:
    result = _run(tmp_path, [EMPTY_BODY, NONZERO_BODY])
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_A_TARGET_NONZERO
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is True
    assert summary["P08_CLOSED"] is True
    assert summary["GET_REQUEST_COUNT"] == 2


def test_empty_then_empty_then_other_instrument_is_case_d(tmp_path: Path) -> None:
    result = _run(tmp_path, [EMPTY_BODY, EMPTY_BODY, OTHER_INST_BODY])
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_D_TARGET_NOT_OBSERVED
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 3
    assert summary["UNFILTERED_EMPTY_AND_TYPED_NONEMPTY"] is True


def test_case_e_50110_does_not_issue_followup_gets(tmp_path: Path) -> None:
    result = _run(tmp_path, [FAIL_50110_BODY], status=401)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_E_HTTP_OR_OKX_ERROR
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False


def test_filtered_empty_is_still_not_zero(tmp_path: Path) -> None:
    result = _run(tmp_path, [EMPTY_BODY, EMPTY_BODY, EMPTY_BODY])
    assert result["summary"]["TARGET_POSITION_ZERO_PROVEN"] is False
    assert result["adjudication"]["FILTERED_EMPTY_IS_ZERO"] is False
    assert result["adjudication"]["TYPED_EMPTY_IS_ZERO"] is False
    assert result["adjudication"]["EMPTY_DATA_IS_ZERO"] is False
