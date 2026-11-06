"""P08 read-only closure GET-package tests. Recording transport only."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_ORDERS_ALGO_PENDING,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_TRADE_FILLS,
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
    UrllibLiveCanaryTransportV1,
    sanitize_redirect_location_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.census_v1 import (
    CANDIDATES,
    DISPOSITION_DISTINCT,
    DISPOSITION_ID_NOT_PROVEN,
    DISPOSITION_INSUFFICIENT,
    DISPOSITION_REDUNDANT,
    census_payload_v1,
    distinct_unconsumed_candidates_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.classify_v1 import (
    classify_identifier_channel_v1,
    synthesize_read_only_closure_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.constants_v1 import (
    AUTHORIZED_HOST,
    CASE_A_TARGET_NONZERO,
    CASE_B_TARGET_ZERO,
    CASE_C_EMPTY_DATA_NOT_ZERO,
    CASE_E_HTTP_OR_OKX_ERROR,
    CLOSURE_RESULT_CLOSED_NONZERO,
    CLOSURE_RESULT_READ_ONLY_EXHAUSTED,
    EMPTY_DATA_IS_ZERO,
    EXPECTED_ORIGIN_MAIN_SHA,
    FALLBACK_REQUEST_ALLOWED,
    FILLS_EMPTY_IS_CURRENT_ZERO,
    FILLS_EMPTY_IS_NEVER_HELD,
    GET_ROLE_ALGO_CONDITIONAL_OCO,
    GET_ROLE_ALGO_MOVE_ORDER_STOP,
    GET_ROLE_ALGO_TRIGGER,
    GET_ROLE_FILLS,
    GET_ROLE_ORDERS_HISTORY,
    GET_ROLE_ORDERS_PENDING,
    GET_ROLE_POSID_POSITIONS,
    ID_CLASS_EMPTY,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    NEXT_AUTHORITY_BOUNDARY_READ_ONLY_EXHAUSTED,
    ORDERS_EMPTY_IS_CURRENT_ZERO,
    ORDERS_EMPTY_IS_NEVER_HELD,
    OWNER_GO,
    P09_WORK_ALLOWED,
    POSID_GET_REQUIRES_INDEPENDENT_PROOF,
    POSITIONS_HISTORY_GET_ALLOWED,
    POSITIONS_INSTID_GET_ALLOWED,
    POSITIONS_UNFILTERED_GET_ALLOWED,
    POST_ALLOWED,
    REDIRECT_FOLLOW_ALLOWED,
    RESULT_CLASS_200_OKX_0,
    RETRY_ALLOWED,
    TARGET_INST_TYPE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WHITELIST_MUTATION_ALLOWED,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.execute_v1 import (
    P08ReadOnlyClosureError,
    execute_p08_read_only_closure_gets_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.persist_claims_v1 import CLAIMS
from src.ops.section_11_13_5_p08_read_only_closure_v1.query_grammar_v1 import (
    P08ReadOnlyClosureQueryGrammarError,
    build_proven_posid_positions_query_v1,
    build_target_algo_pending_path_v1,
    build_target_fills_query_v1,
    build_target_orders_history_query_v1,
    build_target_orders_pending_query_v1,
)

EMPTY_BODY = b'{"code":"0","msg":"","data":[]}'
FAIL_50110_BODY = (
    b'{"code":"50110","msg":"Your IP 203.0.113.50 is not included in your API '
    b'key\'s IP whitelist.","data":[]}'
)
ORDER_POSID_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"ordId":"111","posId":"123456789","state":"live"}]}'
)
ZERO_POS_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"0","posSide":"net","mgnMode":"isolated","posId":"123456789"}]}'
)
NONZERO_POS_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"1","posSide":"net","mgnMode":"isolated","posId":"123456789"}]}'
)

_IDENTIFIER_EMPTY_BODIES = [
    EMPTY_BODY,
    EMPTY_BODY,
    EMPTY_BODY,
    EMPTY_BODY,
    EMPTY_BODY,
    EMPTY_BODY,
]


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
    return execute_p08_read_only_closure_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )


def test_standing_flags_remain_fail_closed() -> None:
    assert OWNER_GO == ("PEAK_TRADE_OWNER_GO_P08_READ_ONLY_CLOSURE_MAXIMUM_SAFE_LEVERAGE_V3")
    assert THIS_SLICE == "11.13.5.P08_READ_ONLY_CLOSURE"
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert TARGET_INSTRUMENT_ID == DEFAULT_INSTRUMENT_ID
    assert TARGET_INST_TYPE == DEFAULT_INST_TYPE
    assert MAX_NETWORK_REQUEST_COUNT == 8
    assert MAX_HTTP_EXCHANGE_COUNT == 8
    assert RETRY_ALLOWED is False
    assert REDIRECT_FOLLOW_ALLOWED is False
    assert FALLBACK_REQUEST_ALLOWED is False
    assert POSITIONS_UNFILTERED_GET_ALLOWED is False
    assert POSITIONS_INSTID_GET_ALLOWED is False
    assert POSITIONS_HISTORY_GET_ALLOWED is False
    assert POSID_GET_REQUIRES_INDEPENDENT_PROOF is True
    assert WHITELIST_MUTATION_ALLOWED is False
    assert POST_ALLOWED is False
    assert P09_WORK_ALLOWED is False
    assert EMPTY_DATA_IS_ZERO is False
    assert ORDERS_EMPTY_IS_NEVER_HELD is False
    assert ORDERS_EMPTY_IS_CURRENT_ZERO is False
    assert FILLS_EMPTY_IS_NEVER_HELD is False
    assert FILLS_EMPTY_IS_CURRENT_ZERO is False
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert CLAIMS["EXECUTION_READY"] is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert REQUIRED_SECRETREF_URI == (
        "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
    )
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_census_marks_consumed_and_distinct_paths() -> None:
    census = census_payload_v1()
    assert census["P08_READ_ONLY_CANDIDATE_COUNT"] == len(CANDIDATES)
    assert census["P08_READ_ONLY_CANDIDATE_COUNT"] == 21
    distinct = distinct_unconsumed_candidates_v1()
    assert census["P08_DISTINCT_UNCONSUMED_CANDIDATE_COUNT"] == 4
    assert [item["ID"] for item in distinct] == [
        "TARGET_ORDERS_PENDING",
        "TARGET_ORDERS_HISTORY",
        "TARGET_ORDERS_ALGO_PENDING",
        "TARGET_FILLS",
    ]
    by_id = {item["ID"]: item for item in CANDIDATES}
    assert by_id["UNFILTERED_ACCOUNT_POSITIONS"]["DISPOSITION"] == DISPOSITION_REDUNDANT
    assert by_id["TARGET_POSITIONS_HISTORY"]["DISPOSITION"] == DISPOSITION_REDUNDANT
    assert by_id["ACCOUNT_POSITION_RISK_FUTURES"]["DISPOSITION"] == DISPOSITION_REDUNDANT
    assert by_id["ACCOUNT_BALANCE"]["DISPOSITION"] == DISPOSITION_INSUFFICIENT
    assert by_id["POSID_ACCOUNT_POSITIONS"]["DISPOSITION"] == DISPOSITION_ID_NOT_PROVEN
    assert by_id["TARGET_ORDERS_PENDING"]["DISPOSITION"] == DISPOSITION_DISTINCT
    assert by_id["TARGET_FILLS"]["CAN_SATISFY_NONZERO"] is False
    assert by_id["POSID_ACCOUNT_POSITIONS"]["CAN_SATISFY_NONZERO"] is True


def test_query_grammar_binds_target_and_refuses_empty_posid() -> None:
    pending = build_target_orders_pending_query_v1()
    assert pending.endpoint == ENDPOINT_ORDERS_PENDING
    assert pending.query == {"instType": "FUTURES", "instId": TARGET_INSTRUMENT_ID}
    assert pending.empty_result_is_zero is False
    assert pending.is_canonical_p08_authority is False
    history = build_target_orders_history_query_v1()
    assert history.endpoint == ENDPOINT_ORDERS_HISTORY
    assert history.query["limit"] == "100"
    fills = build_target_fills_query_v1()
    assert fills.endpoint == ENDPOINT_TRADE_FILLS
    algo = build_target_algo_pending_path_v1(ord_type="conditional,oco")
    assert algo.startswith(ENDPOINT_ORDERS_ALGO_PENDING + "?")
    assert "ordType=conditional,oco" in algo
    assert f"instId={TARGET_INSTRUMENT_ID}" in algo
    posid = build_proven_posid_positions_query_v1(pos_id="123456789")
    assert posid.endpoint == ENDPOINT_ACCOUNT_POSITIONS
    assert posid.query == {"posId": "123456789"}
    with pytest.raises(P08ReadOnlyClosureQueryGrammarError):
        build_proven_posid_positions_query_v1(pos_id="")


def test_identifier_empty_is_not_never_held_or_zero() -> None:
    classified = classify_identifier_channel_v1(
        channel=GET_ROLE_ORDERS_PENDING,
        result_class=RESULT_CLASS_200_OKX_0,
        payload={"code": "0", "data": [], "msg": ""},
    )
    assert classified["IDENTIFIER_OBSERVATION_CLASS"] == ID_CLASS_EMPTY
    assert classified["EMPTY_IS_NEVER_HELD"] is False
    assert classified["EMPTY_IS_CURRENT_ZERO"] is False
    assert classified["TARGET_POS_ID_PROVEN"] is False
    assert classified["CHANNEL_IS_CANONICAL_P08_AUTHORITY"] is False


def test_synthesis_does_not_promote_empty_orders_to_current_zero() -> None:
    pending = classify_identifier_channel_v1(
        channel=GET_ROLE_ORDERS_PENDING,
        result_class=RESULT_CLASS_200_OKX_0,
        payload={"code": "0", "data": [], "msg": ""},
    )
    package = synthesize_read_only_closure_v1(
        identifier_channels=(pending,),
        positions=None,
    )
    assert package["TARGET_POSITION_ZERO_PROVEN"] is False
    assert package["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert package["P08_CLOSED"] is False
    assert package["P08_READ_ONLY_CLOSURE_RESULT"] == CLOSURE_RESULT_READ_ONLY_EXHAUSTED
    assert package["HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE"] is False
    assert package["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO


def test_urllib_transport_without_wire_flag_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(P08ReadOnlyClosureError, match="PRODUCTIVE_WIRE_DISABLED"):
        execute_p08_read_only_closure_gets_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=UrllibLiveCanaryTransportV1(wire_send_enabled=False),
        )


def test_wrong_owner_go_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(P08ReadOnlyClosureError, match="OWNER_GO_MISMATCH"):
        execute_p08_read_only_closure_gets_v1(
            owner_go="PEAK_TRADE_OWNER_GO_P08_DISTINCT_FIRST_PARTY_EVIDENCE_MAXIMUM_SAFE_LEVERAGE_V2",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=_SequencedRecordingTransportV1(bodies=[EMPTY_BODY]),
        )


def test_wrong_origin_main_sha_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(P08ReadOnlyClosureError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_p08_read_only_closure_gets_v1(
            owner_go=OWNER_GO,
            origin_main_sha="fd22be6386894e3982aa83ebd4e7c0365038bcf0",
            evidence_root=tmp_path,
            transport=_SequencedRecordingTransportV1(bodies=[EMPTY_BODY]),
        )


def test_empty_identifier_channels_do_not_issue_posid_get(tmp_path: Path) -> None:
    result = _run(tmp_path, list(_IDENTIFIER_EMPTY_BODIES))
    summary = result["summary"]
    assert summary["RESULT_CLASS"] == RESULT_CLASS_200_OKX_0
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["TARGET_POS_ID_PROVEN"] is False
    assert summary["P08_CLOSED"] is False
    assert summary["P08_READ_ONLY_CLOSURE_RESULT"] == CLOSURE_RESULT_READ_ONLY_EXHAUSTED
    assert summary["GET_REQUEST_COUNT"] == 6
    assert summary["POSID_POSITIONS_GET_PERFORMED"] is False
    assert summary["GET_ROLES_PERFORMED"] == [
        GET_ROLE_ORDERS_PENDING,
        GET_ROLE_ORDERS_HISTORY,
        GET_ROLE_ALGO_CONDITIONAL_OCO,
        GET_ROLE_ALGO_TRIGGER,
        GET_ROLE_ALGO_MOVE_ORDER_STOP,
        GET_ROLE_FILLS,
    ]
    assert summary["POST_COUNT"] == 0
    assert summary["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY_READ_ONLY_EXHAUSTED
    pack = Path(result["EVIDENCE_PACK"])
    assert (pack / "GET_ORDERS_PENDING.raw.json").is_file()
    assert (pack / "GET_ORDERS_HISTORY.raw.json").is_file()
    assert (pack / "GET_ALGO_PENDING_CONDITIONAL_OCO.raw.json").is_file()
    assert (pack / "GET_ALGO_PENDING_TRIGGER.raw.json").is_file()
    assert (pack / "GET_ALGO_PENDING_MOVE_ORDER_STOP.raw.json").is_file()
    assert (pack / "GET_FILLS.raw.json").is_file()
    assert not (pack / "GET_POSID_POSITIONS.raw.json").exists()
    raw_pending = json.loads((pack / "GET_ORDERS_PENDING.raw.json").read_text(encoding="utf-8"))
    assert raw_pending["BODY_WAS_JSON_RESERIALIZED"] is False
    assert raw_pending["BODY_UTF8_EXACT"] == EMPTY_BODY.decode("utf-8")
    assert raw_pending["ENDPOINT_PATH"] == ENDPOINT_ORDERS_PENDING
    assert raw_pending["QUERY_PARAMETERS"]["instId"] == TARGET_INSTRUMENT_ID
    assert "posId" not in json.dumps(raw_pending)


def test_unique_posid_from_pending_issues_positions_get_and_closes(tmp_path: Path) -> None:
    bodies = [
        ORDER_POSID_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        NONZERO_POS_BODY,
    ]
    result = _run(tmp_path, bodies)
    summary = result["summary"]
    assert summary["GET_ROLES_PERFORMED"][-1] == GET_ROLE_POSID_POSITIONS
    assert summary["GET_REQUEST_COUNT"] == 7
    assert summary["TARGET_POS_ID_PROVEN"] is True
    assert summary["TARGET_POS_ID"] == "123456789"
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_A_TARGET_NONZERO
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is True
    assert summary["P08_CLOSED"] is True
    assert summary["P08_READ_ONLY_CLOSURE_RESULT"] == CLOSURE_RESULT_CLOSED_NONZERO
    assert summary["HISTORICAL_OR_INDIRECT_PROMOTED_TO_CURRENT_STATE"] is False


def test_unique_posid_then_empty_positions_is_not_zero(tmp_path: Path) -> None:
    bodies = [
        ORDER_POSID_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
    ]
    result = _run(tmp_path, bodies)
    summary = result["summary"]
    assert summary["TARGET_POS_ID_PROVEN"] is True
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_C_EMPTY_DATA_NOT_ZERO
    assert summary["P08_READ_ONLY_CLOSURE_RESULT"] == CLOSURE_RESULT_READ_ONLY_EXHAUSTED


def test_unique_posid_then_zero_row_does_not_close(tmp_path: Path) -> None:
    bodies = [
        ORDER_POSID_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        EMPTY_BODY,
        ZERO_POS_BODY,
    ]
    result = _run(tmp_path, bodies)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_B_TARGET_ZERO
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is True
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["P08_CLOSED"] is False


def test_never_invents_posid_or_posts(tmp_path: Path) -> None:
    transport = _SequencedRecordingTransportV1(bodies=list(_IDENTIFIER_EMPTY_BODIES))
    execute_p08_read_only_closure_gets_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    assert all(call.method == "GET" for call in transport.calls)
    assert len(transport.calls) == 6
    assert all("posId=" not in call.endpoint for call in transport.calls)
    assert all("/account/positions?" not in call.endpoint for call in transport.calls)
    assert all("/account/positions-history" not in call.endpoint for call in transport.calls)
    assert all("/account/account-position-risk" not in call.endpoint for call in transport.calls)


def test_identifier_50110_does_not_invent_posid(tmp_path: Path) -> None:
    result = _run(tmp_path, [FAIL_50110_BODY] * 6, status=401)
    summary = result["summary"]
    assert summary["POSITION_OBSERVATION_CLASS"] == CASE_E_HTTP_OR_OKX_ERROR
    assert summary["P08_CLOSED"] is False
    assert summary["GET_REQUEST_COUNT"] == 6
    assert summary["TARGET_POS_ID_PROVEN"] is False
    assert summary["POSID_POSITIONS_GET_PERFORMED"] is False
    assert GET_ROLE_POSID_POSITIONS not in summary["GET_ROLES_PERFORMED"]
