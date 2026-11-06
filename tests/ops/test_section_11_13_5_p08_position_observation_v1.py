"""P08 one-shot unfiltered positions GET tests. Recording transport only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    REQUIRED_SECRETREF_URI,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_D_TARGET_NOT_OBSERVED,
    CASE_E_HTTP_OR_OKX_ERROR,
    CASE_F_AMBIGUOUS,
    DEFAULT_MAX_RETRIES,
    EMPTY_DATA_IS_ZERO,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FALLBACK_REQUEST_ALLOWED,
    INSTID_FILTER_ALLOWED,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    P09_WORK_ALLOWED,
    POST_ALLOWED,
    REDIRECT_FOLLOW_ALLOWED,
    RESULT_CLASS_200_OKX_0,
    RESULT_CLASS_401_50110,
    RETRY_ALLOWED,
    SECOND_GET_ALLOWED,
    SUBMIT_BODY_PROBE_ALLOWED,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WHITELIST_MUTATION_ALLOWED,
)
from src.ops.section_11_13_5_p08_position_observation_v1.execute_v1 import (
    P08PositionObservationError,
    execute_single_p08_position_observation_get_v1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.persist_claims_v1 import (
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
AMBIGUOUS_BODY = (
    b'{"code":"0","msg":"","data":['
    b'{"instId":"SUI-USD_UM_XPERP-310404","pos":"1","posSide":"long"},'
    b'{"instId":"SUI-USD_UM_XPERP-310404","pos":"1","posSide":"short"}'
    b"]}"
)
FAIL_50110_BODY = (
    b'{"code":"50110","msg":"Your IP 203.0.113.50 is not included in your API '
    b'key\'s IP whitelist.","data":[]}'
)
VENUE_ERROR_BODY = b'{"code":"50014","msg":"Invalid sign","data":[]}'


def _run(tmp_path: Path, body: bytes, *, status: int = 200) -> dict:
    transport = RecordingFakeCanaryTransportV1(status_code=status, body=body)
    return execute_single_p08_position_observation_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )


def test_standing_flags_remain_fail_closed() -> None:
    assert OWNER_GO == "PEAK_TRADE_OWNER_GO_P08_POSITION_OBSERVATION_V1"
    assert THIS_SLICE == "11.13.5.P08_POSITION_OBSERVATION"
    assert ENDPOINT == "/api/v5/account/positions"
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert TARGET_INSTRUMENT_ID == DEFAULT_INSTRUMENT_ID
    assert MAX_NETWORK_REQUEST_COUNT == 1
    assert MAX_HTTP_EXCHANGE_COUNT == 1
    assert DEFAULT_MAX_RETRIES == 0
    assert RETRY_ALLOWED is False
    assert REDIRECT_FOLLOW_ALLOWED is False
    assert FALLBACK_REQUEST_ALLOWED is False
    assert SECOND_GET_ALLOWED is False
    assert INSTID_FILTER_ALLOWED is False
    assert WHITELIST_MUTATION_ALLOWED is False
    assert POST_ALLOWED is False
    assert P09_WORK_ALLOWED is False
    assert SUBMIT_BODY_PROBE_ALLOWED is False
    assert EMPTY_DATA_IS_ZERO is False
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
    with pytest.raises(P08PositionObservationError, match="OWNER_GO_MISMATCH"):
        execute_single_p08_position_observation_get_v1(
            owner_go="PEAK_TRADE_OWNER_GO_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_V1",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=EMPTY_BODY),
        )


def test_wrong_origin_main_sha_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(P08PositionObservationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_single_p08_position_observation_get_v1(
            owner_go=OWNER_GO,
            origin_main_sha="f796e2f7497282862a1762f1bcc7a63ce4b99d9c",
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=EMPTY_BODY),
        )


def test_case_c_empty_data_is_not_zero(tmp_path: Path) -> None:
    result = _run(tmp_path, EMPTY_BODY)
    summary = result["summary"]
    assert summary["RESULT_CLASS"] == RESULT_CLASS_200_OKX_0
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    assert summary["POSITION_STATE_OBSERVED"] is False
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["POST_COUNT"] == 0
    assert summary["RETRY_COUNT"] == 0
    assert summary["G_POSMODE_SUBMIT_BODY_PROVEN"] is False


def test_case_b_zero_row_does_not_close_p08(tmp_path: Path) -> None:
    result = _run(tmp_path, ZERO_BODY)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_B_TARGET_ZERO
    assert summary["POSITION_STATE_OBSERVED"] is True
    assert summary["TARGET_INSTRUMENT_ROW_OBSERVED"] is True
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is True
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False


def test_case_a_nonzero_closes_p08_observation_gate(tmp_path: Path) -> None:
    result = _run(tmp_path, NONZERO_BODY)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_A_TARGET_NONZERO
    assert summary["POSITION_STATE_OBSERVED"] is True
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is True
    assert summary["P08_CLOSED"] is True
    assert summary["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert summary["LIVE_EXECUTION"] is False
    assert "EXECUTION_PREREQUISITE_10" in summary["NEXT_AUTHORITY_BOUNDARY"]


def test_case_d_other_instrument_is_not_observed(tmp_path: Path) -> None:
    result = _run(tmp_path, OTHER_INST_BODY)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_D_TARGET_NOT_OBSERVED
    assert summary["TARGET_INSTRUMENT_ROW_OBSERVED"] is False
    assert summary["POSITION_STATE_OBSERVED"] is False
    assert summary["P08_CLOSED"] is False


def test_case_f_ambiguous_rows_fail_closed(tmp_path: Path) -> None:
    result = _run(tmp_path, AMBIGUOUS_BODY)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_F_AMBIGUOUS
    assert summary["P08_CLOSED"] is False
    assert summary["POSITION_STATE_OBSERVED"] is False


def test_case_e_50110_does_not_retry(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(status_code=401, body=FAIL_50110_BODY)
    result = execute_single_p08_position_observation_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    summary = result["summary"]
    assert summary["RESULT_CLASS"] == RESULT_CLASS_401_50110
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_E_HTTP_OR_OKX_ERROR
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 1
    assert len(transport.calls) == 1
    assert transport.calls[0].method == "GET"
    assert transport.calls[0].endpoint == ENDPOINT


def test_case_e_venue_error_malformed_okx(tmp_path: Path) -> None:
    result = _run(tmp_path, VENUE_ERROR_BODY)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_E_HTTP_OR_OKX_ERROR
    assert summary["P08_CLOSED"] is False
    assert summary["RETRY_COUNT"] == 0


def test_redaction_omits_secrets_and_keeps_pos(tmp_path: Path) -> None:
    result = _run(tmp_path, NONZERO_BODY)
    pack = Path(result["EVIDENCE_PACK"])
    snapshot = json.loads((pack / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8"))
    text = json.dumps(snapshot)
    lowered = text.lower()
    assert "plaintext:" not in lowered
    assert "api_secret" not in lowered
    assert '"ok-access-key":' not in lowered
    assert snapshot["REDACTED_PAYLOAD"]["data"][0]["pos"] == "1"
    assert snapshot["REDACTED_PAYLOAD"]["data"][0]["instId"] == TARGET_INSTRUMENT_ID
    assert snapshot["AUTH_PATH"]["SECRETREF_URI"] == REQUIRED_SECRETREF_URI
    assert snapshot["QUERY_PARAMETERS"] == {}
    assert snapshot["INSTID_FILTER_USED"] is False
    assert int((pack / "MANIFEST.sha256").stat().st_size) > 0
