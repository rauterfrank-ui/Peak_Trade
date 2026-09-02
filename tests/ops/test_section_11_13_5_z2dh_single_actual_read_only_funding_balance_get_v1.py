"""§11.13.5.Z2DH one-shot Funding Account GET tests. Recording transport only."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.offline_funding_balance_read_producer_v1.constants_v1 import (
    FUNDING_BALANCE_GET_EXECUTED as Z2DF_GET_EXECUTED,
)
from src.ops.offline_funding_balance_read_producer_v1.fixtures_v1 import (
    fixture_empty_funding_account_v1,
    fixture_usdc_nonzero_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.producer_v1 import (
    build_offline_funding_balance_read_client_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
)
from src.ops.section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1.constants_v1 import (
    AUTHORITY_EXPANSION_BEYOND_THIS_GET,
    AUTHORIZED_HOST,
    CAPITAL_MOVEMENT_ALLOWED,
    DEFAULT_MAX_RETRIES,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    POST_ALLOWED,
    PREDECESSOR_SLICE,
    RETRY_ALLOWED,
    SECOND_HTTP_CLIENT_CREATED,
    THIS_SLICE,
    TRANSFER_ALLOWED,
    WHITELIST_MUTATION_ALLOWED,
)
from src.ops.section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1.execute_v1 import (
    Z2DHFundingBalanceGetError,
    execute_single_actual_funding_balance_get_v1,
)
from src.ops.section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1.persist_claims_v1 import (
    CLAIMS,
)


def test_standing_flags_remain_fail_closed() -> None:
    assert OWNER_GO.endswith("Z2DH_SINGLE_ACTUAL_READ_ONLY_FUNDING_BALANCE_GET_V1")
    assert THIS_SLICE == "11.13.5.Z2DH"
    assert PREDECESSOR_SLICE == "11.13.5.Z2DG"
    assert ENDPOINT == "/api/v5/asset/balances"
    assert AUTHORIZED_HOST == "eea.okx.com"
    assert MAX_NETWORK_REQUEST_COUNT == 1
    assert DEFAULT_MAX_RETRIES == 0
    assert RETRY_ALLOWED is False
    assert WHITELIST_MUTATION_ALLOWED is False
    assert CLAIMS["RETRY_ALLOWED"] is False
    assert CLAIMS["WHITELIST_MUTATION_ALLOWED"] is False
    assert CLAIMS["SECRETREF_CHANGE_ALLOWED"] is False
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
    assert SECOND_HTTP_CLIENT_CREATED is False
    assert Z2DF_GET_EXECUTED is False


def test_offline_z2df_helper_still_forbids_productive_transport() -> None:
    with pytest.raises(Exception, match="FUNDING_BALANCE_PRODUCTIVE_TRANSPORT_FORBIDDEN"):
        build_offline_funding_balance_read_client_v1(
            transport=UrllibLiveCanaryTransportV1(wire_send_enabled=True)
        )


def test_consumed_z2dg_owner_go_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(Z2DHFundingBalanceGetError, match="OWNER_GO_MISMATCH"):
        execute_single_actual_funding_balance_get_v1(
            owner_go="PEAK_TRADE_OWNER_GO_Z2DG_SINGLE_ACTUAL_READ_ONLY_FUNDING_BALANCE_GET_V1",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=fixture_empty_funding_account_v1()),
        )


def test_wrong_origin_main_sha_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(Z2DHFundingBalanceGetError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_single_actual_funding_balance_get_v1(
            owner_go=OWNER_GO,
            origin_main_sha="78bb68cb53946acd26b92c872a169117373eb36f",
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(body=fixture_empty_funding_account_v1()),
        )


def test_recording_http_401_persists_then_fail_closed(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(
        status_code=401,
        body=(
            b'{"code":"50110","msg":"Your IP is not included in your API key'
            b' IP whitelist.","data":[]}'
        ),
    )
    with pytest.raises(Z2DHFundingBalanceGetError, match="FUNDING_BALANCE_OBSERVATION_FAIL_CLOSED"):
        execute_single_actual_funding_balance_get_v1(
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
    assert '"GET_REQUEST_COUNT": 1' in summary
    assert '"POST_COUNT": 0' in summary
    assert '"WRITE_REQUEST_COUNT": 0' in summary
    assert '"VENUE_CODE": "50110"' in snapshot
    assert '"SECRET_VALUES_INCLUDED": false' in snapshot
    assert len(transport.calls) == 1
    assert transport.calls[0].method == "GET"


def test_recording_usdc_observation_persists_without_secrets(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=fixture_usdc_nonzero_v1())
    result = execute_single_actual_funding_balance_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    assert result["MANIFEST_VERIFY_RC"] == 0
    summary = result["summary"]
    assert summary["HTTP_STATUS"] == 200
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["POST_COUNT"] == 0
    assert summary["WRITE_REQUEST_COUNT"] == 0
    assert summary["TRANSFER_REQUEST_COUNT"] == 0
    assert summary["OBSERVATION_CLASS"] == "SUCCESS"
    assert summary["FUNDING_ACCOUNT_STATUS"] == "OBSERVED_NONZERO_ROWS"
    assert summary["USDC_ROW_STATUS"] == "PRESENT"
    assert summary["USD_ROW_STATUS"] == "ABSENT_NOT_ZERO"
    assert summary["LIVE_AUTHORIZED"] is False
    assert len(transport.calls) == 1
    assert transport.calls[0].method == "GET"
    assert transport.calls[0].endpoint == ENDPOINT
    snapshot_text = (
        Path(result["EVIDENCE_PACK"])
        .joinpath("GET_SNAPSHOT.sanitized.json")
        .read_text(encoding="utf-8")
    )
    lowered = snapshot_text.lower()
    assert '"ok-access-key"' not in lowered
    assert "api_secret" not in lowered
    assert "plaintext:" not in lowered


def test_empty_array_is_observed_empty_not_zero(tmp_path: Path) -> None:
    result = execute_single_actual_funding_balance_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=RecordingFakeCanaryTransportV1(body=fixture_empty_funding_account_v1()),
    )
    assert result["summary"]["FUNDING_ACCOUNT_STATUS"] == "OBSERVED_EMPTY_NOT_ZERO"
    assert result["summary"]["ROW_COUNT"] == 0
    assert result["observation"]["ABSENT_CURRENCY_ROW_IS_NOT_ZERO"] is True
    assert result["observation"]["EMPTY_DATA_IS_NOT_ZERO"] is True


def test_ungated_post_remains_hard_blocked(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(body=fixture_empty_funding_account_v1())
    execute_single_actual_funding_balance_get_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=transport,
    )
    client_transport = transport
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
        LiveCanaryHttpClientV1,
    )
    from src.ops.section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1.constants_v1 import (
        FORBIDDEN_TRANSFER,
        REUSED_REST_BASE,
        REUSED_REST_HOST,
    )

    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=client_transport,
        max_request_count=1,
        max_retries=0,
    )
    with pytest.raises(LiveCanaryHttpError, match="UNGATED_POST_FORBIDDEN"):
        client.post(endpoint=FORBIDDEN_TRANSFER)
