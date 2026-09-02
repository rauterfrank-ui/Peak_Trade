"""§11.13.5.Z2DL one-shot private Auth GET tests. Recording transport only."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    REQUIRED_SECRETREF_URI,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_z2dl_post_remediation_single_private_auth_get_v1.constants_v1 import (
    AUTHORITY_EXPANSION_BEYOND_THIS_GET,
    AUTHORIZED_HOST,
    CAPITAL_MOVEMENT_ALLOWED,
    DEFAULT_MAX_RETRIES,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FALLBACK_REQUEST_ALLOWED,
    MAX_HTTP_EXCHANGE_COUNT,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    POST_ALLOWED,
    PREDECESSOR_SLICE,
    REDIRECT_FOLLOW_ALLOWED,
    RETRY_ALLOWED,
    SECOND_GET_ALLOWED,
    THIS_SLICE,
    TRANSFER_ALLOWED,
    WHITELIST_MUTATION_ALLOWED,
)
from src.ops.section_11_13_5_z2dl_post_remediation_single_private_auth_get_v1.execute_v1 import (
    Z2DLPrivateAuthGetError,
    execute_single_actual_private_auth_get_v1,
)
from src.ops.section_11_13_5_z2dl_post_remediation_single_private_auth_get_v1.persist_claims_v1 import (
    CLAIMS,
)

SUCCESS_BODY = (
    b'{"code":"0","msg":"","data":[{"acctLv":"2","posMode":"net_mode","uid":"redacted"}]}'
)
FAIL_50110_BODY = (
    b'{"code":"50110","msg":"Your IP is not included in your API key IP whitelist.","data":[]}'
)


def test_standing_flags_remain_fail_closed() -> None:
    assert OWNER_GO.endswith("Z2DL_POST_REMEDIATION_SINGLE_PRIVATE_AUTH_GET_V1")
    assert THIS_SLICE == "11.13.5.Z2DL"
    assert PREDECESSOR_SLICE == "11.13.5.Z2DK"
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
    assert CLAIMS["RETRY_ALLOWED"] is False
    assert CLAIMS["SECRETREF_CHANGE_ALLOWED"] is False
    assert CLAIMS["EXECUTION_READY"] is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert CLAIMS["LIVE_AUTHORIZED"] is False
    assert CLAIMS["CANARY_AUTHORIZED"] is False
    assert CLAIMS["SUBMIT_UNLOCKED"] is False
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert TRANSFER_ALLOWED is False
    assert POST_ALLOWED is False
    assert CAPITAL_MOVEMENT_ALLOWED is False
    assert AUTHORITY_EXPANSION_BEYOND_THIS_GET is False
    assert REQUIRED_SECRETREF_URI == (
        "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
    )


def test_wrong_owner_go_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(Z2DLPrivateAuthGetError, match="OWNER_GO_MISMATCH"):
        execute_single_actual_private_auth_get_v1(
            owner_go="PEAK_TRADE_OWNER_GO_Z2DK_POST_WHITELIST_SINGLE_PRIVATE_AUTH_GET_V1",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=SUCCESS_BODY),
        )


def test_wrong_origin_main_sha_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(Z2DLPrivateAuthGetError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_single_actual_private_auth_get_v1(
            owner_go=OWNER_GO,
            origin_main_sha="cd070c4c16c31f4e40bdeb315cf909f62b441e1c",
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=SUCCESS_BODY),
        )


def test_recording_http_401_50110_persists_then_fail_closed(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(status_code=401, body=FAIL_50110_BODY)
    with pytest.raises(Z2DLPrivateAuthGetError, match="PRIVATE_AUTH_GET_NOT_SUCCESS"):
        execute_single_actual_private_auth_get_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=transport,
        )
    packs = [path for path in tmp_path.iterdir() if path.is_dir()]
    assert len(packs) == 1
    summary = (packs[0] / "SUMMARY.json").read_text(encoding="utf-8")
    snapshot = (packs[0] / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    assert '"HTTP_STATUS": 401' in summary
    assert '"OKX_CODE": "50110"' in summary
    assert '"PRIVATE_API_AUTH_SUCCESS": false' in summary
    assert '"RUNTIME_50110_CLEARANCE": false' in summary
    assert '"ROOT_CAUSE": "UNPROVEN"' in summary
    assert '"GET_REQUEST_COUNT": 1' in summary
    assert '"POST_COUNT": 0' in summary
    assert '"REDIRECT_FOLLOWED": false' in summary
    assert '"SECRET_VALUES_INCLUDED": false' in snapshot
    assert '"DATA_VALUES_INCLUDED": false' in snapshot
    assert '"FUNDING_GET_PERFORMED": false' in snapshot
    assert '"POSITIONS_GET_PERFORMED": false' in snapshot
    assert len(transport.calls) == 1
    assert transport.calls[0].method == "GET"
    assert transport.calls[0].endpoint == ENDPOINT


def test_recording_http_200_code_zero_is_auth_success_not_execution(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=SUCCESS_BODY)
    result = execute_single_actual_private_auth_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    assert result["MANIFEST_VERIFY_RC"] == 0
    summary = result["summary"]
    assert summary["HTTP_STATUS"] == 200
    assert summary["OKX_CODE"] == "0"
    assert summary["PRIVATE_API_AUTH_SUCCESS"] is True
    assert summary["AUTHENTICATED_PRIVATE_API_REACHABILITY_PROVEN"] is True
    assert summary["RUNTIME_50110_CLEARANCE"] is True
    assert summary["EXECUTION_READY"] is False
    assert summary["SUBMIT_UNLOCKED"] is False
    assert summary["CANARY_AUTHORIZED"] is False
    assert summary["LIVE_AUTHORIZED"] is False
    assert summary["FUNDING_STATE"] == "UNPROVEN"
    assert summary["POSITION_STATE"] == "UNPROVEN"
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["POST_COUNT"] == 0
    assert summary["REDIRECT_FOLLOWED"] is False
    assert len(transport.calls) == 1
    snapshot_text = (
        Path(result["EVIDENCE_PACK"])
        .joinpath("GET_SNAPSHOT.sanitized.json")
        .read_text(encoding="utf-8")
    )
    lowered = snapshot_text.lower()
    assert '"ok-access-key"' not in lowered
    assert "api_secret" not in lowered
    assert "plaintext:" not in lowered
    assert "acctLv" not in snapshot_text
    assert "net_mode" not in snapshot_text
    assert '"DATA_VALUES_INCLUDED": false' in snapshot_text
    assert '"DATA_ROW_COUNT": 1' in snapshot_text
