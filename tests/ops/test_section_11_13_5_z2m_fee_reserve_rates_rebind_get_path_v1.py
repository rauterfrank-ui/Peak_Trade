"""§11.13.5.Z2M one-shot authenticated trade-fee GET execution-path ratification.

Code contract plus docs/governance invariants. Does not authorize Live,
Testnet, orders, funding, conversion, transfer, Canary execute, or a
productive HTTP GET. Does not instantiate COVER_USDC or freeze fee rates.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    ENDPOINT_ALLOWLIST_READ,
    GET_ENDPOINTS_PRIVATE,
    GET_ENDPOINTS_PUBLIC,
    LIVE_AUTHORIZED,
    POST_ENDPOINTS_GATED,
    REQUIRED_SECRETREF_URI,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_fee_reserve_rates_rebind_get_path_v1 import (
    AUTHORIZED_SCOPE,
    COVER_USDC_STATUS,
    EXECUTE_OWNER_GO,
    FEE_RESERVE_RATES_ADJUDICATION,
    MAX_RETRIES,
    NEXT_CANONICAL_POINTER,
    OWNER_GO,
    SEALED_ENDPOINT,
    SEALED_HOST,
    SEALED_INST_FAMILY,
    SEALED_INST_TYPE,
    SEALED_METHOD,
    SEALED_PATH,
    SEALED_QUERY,
    CoverUsdcFeeReserveRatesRebindGetPathError,
    assert_sealed_trade_fee_request_grammar_v1,
    build_sealed_trade_fee_get_request_v1,
    classify_fee_reserve_rates_rebind_get_path_v1,
    collect_fee_reserve_rates_rebind_get_v1,
    ratify_fee_reserve_rates_rebind_get_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.governance_state_matrix_v1 import (
    NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.secretref_v1 import (
    LiveCanarySecretRefError,
    validate_live_canary_secretref_uri_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
)
from scripts.ops.run_section_11_13_5_z2m_fee_reserve_rates_rebind_get_path_v1 import (
    main as ratify_cli_main,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2M_HEADING = "### 11.13.5.Z2M One-shot authenticated trade-fee GET execution-path ratification"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2m_section(text: str) -> str:
    start = text.find(Z2M_HEADING)
    assert start >= 0, "missing §11.13.5.Z2M heading"
    end = text.find("## 11.14 Live order and economic evidence ladder", start)
    assert end > start, "missing §11.14 boundary after Z2M"
    return text[start:end]


def _fixture_creds() -> dict[str, str]:
    return {"api_key": "A" * 36, "api_secret": "B" * 32, "passphrase": "C" * 14}


def _handle(tmp_path: Path):
    vault = tmp_path / "vault.json"
    vault.write_text(
        json.dumps({REQUIRED_SECRETREF_URI: _fixture_creds()}),
        encoding="utf-8",
    )
    backend = build_file_secretref_vault_backend_v1(vault_file=vault)
    return resolve_and_load_live_canary_secretref_ephemeral_v1(
        secret_reference=REQUIRED_SECRETREF_URI,
        vault_backend=backend,
    )


def test_classification_is_authenticated_readonly_exact_grammar() -> None:
    classification = classify_fee_reserve_rates_rebind_get_path_v1()
    assert classification["HOST"] == "eea.okx.com"
    assert classification["METHOD"] == "GET"
    assert classification["PATH"] == "/api/v5/account/trade-fee"
    assert classification["QUERY"] == "instType=FUTURES&instFamily=BTC-USD_UM_XPERP"
    assert classification["ENDPOINT"] == SEALED_ENDPOINT
    assert classification["READ_ONLY"] is True
    assert classification["SECRETREF_URI"] == REQUIRED_SECRETREF_URI
    assert classification["CREDENTIAL_CLASS"] == "LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY"
    assert classification["ONE_SHOT_REQUEST_LIMIT"] == 1
    assert classification["RETRY_COUNT_ALLOWED"] == 0
    assert classification["THIS_GO_AUTHORIZES_HTTP_GET"] is False
    assert classification["GENERAL_CLIENT_ALLOWLIST_WIDENED"] is False
    assert classification["GET_ENDPOINTS_PRIVATE_INCLUDES_TRADE_FEE"] is False
    assert classification["FEE_RESERVE_RATES_ADJUDICATION"] == "UNPROVEN"
    assert classification["COVER_USDC_STATUS"] == "UNINSTANTIATED"
    assert classification["LIVE_AUTHORIZED"] is False


def test_exact_grammar_accepted_and_deviations_rejected() -> None:
    assert_sealed_trade_fee_request_grammar_v1(
        method=SEALED_METHOD,
        host=SEALED_HOST,
        path=SEALED_PATH,
        query=SEALED_QUERY,
    )
    request = build_sealed_trade_fee_get_request_v1()
    assert request.method == "GET"
    assert request.host == "eea.okx.com"
    assert request.endpoint == SEALED_ENDPOINT
    assert request.body_text == ""
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="HOST_NOT_ALLOWLISTED"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="GET",
            host="www.okx.com",
            path=SEALED_PATH,
            query=SEALED_QUERY,
        )
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="METHOD_NOT_ALLOWLISTED"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="POST",
            host=SEALED_HOST,
            path=SEALED_PATH,
            query=SEALED_QUERY,
        )
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="PATH_NOT_ALLOWLISTED"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="GET",
            host=SEALED_HOST,
            path="/api/v5/account/balance",
            query=SEALED_QUERY,
        )
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="QUERY_NOT_ALLOWLISTED"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="GET",
            host=SEALED_HOST,
            path=SEALED_PATH,
            query=f"instType=SWAP&instFamily={SEALED_INST_FAMILY}",
        )
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="QUERY_NOT_ALLOWLISTED"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="GET",
            host=SEALED_HOST,
            path=SEALED_PATH,
            query=f"instType={SEALED_INST_TYPE}&instFamily=BTC-USDT",
        )
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="QUERY_NOT_ALLOWLISTED"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="GET",
            host=SEALED_HOST,
            path=SEALED_PATH,
            query=SEALED_QUERY + "&instId=BTC-USD_UM_XPERP-310404",
        )
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="QUERY_NOT_ALLOWLISTED"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="GET",
            host=SEALED_HOST,
            path=SEALED_PATH,
            query=f"instFamily={SEALED_INST_FAMILY}",
        )
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="QUERY_NOT_ALLOWLISTED"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="GET",
            host=SEALED_HOST,
            path=SEALED_PATH,
            query=f"instType={SEALED_INST_TYPE}",
        )
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="HTTP_METHOD_HARD_BLOCK"):
        assert_sealed_trade_fee_request_grammar_v1(
            method="DELETE",
            host=SEALED_HOST,
            path=SEALED_PATH,
            query=SEALED_QUERY,
        )


def test_general_canary_allowlists_do_not_include_trade_fee() -> None:
    assert SEALED_PATH not in GET_ENDPOINTS_PRIVATE
    assert SEALED_PATH not in GET_ENDPOINTS_PUBLIC
    assert SEALED_PATH not in ENDPOINT_ALLOWLIST_READ
    assert SEALED_PATH not in POST_ENDPOINTS_GATED
    assert "/api/v5/trade/order" in POST_ENDPOINTS_GATED
    transport = RecordingFakeCanaryTransportV1()
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=transport,
        max_retries=0,
        max_request_count=1,
    )
    with pytest.raises(LiveCanaryHttpError, match="ENDPOINT_NOT_ALLOWLISTED"):
        client.get(endpoint=SEALED_ENDPOINT)
    assert transport.calls == []


def test_secretref_is_canary_native_and_rejects_shadow_recon() -> None:
    assert validate_live_canary_secretref_uri_v1(REQUIRED_SECRETREF_URI) == REQUIRED_SECRETREF_URI
    with pytest.raises(LiveCanarySecretRefError, match="SECRETREF_CANARY_PATH_MARKER_REQUIRED"):
        validate_live_canary_secretref_uri_v1("secretref://vault/peak-trade/live-shadow-recon/okx")
    with pytest.raises(LiveCanarySecretRefError, match="SECRETREF_URI_BINDING_MISMATCH"):
        validate_live_canary_secretref_uri_v1(
            "secretref://vault/peak-trade/live-canary-minimum-exposure/other"
        )


def test_collect_one_shot_no_retry_no_secret_leak(tmp_path: Path) -> None:
    handle = _handle(tmp_path)
    try:
        body = json.dumps(
            {
                "code": "0",
                "msg": "",
                "data": [
                    {
                        "instType": SEALED_INST_TYPE,
                        "instFamily": SEALED_INST_FAMILY,
                        "taker": "",
                        "maker": "",
                        "takerUSDC": "-0.0005",
                        "makerUSDC": "-0.0002",
                        "ruleType": "normal",
                    }
                ],
            }
        ).encode("utf-8")
        transport = RecordingFakeCanaryTransportV1(body=body, venue_live_contact=True)
        snapshot, response = collect_fee_reserve_rates_rebind_get_v1(
            transport=transport,
            handle=handle,
            owner_go=EXECUTE_OWNER_GO,
            execute_trade_fee_get=True,
        )
        assert len(transport.calls) == 1
        assert transport.calls[0].method == "GET"
        assert transport.calls[0].host == "eea.okx.com"
        assert transport.calls[0].endpoint == SEALED_ENDPOINT
        assert transport.calls[0].body_text == ""
        assert response.status_code == 200
        assert snapshot["GET_REQUEST_COUNT"] == 1
        assert snapshot["POST_COUNT"] == 0
        assert snapshot["RETRY_COUNT"] == 0
        assert snapshot["FEE_RESERVE_RATES_ADJUDICATION"] == "UNPROVEN"
        rendered = json.dumps(snapshot)
        creds = _fixture_creds()
        assert creds["api_key"] not in rendered
        assert creds["api_secret"] not in rendered
        assert creds["passphrase"] not in rendered
        assert snapshot["SECRET_VALUES_INCLUDED"] is False
        assert snapshot["AUTH_HEADERS_PRESENCE"]["OK-ACCESS-SIGN_PRESENT"] is True
        assert snapshot["AUTH_HEADERS_PRESENCE"]["OK-ACCESS-KEY_PRESENT"] is True
        timeout_transport = RecordingFakeCanaryTransportV1(raise_timeout=True)
        with pytest.raises(TimeoutError):
            collect_fee_reserve_rates_rebind_get_v1(
                transport=timeout_transport,
                handle=handle,
                owner_go=EXECUTE_OWNER_GO,
                execute_trade_fee_get=True,
            )
        assert len(timeout_transport.calls) == 1
        with pytest.raises(
            CoverUsdcFeeReserveRatesRebindGetPathError,
            match="EXECUTE_OWNER_GO_MISMATCH",
        ):
            collect_fee_reserve_rates_rebind_get_v1(
                transport=transport,
                handle=handle,
                owner_go=OWNER_GO,
                execute_trade_fee_get=True,
            )
    finally:
        release_live_canary_ephemeral_material_v1(handle)
    assert MAX_RETRIES == 0


def test_ratify_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    assert EXECUTE_OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    assert NEXT_CANONICAL_POINTER in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=OWNER_GO,
        owner_go_consumed=False,
        authorization_scope=AUTHORIZATION_SCOPE,
        bound_origin_main_sha="abc",
        expected_origin_main_sha="abc",
        live_canary_authorized=True,
        live_enabled=True,
        live_armed=True,
        confirm_token=LIVE_CONFIRM_TOKEN,
        blocks_new_entry=False,
        unresolved_economic_divergence=False,
        live_reconciliation_proven=True,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        environment="LIVE",
        fixture_or_demo_or_testnet=False,
        max_notional="6.30437",
        min_executable_notional="6.30437",
        order_count=0,
        position_count=0,
        exposure_above_minimum_bound=False,
        live_canary_cybersecurity_gate="PASS",
        rest_host="eea.okx.com",
        secretref_uri="secretref://vault/peak-trade/live-canary-minimum-exposure/okx",
    )
    assert evaluation.submit_allowed is False
    assert "REEVALUATION_OR_PREPARATION_GO_CANNOT_AUTHORIZE_SUBMIT" in evaluation.reasons


def test_ratify_cli_does_not_execute_http() -> None:
    rc = ratify_cli_main(
        [
            "--owner-go",
            OWNER_GO,
            "--bound-origin-main-sha",
            "eecf5f0d47a9b7654a9c1b0469539dbb7d6afeed",
            "--ratify-execution-path",
        ]
    )
    assert rc == 0
    rc_execute = ratify_cli_main(
        [
            "--owner-go",
            OWNER_GO,
            "--bound-origin-main-sha",
            "eecf5f0d47a9b7654a9c1b0469539dbb7d6afeed",
            "--execute-trade-fee-get",
        ]
    )
    assert rc_execute == 2
    payload = ratify_fee_reserve_rates_rebind_get_path_v1(owner_go=OWNER_GO)
    assert payload["EVIDENCE_CALL_EXECUTED"] is False
    assert payload["EVIDENCE_CALL_COUNT"] == 0
    assert payload["MAX_RETRIES"] == 0
    assert payload["FEE_RESERVE_RATES_ADJUDICATION"] == FEE_RESERVE_RATES_ADJUDICATION
    assert payload["classification"]["COVER_USDC_STATUS"] == COVER_USDC_STATUS
    assert AUTHORIZED_SCOPE == "FEE_RESERVE_RATES_REBIND_GET_EXECUTION_PATH_RATIFICATION_ONLY"
    with pytest.raises(CoverUsdcFeeReserveRatesRebindGetPathError, match="OWNER_GO_MISMATCH"):
        ratify_fee_reserve_rates_rebind_get_path_v1(owner_go=EXECUTE_OWNER_GO)


def test_z2m_docs_bind_path_without_get_or_cover_usdc() -> None:
    section = _z2m_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=FEE_RESERVE_RATES_REBIND_GET_EXECUTION_PATH_RATIFICATION_ONLY",
        "EVIDENCE_CALL_EXECUTED=false",
        "EVIDENCE_CALL_COUNT=0",
        "REQUEST_HOST=eea.okx.com",
        "REQUEST_METHOD=GET",
        "REQUEST_PATH=/api/v5/account/trade-fee",
        "REQUEST_QUERY=instType=FUTURES&instFamily=BTC-USD_UM_XPERP",
        "RETRY_COUNT_ALLOWED=0",
        "ONE_SHOT_REQUEST_LIMIT=1",
        "SECRETREF_URI=secretref://vault/peak-trade/live-canary-minimum-exposure/okx",
        "REQUIRED_CREDENTIAL_CLASS=LIVE_CANARY_MINIMUM_EXPOSURE_TRADE_API_KEY",
        "FEE_RESERVE_RATES_ADJUDICATION=UNPROVEN",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "LIVE_AUTHORIZED=false",
        "NO_FUNDING",
        "NO_TRANSFER",
        "NO_CONVERSION",
        "NO_ORDER",
        "NO_CANARY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CANONICAL_NEXT_STEP={NEXT_CANONICAL_POINTER}",
        f"EXECUTE_OWNER_GO={EXECUTE_OWNER_GO}",
        "THIS_GO_AUTHORIZES_HTTP_GET=false",
        "GENERAL_CANARY_GET_ALLOWLIST_WIDENED=false",
    )
    for token in required:
        assert token in section, f"missing runbook token: {token}"
    mot = _read(MAP_OF_TRUTH)
    assert "§11.13.5.Z2M" in mot
    assert "FEE_RESERVE_RATES_REBIND_GET_EXECUTION_PATH_RATIFIED=true" in mot
    assert (
        "FEE_RESERVE_RATES_REBIND_GET_USING_SEALED_GRAMMAR_AND_SEALED_EXECUTION_PATH_NOT_EXECUTED"
        in mot
    )
