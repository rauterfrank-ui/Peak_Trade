"""Post-whitelist one-shot private auth GET tests. Recording transport only."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
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
from src.ops.section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1.constants_v1 import (
    AUTH_SUCCESS_PROVEN,
    AUTHORITY_EXPANSION_BEYOND_THIS_GET,
    AUTHORIZED_HOST,
    BLOCKER_CLEARED,
    BLOCKER_OPEN,
    CAPITAL_MOVEMENT_ALLOWED,
    CLEARANCE_PROVEN,
    DEFAULT_MAX_RETRIES,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FALLBACK_REQUEST_ALLOWED,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    NEXT_AUTHORITY_BOUNDARY_CASE_A,
    NEXT_AUTHORITY_BOUNDARY_CASE_B,
    NEXT_AUTHORITY_BOUNDARY_CASE_C,
    OWNER_GO,
    P08_OBSERVATION_ALLOWED,
    POST_ALLOWED,
    PREDECESSOR_SLICE,
    REDIRECT_FOLLOW_ALLOWED,
    RESULT_CLASS_200_OKX_0,
    RESULT_CLASS_401_50110,
    RESULT_CLASS_OTHER,
    RETRY_ALLOWED,
    SECOND_GET_ALLOWED,
    THIS_SLICE,
    TRANSFER_ALLOWED,
    WHITELIST_MUTATION_ALLOWED,
)
from src.ops.section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1.execute_v1 import (
    PostWhitelistPrivateAuthAttestationError,
    execute_single_post_whitelist_private_auth_attestation_get_v1,
)
from src.ops.section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1.persist_claims_v1 import (
    CLAIMS,
)

SUCCESS_BODY = (
    b'{"code":"0","msg":"","data":[{"acctLv":"2","posMode":"net_mode","uid":"redacted"}]}'
)
FAIL_50110_BODY = (
    b'{"code":"50110","msg":"Your IP 203.0.113.50 is not included in your API '
    b'key\'s 11111111-2222-3333-4444-555555555555 IP whitelist.","data":[]}'
)
OTHER_BODY = b'{"code":"50014","msg":"Invalid sign","data":[]}'


def test_standing_flags_remain_fail_closed() -> None:
    assert OWNER_GO.endswith("POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_V1")
    assert THIS_SLICE == "11.13.5.POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION"
    assert PREDECESSOR_SLICE == "11.13.5.POST_Z2DS_50110_WHITELIST_ADD_FROM_CAPTURE"
    assert ENDPOINT == "/api/v5/account/config"
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert MAX_NETWORK_REQUEST_COUNT == 1
    assert MAX_HTTP_EXCHANGE_COUNT == 1
    assert DEFAULT_MAX_RETRIES == 0
    assert RETRY_ALLOWED is False
    assert REDIRECT_FOLLOW_ALLOWED is False
    assert FALLBACK_REQUEST_ALLOWED is False
    assert SECOND_GET_ALLOWED is False
    assert WHITELIST_MUTATION_ALLOWED is False
    assert P08_OBSERVATION_ALLOWED is False
    assert CLAIMS["RETRY_ALLOWED"] is False
    assert CLAIMS["WHITELIST_MUTATION_PERFORMED"] is False
    assert CLAIMS["P08_CLOSED_INFERRED"] is False
    assert CLAIMS["EXECUTION_READY"] is False
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert CLAIMS["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert CLAIMS["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert TRANSFER_ALLOWED is False
    assert POST_ALLOWED is False
    assert CAPITAL_MOVEMENT_ALLOWED is False
    assert AUTHORITY_EXPANSION_BEYOND_THIS_GET is False
    assert REQUIRED_SECRETREF_URI == (
        "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
    )
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS


def test_wrong_owner_go_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(PostWhitelistPrivateAuthAttestationError, match="OWNER_GO_MISMATCH"):
        execute_single_post_whitelist_private_auth_attestation_get_v1(
            owner_go="PEAK_TRADE_OWNER_GO_OKX_EEA_PRIVATE_GET_CURRENT_50110_EGRESS_CAPTURE_V1",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=SUCCESS_BODY),
        )


def test_wrong_origin_main_sha_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(PostWhitelistPrivateAuthAttestationError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_single_post_whitelist_private_auth_attestation_get_v1(
            owner_go=OWNER_GO,
            origin_main_sha="36e8d281d91c0423a22da3bfded5c6be803b17b5",
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=SUCCESS_BODY),
        )


def test_recording_http_200_okx_0_does_not_close_p08(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=SUCCESS_BODY)
    result = execute_single_post_whitelist_private_auth_attestation_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    summary = result["summary"]
    assert summary["RESULT_CLASS"] == RESULT_CLASS_200_OKX_0
    assert summary["PRIVATE_API_AUTH_SUCCESS"] == AUTH_SUCCESS_PROVEN
    assert summary["RUNTIME_50110_CLEARANCE"] == CLEARANCE_PROVEN
    assert summary["PRIVATE_AUTH_BLOCKER_50110"] == BLOCKER_CLEARED
    assert summary["OKX_REPORTED_EGRESS_IPV4"] == "NONE"
    assert summary["PREREQUISITE_08_CLOSED"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["POSITION_STATE_OBSERVED"] is False
    assert summary["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert summary["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY_CASE_A
    assert summary["OWNER_GO_CONSUMED"] is True
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["POST_COUNT"] == 0
    assert summary["WRITE_REQUEST_COUNT"] == 0
    snapshot_text = (
        Path(result["EVIDENCE_PACK"])
        .joinpath("GET_SNAPSHOT.sanitized.json")
        .read_text(encoding="utf-8")
    )
    assert "acctLv" not in snapshot_text
    assert "net_mode" not in snapshot_text
    assert len(transport.calls) == 1
    assert transport.calls[0].method == "GET"
    assert transport.calls[0].endpoint == ENDPOINT


def test_recording_http_401_50110_keeps_blocker_open(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(status_code=401, body=FAIL_50110_BODY)
    result = execute_single_post_whitelist_private_auth_attestation_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    summary = result["summary"]
    assert summary["HTTP_STATUS"] == 401
    assert summary["OKX_CODE"] == "50110"
    assert summary["RESULT_CLASS"] == RESULT_CLASS_401_50110
    assert summary["PRIVATE_API_AUTH_SUCCESS"] is False
    assert summary["RUNTIME_50110_CLEARANCE"] is False
    assert summary["PRIVATE_AUTH_BLOCKER_50110"] == BLOCKER_OPEN
    assert summary["OKX_REPORTED_EGRESS_IPV4"] == "203.0.113.50"
    assert summary["FORENSIC_RAW_OKX_REPORTED_EGRESS_IPV4"] == "203.0.113.50"
    assert summary["WHITELIST_MUTATION_PERFORMED"] is False
    assert summary["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY_CASE_B
    snapshot_text = (
        Path(result["EVIDENCE_PACK"])
        .joinpath("GET_SNAPSHOT.sanitized.json")
        .read_text(encoding="utf-8")
    )
    assert "11111111-2222-3333-4444-555555555555" not in snapshot_text
    assert "<REDACTED_KEY_ID>" in snapshot_text


def test_recording_other_result_fail_closed_no_root_cause(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(status_code=401, body=OTHER_BODY)
    result = execute_single_post_whitelist_private_auth_attestation_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    summary = result["summary"]
    assert summary["RESULT_CLASS"] == RESULT_CLASS_OTHER
    assert summary["PRIVATE_API_AUTH_SUCCESS"] == "NOT_PROVEN"
    assert summary["RUNTIME_50110_CLEARANCE"] == "NOT_PROVEN"
    assert summary["PRIVATE_AUTH_RESULT"] == RESULT_CLASS_OTHER
    assert summary["FAIL_CLOSED_RECORD"] is True
    assert summary["DO_NOT_INFER_ROOT_CAUSE"] is True
    assert summary["ROOT_CAUSE"] == "UNPROVEN"
    assert summary["OKX_REPORTED_EGRESS_IPV4"] == "NOT_OBSERVED"
    assert summary["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY_CASE_C
    assert summary["PREREQUISITE_08_CLOSED"] is False
