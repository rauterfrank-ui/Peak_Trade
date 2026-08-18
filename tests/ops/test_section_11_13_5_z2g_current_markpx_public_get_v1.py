"""§11.13.5.Z2G current markPx public GET evidence.

Code contract plus docs/governance invariants. Does not authorize Live,
Testnet, orders, funding, scaling, or Multi-Future. Does not instantiate
COVER_USDC or treat markPx as an OKX expiry-fee operand.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.environment import LIVE_CONFIRM_TOKEN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    DEFAULT_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_markpx_productive_evidence_v1 import (
    AUTHORIZED_SCOPE,
    COVER_USDC_STATUS,
    CoverUsdcCurrentMarkpxEvidenceError,
    MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS,
    MARKPX_TERM_STATUS,
    MARK_PRICE_QUERY_PATH,
    NEXT_CANONICAL_POINTER,
    OWNER_GO,
    adjudicate_current_markpx_public_get_v1,
    classify_current_markpx_evidence_surface_v1,
    collect_current_markpx_public_get_v1,
    encode_fixture_mark_price_payload_v1,
    extract_current_markpx_from_public_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.formula_term_instance_binding_v1 import (
    HISTORICAL_L_PACK_MARKPX,
    HISTORICAL_S_PACK_MARKPX,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.governance_state_matrix_v1 import (
    NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
CANARY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE_V1.md"
)

Z2G_HEADING = "### 11.13.5.Z2G Current markPx public GET evidence"
CURRENT_MARKPX = "64123.4"
PROVIDER_TS = "1787080000001"
RECEIVE_TS = "1787080001.25"

_ADJ_KWARGS = {
    "markpx_current_value": CURRENT_MARKPX,
    "provider_ts_ms": PROVIDER_TS,
    "receive_ts_unix": RECEIVE_TS,
    "instrument_id": DEFAULT_INSTRUMENT_ID,
    "host": REUSED_BINDING_REST_HOST,
    "endpoint": MARK_PRICE_QUERY_PATH,
    "http_status": 200,
    "okx_code": "0",
    "get_request_count": 1,
    "post_count": 0,
    "owner_go": OWNER_GO,
}


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2g_section(text: str) -> str:
    start = text.find(Z2G_HEADING)
    assert start >= 0, "missing §11.13.5.Z2G heading"
    end = text.find("### 11.13.5.Z2H Current ticker bid/ask public GET evidence", start)
    assert end > start, "missing §11.13.5.Z2H boundary after Z2G"
    return text[start:end]


def _adjudicate(**overrides: object):
    kwargs = dict(_ADJ_KWARGS)
    kwargs.update(overrides)
    return adjudicate_current_markpx_public_get_v1(**kwargs)


def test_classification_is_public_readonly_mark_price_not_ticker() -> None:
    classification = classify_current_markpx_evidence_surface_v1()
    assert classification["ENDPOINT"] == MARK_PRICE_QUERY_PATH
    assert classification["HOST"] == "eea.okx.com"
    assert classification["METHOD"] == "GET"
    assert classification["AUTHENTICATION_REQUIREMENT"] == "NONE_PUBLIC"
    assert classification["READ_ONLY"] is True
    assert classification["INSTRUMENT_BINDING"] == DEFAULT_INSTRUMENT_ID
    assert classification["ACCOUNT_BINDING"] == "NONE_PUBLIC_ENDPOINT"
    assert "/api/v5/market/ticker" not in classification["ENDPOINT"]
    assert "mark-price" in classification["ENDPOINT"]


def test_payload_extracts_markpx_string_without_historical_substitution() -> None:
    payload = {
        "code": "0",
        "data": [
            {
                "instId": DEFAULT_INSTRUMENT_ID,
                "markPx": CURRENT_MARKPX,
                "ts": PROVIDER_TS,
            }
        ],
    }
    mark, ts = extract_current_markpx_from_public_payload_v1(
        payload,
        expected_instrument_id=DEFAULT_INSTRUMENT_ID,
    )
    assert mark == CURRENT_MARKPX
    assert ts == PROVIDER_TS
    assert mark not in {HISTORICAL_L_PACK_MARKPX, HISTORICAL_S_PACK_MARKPX}
    with pytest.raises(CoverUsdcCurrentMarkpxEvidenceError, match="REQUIRED_PRICE_FIELD_MISSING"):
        extract_current_markpx_from_public_payload_v1(
            {"code": "0", "data": [{"instId": DEFAULT_INSTRUMENT_ID, "ts": PROVIDER_TS}]},
            expected_instrument_id=DEFAULT_INSTRUMENT_ID,
        )
    with pytest.raises(
        CoverUsdcCurrentMarkpxEvidenceError,
        match="VENUE_INSTRUMENT_RESPONSE_MISMATCH",
    ):
        extract_current_markpx_from_public_payload_v1(
            {
                "code": "0",
                "data": [{"instId": "BTC-USD_UM_XPERP-310328", "markPx": "1", "ts": "1"}],
            },
            expected_instrument_id=DEFAULT_INSTRUMENT_ID,
        )


def test_adjudication_binds_observational_markpx_without_cover_usdc() -> None:
    bound = _adjudicate()
    assert bound.markpx_term_status == MARKPX_TERM_STATUS == "OBSERVED_NOT_NORMATIVELY_BOUND"
    assert bound.markpx_current_value == CURRENT_MARKPX
    assert bound.markpx_okx_delivery_fee_operand_status == MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS
    assert bound.markpx_okx_delivery_fee_operand_status == "UNPROVEN"
    assert bound.cover_usdc_status == COVER_USDC_STATUS == "UNINSTANTIATED"
    assert bound.numeric_funding_amount_produced is False
    assert bound.monetary_base_status == "UNPROVEN"
    assert bound.fx_status == "UNPROVEN"
    assert bound.rounding_status == "UNPROVEN"
    assert bound.exact_okx_fee_formula_status == "UNPROVEN"
    assert bound.position_value_algebra_status == "UNPROVEN"
    assert bound.evidence_read_only is True
    assert bound.live_authorized is False
    assert bound.next_canonical_pointer == NEXT_CANONICAL_POINTER
    with pytest.raises(
        CoverUsdcCurrentMarkpxEvidenceError,
        match="HISTORICAL_MARKPX_IS_NOT_CURRENT",
    ):
        _adjudicate(substitute_historical_markpx=True)
    with pytest.raises(
        CoverUsdcCurrentMarkpxEvidenceError,
        match="MARKPX_NOT_OKX_DELIVERY_FEE_OPERAND",
    ):
        _adjudicate(claim_okx_delivery_fee_operand=True)
    with pytest.raises(
        CoverUsdcCurrentMarkpxEvidenceError,
        match="COVER_USDC_REMAINS_UNINSTANTIATED",
    ):
        _adjudicate(instantiate_cover_usdc=True)
    with pytest.raises(CoverUsdcCurrentMarkpxEvidenceError, match="USD_USDC_CONVERSION_UNPROVEN"):
        _adjudicate(assume_usd_equals_usdc=True)
    with pytest.raises(CoverUsdcCurrentMarkpxEvidenceError, match="POST_NOT_AUTHORIZED"):
        _adjudicate(post_count=1)


def test_collect_uses_one_public_get_and_no_post() -> None:
    body = encode_fixture_mark_price_payload_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID,
        mark_px=CURRENT_MARKPX,
        ts_ms=PROVIDER_TS,
    )
    transport = RecordingFakeCanaryTransportV1(body=body, venue_live_contact=True)
    bound, snapshot, response = collect_current_markpx_public_get_v1(
        transport=transport,
        receive_ts_unix=RECEIVE_TS,
    )
    assert len(transport.calls) == 1
    request = transport.calls[0]
    assert request.method == "GET"
    assert request.host == "eea.okx.com"
    assert request.endpoint == MARK_PRICE_QUERY_PATH
    assert request.body_text == ""
    assert bound.markpx_current_value == CURRENT_MARKPX
    assert bound.get_request_count == 1
    assert bound.post_count == 0
    assert snapshot["POST_COUNT"] == 0
    assert response.status_code == 200


def test_z2g_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
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


def test_z2g_docs_bind_observational_markpx_without_cover_usdc() -> None:
    section = _z2g_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_ONLY",
        "MARKPX_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND",
        "MARKPX_CURRENT_VALUE=64495.3",
        "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS=UNPROVEN",
        "HISTORICAL_MARKPX_IS_NOT_CURRENT=true",
        "MONETARY_BASE_STATUS=UNPROVEN",
        "FX_STATUS=UNPROVEN",
        "ROUNDING_STATUS=UNPROVEN",
        "EXACT_OKX_FEE_FORMULA_STATUS=UNPROVEN",
        "POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN",
        "NORMAL_EXPIRY_RATE_0_0001_STATUS=PROVEN_APPLICABILITY_NON_OPERATIVE",
        "CONSERVATIVE_RATE_0_0003_STATUS=INTERNAL_CONSERVATIVE_POLICY_NOT_EXCHANGE_TRUTH",
        "COVER_USDC_STATUS=UNINSTANTIATED",
        "NUMERIC_FUNDING_AMOUNT_PRODUCED=false",
        "NUMERIC_FUNDING_AMOUNT=NONE",
        "QTY_LIMIT=1",
        "SCALING_AUTHORIZED=false",
        "MULTI_FUTURE_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "FUNDING_EXECUTED=false",
        "EXCHANGE_TRUTH_CHANGED=false",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CANONICAL_NEXT_STEP={NEXT_CANONICAL_POINTER}",
        "NO_USD_EQUALS_USDC",
        "NO_COVER_USDC_INSTANTIATION",
        "NO_NUMERIC_FUNDING_AMOUNT",
        "NO_FUNDING",
        "NO_EXECUTE",
        "/api/v5/public/mark-price",
    )
    for marker in required:
        assert marker in section, f"missing Z2G marker: {marker}"
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nSCALING_AUTHORIZED=true\n",
        "\nFUNDING_AMOUNT_PROVEN=true\n",
        "\nCOVER_USDC_STATUS=PROVEN\n",
        "\nEXCHANGE_TRUTH_CHANGED=true\n",
        "\nFX_STATUS=PROVEN\n",
        "\nROUNDING_STATUS=PROVEN\n",
        "\nMONETARY_BASE_STATUS=PROVEN\n",
        "\nNUMERIC_FUNDING_AMOUNT_PRODUCED=true\n",
        "\nUSD_EQUALS_USDC=true\n",
        "MARKPX_TERM_STATUS=UNINSTANTIATED",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"
    assert HISTORICAL_L_PACK_MARKPX not in section
    assert HISTORICAL_S_PACK_MARKPX not in section


def test_map_of_truth_and_spec_record_z2g_as_consumed_historical() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2G" in mot
    assert f"{OWNER_GO}_STATUS=CONSUMED_GET_ONLY_MARKPX_OBSERVED_NOT_COVER_USDC" in mot
    assert (
        f"{NEXT_CANONICAL_POINTER}_STATUS=CONSUMED_GET_ONLY_TICKER_BID_ASK_OBSERVED_NOT_COVER_USDC"
        in mot
    )
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert "Current SSOT: Master Runbook §11.13.5.Z2G." not in spec
    assert OWNER_GO in spec
    assert NEXT_CANONICAL_POINTER in spec
    assert "CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_ONLY" in spec


def test_sealed_z2g_evidence_pack_verifies_without_cover_usdc() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
        verify_manifest_v1,
    )

    root = (
        REPO_ROOT
        / "evidence"
        / "ops"
        / "section_11_13_5_z2g_current_markpx_public_get_v1"
        / "20260818T200745Z"
    )
    verify = verify_manifest_v1(root)
    assert verify["MANIFEST_VERIFY_RC"] == 0
    summary = _read(root / "SUMMARY.json")
    assert '"MARKPX_CURRENT_VALUE": "64495.3"' in summary
    assert '"COVER_USDC_STATUS": "UNINSTANTIATED"' in summary
    assert '"POST_COUNT": 0' in summary
    assert '"LIVE_AUTHORIZED": false' in summary
    zero = _read(root / "zero_write_assertions.json")
    assert '"ORDER_EXECUTED": false' in zero
    redaction = _read(root / "redaction_check.json")
    assert '"SECRET_VALUE_PERSISTED": false' in redaction
