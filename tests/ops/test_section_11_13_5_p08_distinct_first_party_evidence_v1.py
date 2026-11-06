"""P08 distinct first-party evidence GET-package tests. Recording transport only."""

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
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.classify_v1 import (
    classify_history_channel_v1,
    classify_risk_channel_v1,
    synthesize_package_v1,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_E_HTTP_OR_OKX_ERROR,
    EMPTY_DATA_IS_ZERO,
    ENDPOINT_ACCOUNT_POSITION_RISK,
    ENDPOINT_ACCOUNT_POSITIONS_HISTORY,
    ENDPOINT_ACCOUNT_POSITIONS_REUSED,
    EXPECTED_ORIGIN_MAIN_SHA,
    FALLBACK_REQUEST_ALLOWED,
    GET_ROLE_ACCOUNT_POSITION_RISK,
    GET_ROLE_POSID_POSITIONS,
    GET_ROLE_TARGET_HISTORY,
    GET_ROLE_TYPED_HISTORY,
    HISTORY_CLASS_EMPTY,
    HISTORY_EMPTY_IS_CURRENT_ZERO,
    HISTORY_EMPTY_IS_NEVER_HELD,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    NEXT_AUTHORITY_BOUNDARY_CHANNELS_UNRESOLVED,
    OWNER_GO,
    P09_WORK_ALLOWED,
    POSID_GET_REQUIRES_INDEPENDENT_PROOF,
    POSITIONS_INSTID_GET_ALLOWED,
    POSITIONS_UNFILTERED_GET_ALLOWED,
    POST_ALLOWED,
    REDIRECT_FOLLOW_ALLOWED,
    RESULT_CLASS_200_OKX_0,
    RETRY_ALLOWED,
    RISK_CLASS_POSDATA_EMPTY,
    RISK_POSDATA_EMPTY_IS_ZERO,
    TARGET_INST_TYPE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WHITELIST_MUTATION_ALLOWED,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.execute_v1 import (
    P08DistinctFirstPartyEvidenceError,
    execute_p08_distinct_first_party_evidence_gets_v1,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_p08_distinct_first_party_evidence_v1.query_grammar_v1 import (
    P08DistinctFirstPartyQueryGrammarError,
    build_account_position_risk_query_v1,
    build_proven_posid_positions_query_v1,
    build_target_positions_history_query_v1,
    build_typed_positions_history_query_v1,
)

EMPTY_BODY = b'{"code":"0","msg":"","data":[]}'
EMPTY_RISK_BODY = b'{"code":"0","msg":"","data":[{"adjEq":"","posData":[]}]}'
HISTORY_POSID_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"posId":"123456789","type":"2","uTime":"1710000000000"}]}'
)
RISK_TARGET_BODY = (
    b'{"code":"0","msg":"","data":[{"adjEq":"1","posData":[{"instId":'
    b'"SUI-USD_UM_XPERP-310404","pos":"1","posId":"123456789"}]}]}'
)
ZERO_POS_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"0","posSide":"net","mgnMode":"isolated","posId":"123456789"}]}'
)
NONZERO_POS_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"1","posSide":"net","mgnMode":"isolated","posId":"123456789"}]}'
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


def _run(tmp_path: Path, bodies: list[bytes], *, status: int = 200) -> dict:
    transport = _SequencedRecordingTransportV1(bodies=list(bodies), status_code=status)
    return execute_p08_distinct_first_party_evidence_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )


def test_standing_flags_remain_fail_closed() -> None:
    assert OWNER_GO == (
        "PEAK_TRADE_OWNER_GO_P08_DISTINCT_FIRST_PARTY_EVIDENCE_MAXIMUM_SAFE_LEVERAGE_V2"
    )
    assert THIS_SLICE == "11.13.5.P08_DISTINCT_FIRST_PARTY_EVIDENCE"
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert TARGET_INSTRUMENT_ID == DEFAULT_INSTRUMENT_ID
    assert TARGET_INST_TYPE == DEFAULT_INST_TYPE
    assert MAX_NETWORK_REQUEST_COUNT == 5
    assert MAX_HTTP_EXCHANGE_COUNT == 5
    assert RETRY_ALLOWED is False
    assert REDIRECT_FOLLOW_ALLOWED is False
    assert FALLBACK_REQUEST_ALLOWED is False
    assert POSITIONS_UNFILTERED_GET_ALLOWED is False
    assert POSITIONS_INSTID_GET_ALLOWED is False
    assert POSID_GET_REQUIRES_INDEPENDENT_PROOF is True
    assert WHITELIST_MUTATION_ALLOWED is False
    assert POST_ALLOWED is False
    assert P09_WORK_ALLOWED is False
    assert EMPTY_DATA_IS_ZERO is False
    assert HISTORY_EMPTY_IS_NEVER_HELD is False
    assert HISTORY_EMPTY_IS_CURRENT_ZERO is False
    assert RISK_POSDATA_EMPTY_IS_ZERO is False
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert CLAIMS["EXECUTION_READY"] is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert REQUIRED_SECRETREF_URI == (
        "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
    )
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_query_grammar_reuses_z2ch_and_z2v() -> None:
    target = build_target_positions_history_query_v1()
    assert target.endpoint == ENDPOINT_ACCOUNT_POSITIONS_HISTORY
    assert target.query["instType"] == "FUTURES"
    assert target.query["instId"] == TARGET_INSTRUMENT_ID
    assert target.empty_result_is_zero is False
    assert target.is_canonical_p08_authority is False
    typed = build_typed_positions_history_query_v1()
    assert "instId" not in typed.query
    assert typed.query["instType"] == "FUTURES"
    risk = build_account_position_risk_query_v1()
    assert risk.endpoint == ENDPOINT_ACCOUNT_POSITION_RISK
    assert risk.query == {"instType": "FUTURES"}
    assert risk.is_canonical_p08_authority is False
    posid = build_proven_posid_positions_query_v1(pos_id="123456789")
    assert posid.endpoint == ENDPOINT_ACCOUNT_POSITIONS_REUSED
    assert posid.query == {"posId": "123456789"}
    assert posid.pos_id_filter_present is True
    with pytest.raises(P08DistinctFirstPartyQueryGrammarError):
        build_proven_posid_positions_query_v1(pos_id="")


