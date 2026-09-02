"""Offline Funding Account balance read producer tests. Recording transport only."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from src.ops.offline_funding_balance_read_producer_v1.constants_v1 import (
    FORBIDDEN_NON_ALLOWLISTED_ASSET_ENDPOINT,
    FORBIDDEN_TRANSFER_ENDPOINT,
    FUNDING_BALANCE_ENDPOINT,
    OWNER_GO,
    PACKAGE_MARKER,
    PRODUCTIVE_NETWORK_REACHABILITY,
    REUSED_RO_SIGNER_SYMBOL,
    SECOND_HTTP_CLIENT_CREATED,
    TRADING_ACCOUNT_BALANCE_ENDPOINT,
    WORKPACKAGE_ID,
)
from src.ops.offline_funding_balance_read_producer_v1.fixtures_v1 import (
    fixture_empty_funding_account_v1,
    fixture_malformed_envelope_v1,
    fixture_malformed_numeric_balance_v1,
    fixture_multiple_asset_rows_v1,
    fixture_okx_code_nonzero_v1,
    fixture_other_nonzero_currency_v1,
    fixture_usd_nonzero_v1,
    fixture_usdc_nonzero_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_NUMERIC_STATUS_NONZERO,
    CURRENCY_ROW_NUMERIC_STATUS_NOT_APPLICABLE,
    CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO,
    CURRENCY_ROW_STATUS_PRESENT,
    FundingAccountBalanceObservationError,
    parse_funding_account_balance_observation_v1,
    row_for_ccy_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.persist_claims_v1 import CLAIMS
from src.ops.offline_funding_balance_read_producer_v1.producer_v1 import (
    assert_transfer_unreachable_through_reader_v1,
    build_offline_funding_balance_read_client_v1,
    observation_without_secrets_v1,
    observe_funding_account_balances_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ALLOWLIST_READ,
    ENDPOINT_ASSET_BALANCES,
    GET_ENDPOINTS_PRIVATE,
    LIVE_AUTHORIZED,
    POST_ENDPOINTS_GATED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
)
from src.ops.treasury_separation_gate import INTERNAL_TRANSFER, enforce_treasury_policy

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / (
    "src/ops/offline_funding_balance_read_producer_v1"
)
_FORBIDDEN_CALLS = frozenset(
    {
        "urlopen",
        "urlretrieve",
        "place_order",
        "submit_order",
        "load_secret",
        "materialize_secret",
        "SecretRef",
        "hmac",
    }
)
_FORBIDDEN_IMPORT_PREFIXES = ("requests", "httpx", "socket", "urllib")
_TS = "2026-09-02T12:00:00.000000Z"


def _parse(body: bytes) -> object:
    return parse_funding_account_balance_observation_v1(
        body_bytes=body,
        http_status=200,
        observed_at_utc=_TS,
        venue="OKX",
        rest_host="eea.okx.com",
        endpoint=FUNDING_BALANCE_ENDPOINT,
        transport_class="GOVERNED_FIXTURE",
        get_performed=True,
    )


def _observe(body: bytes, *, headers: dict[str, str] | None = None):
    transport = RecordingFakeCanaryTransportV1(body=body, venue_live_contact=False)
    client = build_offline_funding_balance_read_client_v1(transport=transport)
    return observe_funding_account_balances_v1(
        client=client,
        headers=headers,
        observed_at_utc=_TS,
    ), transport


def test_package_marker_and_standing_flags() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert WORKPACKAGE_ID == "OFFLINE_FUNDING_BALANCE_READ_PRODUCER_V1"
    assert OWNER_GO.endswith("Z2DF_OFFLINE_FUNDING_BALANCE_READ_PRODUCER_V1")
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert PRODUCTIVE_NETWORK_REACHABILITY is False
    assert SECOND_HTTP_CLIENT_CREATED is False
    assert CLAIMS["FUNDING_BALANCE_GET_IMPLEMENTED"] is True
    assert CLAIMS["FUNDING_BALANCE_GET_EXECUTED"] is False
    assert CLAIMS["FUNDING_ACCOUNT_STATUS"] == "UNKNOWN"
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert CLAIMS["CAPITAL_MOVEMENT_AUTHORIZED"] is False


def test_exact_endpoint_is_allowlisted_and_distinct_from_trading_balance() -> None:
    assert ENDPOINT_ASSET_BALANCES == "/api/v5/asset/balances"
    assert ENDPOINT_ASSET_BALANCES in GET_ENDPOINTS_PRIVATE
    assert ENDPOINT_ASSET_BALANCES in ENDPOINT_ALLOWLIST_READ
    assert TRADING_ACCOUNT_BALANCE_ENDPOINT in GET_ENDPOINTS_PRIVATE
    assert ENDPOINT_ASSET_BALANCES != TRADING_ACCOUNT_BALANCE_ENDPOINT
    assert FORBIDDEN_TRANSFER_ENDPOINT not in GET_ENDPOINTS_PRIVATE
    assert FORBIDDEN_TRANSFER_ENDPOINT not in POST_ENDPOINTS_GATED
    assert FORBIDDEN_NON_ALLOWLISTED_ASSET_ENDPOINT not in GET_ENDPOINTS_PRIVATE
    assert "/api/v5/asset/balances/" not in GET_ENDPOINTS_PRIVATE


def test_empty_valid_array_is_observation_not_inferred_zero() -> None:
    observation = _parse(fixture_empty_funding_account_v1())
    assert observation.row_count == 0
    assert observation.observed_ccys == ()
    assert observation.usdc_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    assert observation.usd_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    assert observation.other_asset_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    assert observation.usdc_numeric_status == CURRENCY_ROW_NUMERIC_STATUS_NOT_APPLICABLE
    payload = observation.to_dict()
    assert payload["ABSENT_CURRENCY_ROW_IS_NOT_ZERO"] is True
    assert payload["EMPTY_DATA_IS_NOT_ZERO"] is True
    assert row_for_ccy_v1(observation, "USDC") is None


def test_usdc_nonzero_preserves_exact_currency_and_numeric_string() -> None:
    observation = _parse(fixture_usdc_nonzero_v1())
    assert observation.usdc_row_status == CURRENCY_ROW_STATUS_PRESENT
    assert observation.usdc_numeric_status == CURRENCY_ROW_NUMERIC_STATUS_NONZERO
    assert observation.usd_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    row = row_for_ccy_v1(observation, "USDC")
    assert row is not None
    assert row.ccy == "USDC"
    assert row.bal_raw == "12.5"
    assert "USDC" in observation.nonzero_ccys
    assert "USD" not in observation.observed_ccys


def test_usd_and_usdc_remain_distinct() -> None:
    observation = _parse(fixture_usd_nonzero_v1())
    assert observation.usd_row_status == CURRENCY_ROW_STATUS_PRESENT
    assert observation.usdc_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    assert row_for_ccy_v1(observation, "USD") is not None
    assert row_for_ccy_v1(observation, "USDC") is None
    assert observation.to_dict()["USD_USDC_COLLAPSED"] is False


def test_multiple_asset_rows_preserve_exact_currencies() -> None:
    observation = _parse(fixture_multiple_asset_rows_v1())
    assert observation.observed_ccys == ("USDC", "USD", "BTC")
    assert observation.row_count == 3
    assert observation.usdc_row_status == CURRENCY_ROW_STATUS_PRESENT
    assert observation.usd_row_status == CURRENCY_ROW_STATUS_PRESENT
    assert observation.other_asset_row_status == CURRENCY_ROW_STATUS_PRESENT
    btc = row_for_ccy_v1(observation, "BTC")
    assert btc is not None
    assert btc.bal_raw == "0.01"
    assert observation.to_dict()["CAPITAL_NEXT_STEP_EMITTED"] is False
    assert observation.to_dict()["AVAILBAL_IS_NOT_TRANSFER_AUTHORITY"] is True


def test_other_nonzero_currency_is_not_classified_as_collateral() -> None:
    observation = _parse(fixture_other_nonzero_currency_v1())
    assert observation.nonzero_ccys == ("BTC",)
    assert observation.usdc_row_status == CURRENCY_ROW_STATUS_ABSENT_NOT_ZERO
    assert "collateral" not in str(observation.to_dict()).lower()


def test_malformed_numeric_balance_fail_closed() -> None:
    with pytest.raises(FundingAccountBalanceObservationError, match="NON_NUMERIC"):
        _parse(fixture_malformed_numeric_balance_v1())


def test_okx_code_nonzero_fail_closed() -> None:
    with pytest.raises(
        FundingAccountBalanceObservationError, match="VENUE_CODE_UNSUCCESSFUL:50111"
    ):
        _parse(fixture_okx_code_nonzero_v1())


def test_malformed_envelope_fail_closed() -> None:
    with pytest.raises(FundingAccountBalanceObservationError, match="MALFORMED_ENVELOPE"):
        _parse(fixture_malformed_envelope_v1())


def test_duplicate_processing_is_deterministic() -> None:
    body = fixture_multiple_asset_rows_v1()
    first = _parse(body)
    second = _parse(body)
    assert first.to_dict() == second.to_dict()
    assert first.body_sha256 == hashlib.sha256(body).hexdigest()


def test_producer_uses_existing_client_and_exact_get() -> None:
    observation, transport = _observe(fixture_usdc_nonzero_v1())
    assert len(transport.calls) == 1
    request = transport.calls[0]
    assert request.method == "GET"
    assert request.endpoint == FUNDING_BALANCE_ENDPOINT
    assert request.host == "eea.okx.com"
    assert "?" not in request.endpoint
    assert observation.get_performed is True
    assert observation.row_count == 1


def test_query_string_rejected_before_wire() -> None:
    transport = RecordingFakeCanaryTransportV1(body=fixture_empty_funding_account_v1())
    client = build_offline_funding_balance_read_client_v1(transport=transport)
    with pytest.raises(FundingAccountBalanceObservationError, match="QUERY_FORBIDDEN"):
        observe_funding_account_balances_v1(
            client=client,
            endpoint=f"{FUNDING_BALANCE_ENDPOINT}?ccy=USDC",
        )
    assert transport.calls == []


def test_only_get_accepted_and_non_allowlisted_asset_rejected() -> None:
    transport = RecordingFakeCanaryTransportV1(body=fixture_empty_funding_account_v1())
    client = build_offline_funding_balance_read_client_v1(transport=transport)
    with pytest.raises(LiveCanaryHttpError, match="ENDPOINT_NOT_ALLOWLISTED"):
        client.get(endpoint=FORBIDDEN_NON_ALLOWLISTED_ASSET_ENDPOINT)
    with pytest.raises(LiveCanaryHttpError, match="POST_ENDPOINT_NOT_ALLOWLISTED"):
        client._build_request(method="POST", endpoint=FUNDING_BALANCE_ENDPOINT)
    with pytest.raises(LiveCanaryHttpError, match="POST_ENDPOINT_NOT_ALLOWLISTED"):
        client._build_request(method="POST", endpoint=FORBIDDEN_TRANSFER_ENDPOINT)
    with pytest.raises(LiveCanaryHttpError, match="HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:PUT"):
        client._build_request(method="PUT", endpoint=FUNDING_BALANCE_ENDPOINT)
    assert transport.calls == []


def test_transfer_unreachable_through_funding_reader() -> None:
    transport = RecordingFakeCanaryTransportV1(body=fixture_empty_funding_account_v1())
    client = build_offline_funding_balance_read_client_v1(transport=transport)
    assert_transfer_unreachable_through_reader_v1(client)
    assert transport.calls == []
    with pytest.raises(Exception, match="treasury_block"):
        enforce_treasury_policy(INTERNAL_TRANSFER, role="bot")


def test_productive_urllib_transport_rejected() -> None:
    with pytest.raises(
        FundingAccountBalanceObservationError, match="PRODUCTIVE_TRANSPORT_FORBIDDEN"
    ):
        build_offline_funding_balance_read_client_v1(transport=UrllibLiveCanaryTransportV1())


def test_existing_client_type_reused_not_subclassed() -> None:
    transport = RecordingFakeCanaryTransportV1(body=fixture_empty_funding_account_v1())
    client = build_offline_funding_balance_read_client_v1(transport=transport)
    assert type(client) is LiveCanaryHttpClientV1
    assert client.max_retries == 0
    assert client.max_request_count == 1


def test_auth_headers_pass_through_without_secret_in_evidence() -> None:
    headers = {
        "OK-ACCESS-KEY": "dummy-not-a-real-secret",
        "OK-ACCESS-SIGN": "dummy-sign",
        "OK-ACCESS-PASSPHRASE": "dummy-pass",
    }
    observation, transport = _observe(fixture_empty_funding_account_v1(), headers=headers)
    assert observation.auth_header_sent is True
    payload = observation_without_secrets_v1(
        observation,
        forbidden_values=("dummy-not-a-real-secret", "dummy-sign", "dummy-pass"),
    )
    rendered = str(payload).lower()
    assert "dummy-not-a-real-secret" not in rendered
    assert "dummy-sign" not in rendered
    assert "dummy-pass" not in rendered
    assert transport.calls[0].headers["OK-ACCESS-KEY"] == "dummy-not-a-real-secret"


def test_package_does_not_create_parallel_http_or_signer_stack() -> None:
    for path in PACKAGE_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(_FORBIDDEN_IMPORT_PREFIXES)
            if isinstance(node, ast.ImportFrom):
                module = str(node.module or "")
                assert not module.startswith(_FORBIDDEN_IMPORT_PREFIXES)
                assert "okx_live_canary_signer" not in module
                assert "secretref" not in module
                assert "live_credential" not in module
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in _FORBIDDEN_CALLS
            if isinstance(node, ast.ClassDef):
                assert "HttpClient" not in node.name
                assert "Signer" not in node.name
    assert REUSED_RO_SIGNER_SYMBOL == "build_okx_live_ro_get_auth_headers_v1"