def test_history_empty_is_not_never_held_or_zero() -> None:
    classified = classify_history_channel_v1(
        result_class=RESULT_CLASS_200_OKX_0,
        payload={"code": "0", "data": [], "msg": ""},
    )
    assert classified["HISTORY_OBSERVATION_CLASS"] == HISTORY_CLASS_EMPTY
    assert classified["HISTORY_EMPTY_IS_NEVER_HELD"] is False
    assert classified["HISTORY_EMPTY_IS_CURRENT_ZERO"] is False
    assert classified["TARGET_POS_ID_PROVEN"] is False
    assert classified["CHANNEL_IS_CANONICAL_P08_AUTHORITY"] is False


def test_risk_empty_posdata_is_not_zero() -> None:
    classified = classify_risk_channel_v1(
        result_class=RESULT_CLASS_200_OKX_0,
        payload={"code": "0", "data": [{"adjEq": "", "posData": []}], "msg": ""},
    )
    assert classified["RISK_OBSERVATION_CLASS"] == RISK_CLASS_POSDATA_EMPTY
    assert classified["RISK_POSDATA_EMPTY_IS_ZERO"] is False
    assert classified["CHANNEL_IS_CANONICAL_P08_AUTHORITY"] is False
    assert classified["RISK_IS_CURRENT_STATE_CROSS_CHECK_ONLY"] is True


def test_synthesis_does_not_promote_history_to_current_zero() -> None:
    history = classify_history_channel_v1(
        result_class=RESULT_CLASS_200_OKX_0,
        payload={"code": "0", "data": [], "msg": ""},
    )
    risk = classify_risk_channel_v1(
        result_class=RESULT_CLASS_200_OKX_0,
        payload={"code": "0", "data": [{"adjEq": "", "posData": []}], "msg": ""},
    )
    package = synthesize_package_v1(history=history, risk=risk, positions=None)
    assert package["TARGET_POSITION_ZERO_PROVEN"] is False
    assert package["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert package["P08_CLOSED"] is False
    assert package["HISTORY_PROMOTED_TO_CURRENT_STATE"] is False
    assert package["RISK_PROMOTED_TO_CANONICAL_AUTHORITY"] is False
    assert package["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO


def test_wrong_owner_go_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(P08DistinctFirstPartyEvidenceError, match="OWNER_GO_MISMATCH"):
        execute_p08_distinct_first_party_evidence_gets_v1(
            owner_go="PEAK_TRADE_OWNER_GO_P08_EMPTY_DATA_NOT_ZERO_MAXIMUM_SAFE_LEVERAGE_V1",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=_SequencedRecordingTransportV1(bodies=[EMPTY_BODY]),
        )


def test_wrong_origin_main_sha_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(P08DistinctFirstPartyEvidenceError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_p08_distinct_first_party_evidence_gets_v1(
            owner_go=OWNER_GO,
            origin_main_sha="975fcf72e8cedcecf614bbf1d6a11b0f97dcf374",
            evidence_root=tmp_path,
            transport=_SequencedRecordingTransportV1(bodies=[EMPTY_BODY]),
        )


def test_empty_history_and_risk_do_not_issue_posid_get(tmp_path: Path) -> None:
    result = _run(tmp_path, [EMPTY_BODY, EMPTY_BODY, EMPTY_RISK_BODY])
    summary = result["summary"]
    assert summary["RESULT_CLASS"] == RESULT_CLASS_200_OKX_0
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    assert summary["POSITION_STATE_OBSERVED"] is False
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["TARGET_POS_ID_PROVEN"] is False
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 3
    assert summary["GET_ROLES_PERFORMED"] == [
        GET_ROLE_TARGET_HISTORY,
        GET_ROLE_TYPED_HISTORY,
        GET_ROLE_ACCOUNT_POSITION_RISK,
    ]
    assert summary["POST_COUNT"] == 0
    assert summary["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert summary["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY_CHANNELS_UNRESOLVED
    assert summary["EQUIVALENT_ACCOUNT_POSITIONS_EMPTY_PROBE_REPEATED"] is False
    pack = Path(result["EVIDENCE_PACK"])
    assert (pack / "GET_TARGET_HISTORY.raw.json").is_file()
    assert (pack / "GET_TYPED_HISTORY.raw.json").is_file()
    assert (pack / "GET_ACCOUNT_POSITION_RISK.raw.json").is_file()
    assert not (pack / "GET_POSID_POSITIONS.raw.json").exists()
    raw1 = json.loads((pack / "GET_TARGET_HISTORY.raw.json").read_text(encoding="utf-8"))
    assert raw1["BODY_WAS_JSON_RESERIALIZED"] is False
    assert raw1["BODY_UTF8_EXACT"] == EMPTY_BODY.decode("utf-8")
    assert raw1["ENDPOINT_PATH"] == ENDPOINT_ACCOUNT_POSITIONS_HISTORY
    raw_risk = json.loads((pack / "GET_ACCOUNT_POSITION_RISK.raw.json").read_text(encoding="utf-8"))
    assert raw_risk["ENDPOINT_PATH"] == ENDPOINT_ACCOUNT_POSITION_RISK
    assert result["adjudication"]["HISTORY_EMPTY_IS_NEVER_HELD"] is False
    assert result["adjudication"]["HISTORY_EMPTY_IS_CURRENT_ZERO"] is False
    assert result["adjudication"]["RISK_POSDATA_EMPTY_IS_ZERO"] is False


def test_history_posid_then_risk_then_nonzero_posid_get_closes_p08(tmp_path: Path) -> None:
    result = _run(tmp_path, [HISTORY_POSID_BODY, EMPTY_RISK_BODY, NONZERO_POS_BODY])
    summary = result["summary"]
    assert summary["GET_ROLES_PERFORMED"] == [
        GET_ROLE_TARGET_HISTORY,
        GET_ROLE_ACCOUNT_POSITION_RISK,
        GET_ROLE_POSID_POSITIONS,
    ]
    assert summary["GET_REQUEST_COUNT"] == 3
    assert summary["TARGET_POS_ID_PROVEN"] is True
    assert summary["TARGET_POS_ID"] == "123456789"
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_A_TARGET_NONZERO
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is True
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is True
    assert summary["HISTORY_PROMOTED_TO_CURRENT_STATE"] is False
    assert GET_ROLE_TYPED_HISTORY not in summary["GET_ROLES_PERFORMED"]
    pack = Path(result["EVIDENCE_PACK"])
    raw_pos = json.loads((pack / "GET_POSID_POSITIONS.raw.json").read_text(encoding="utf-8"))
    assert raw_pos["QUERY_PARAMETERS"] == {"posId": "123456789"}
    assert raw_pos["ENDPOINT_PATH"] == ENDPOINT_ACCOUNT_POSITIONS_REUSED


def test_history_posid_then_empty_posid_get_is_not_zero(tmp_path: Path) -> None:
    result = _run(tmp_path, [HISTORY_POSID_BODY, EMPTY_RISK_BODY, EMPTY_BODY])
    summary = result["summary"]
    assert summary["TARGET_POS_ID_PROVEN"] is True
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO


def test_history_posid_then_zero_row_proves_zero_and_does_not_close(tmp_path: Path) -> None:
    result = _run(tmp_path, [HISTORY_POSID_BODY, EMPTY_RISK_BODY, ZERO_POS_BODY])
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_B_TARGET_ZERO
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is True
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False


def test_case_e_50110_does_not_issue_followup_gets(tmp_path: Path) -> None:
    result = _run(tmp_path, [FAIL_50110_BODY], status=401)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_E_HTTP_OR_OKX_ERROR
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["GET_ROLES_PERFORMED"] == [GET_ROLE_TARGET_HISTORY]


def test_risk_target_posid_without_history_still_authorizes_posid_get(tmp_path: Path) -> None:
    result = _run(tmp_path, [EMPTY_BODY, EMPTY_BODY, RISK_TARGET_BODY, NONZERO_POS_BODY])
    summary = result["summary"]
    assert summary["GET_ROLES_PERFORMED"] == [
        GET_ROLE_TARGET_HISTORY,
        GET_ROLE_TYPED_HISTORY,
        GET_ROLE_ACCOUNT_POSITION_RISK,
        GET_ROLE_POSID_POSITIONS,
    ]
    assert summary["P08_CLOSED"] is True
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is True
    assert summary["RISK_PROMOTED_TO_CANONICAL_AUTHORITY"] is False
