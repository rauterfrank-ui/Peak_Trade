"""§11.13.5.Z2H current ticker bid/ask public GET evidence.

Code contract plus docs/governance invariants. Does not authorize Live,
Testnet, orders, funding, scaling, or Multi-Future. Does not instantiate
COVER_USDC or a numeric SLIPPAGE_RESERVE.
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_ticker_bid_ask_productive_evidence_v1 import (
    AUTHORIZED_SCOPE,
    BID_ASK_TERM_STATUS,
    COVER_USDC_STATUS,
    CoverUsdcCurrentTickerBidAskEvidenceError,
    HISTORICAL_L_PACK_ASK_PX,
    HISTORICAL_L_PACK_BID_PX,
    HISTORICAL_S_PACK_ASK_PX,
    HISTORICAL_S_PACK_BID_PX,
    NEXT_CANONICAL_POINTER,
    OWNER_GO,
    SLIPPAGE_RESERVE_NUMERIC_STATUS,
    TICKER_QUERY_PATH,
    adjudicate_current_ticker_bid_ask_public_get_v1,
    classify_current_ticker_bid_ask_evidence_surface_v1,
    collect_current_ticker_bid_ask_public_get_v1,
    encode_fixture_ticker_payload_v1,
    extract_current_bid_ask_from_public_ticker_payload_v1,
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

Z2H_HEADING = "### 11.13.5.Z2H Current ticker bid/ask public GET evidence"
CURRENT_BID = "64501.1"
CURRENT_ASK = "64501.2"
PROVIDER_TS = "1787085000001"
RECEIVE_TS = "1787085001.25"

_ADJ_KWARGS = {
    "bid_px_current_value": CURRENT_BID,
    "ask_px_current_value": CURRENT_ASK,
    "provider_ts_ms": PROVIDER_TS,
    "receive_ts_unix": RECEIVE_TS,
    "instrument_id": DEFAULT_INSTRUMENT_ID,
    "host": REUSED_BINDING_REST_HOST,
    "endpoint": TICKER_QUERY_PATH,
    "http_status": 200,
    "okx_code": "0",
    "get_request_count": 1,
    "post_count": 0,
    "owner_go": OWNER_GO,
}


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2h_section(text: str) -> str:
    start = text.find(Z2H_HEADING)
    assert start >= 0, "missing §11.13.5.Z2H heading"
    end = text.find("### 11.13.5.Z2I", start)
    assert end > start, "missing §11.13.5.Z2I boundary after Z2H"
    return text[start:end]


def _adjudicate(**overrides: object):
    kwargs = dict(_ADJ_KWARGS)
    kwargs.update(overrides)
    return adjudicate_current_ticker_bid_ask_public_get_v1(**kwargs)


def test_classification_is_public_readonly_ticker_not_mark_price() -> None:
    surface = classify_current_ticker_bid_ask_evidence_surface_v1()
    assert surface["METHOD"] == "GET"
    assert surface["AUTHENTICATION_REQUIREMENT"] == "NONE_PUBLIC"
    assert surface["READ_ONLY"] is True
    assert surface["ENDPOINT"] == TICKER_QUERY_PATH
    assert "mark-price" not in surface["ENDPOINT"]
    assert "SLIPPAGE_BID_ASK_CURRENT_VALUE_OBSERVATIONAL" in surface["TERM_CAN_INSTANTIATE"]
    assert "COVER_USDC" in surface["TERM_CANNOT_PROVE"]
    assert "SLIPPAGE_RESERVE_NUMERIC" in surface["TERM_CANNOT_PROVE"]


def test_extract_binds_bid_ask_and_ignores_ticker_last() -> None:
    body = encode_fixture_ticker_payload_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID,
        bid_px=CURRENT_BID,
        ask_px=CURRENT_ASK,
        ts_ms=PROVIDER_TS,
        mark_px="99999.9",
    )
    import json

    payload = json.loads(body.decode("utf-8"))
    payload["data"][0]["last"] = "99999.9"
    bid, ask, ts = extract_current_bid_ask_from_public_ticker_payload_v1(
        payload,
        expected_instrument_id=DEFAULT_INSTRUMENT_ID,
    )
    assert bid == CURRENT_BID
    assert ask == CURRENT_ASK
    assert ts == PROVIDER_TS


def test_extract_rejects_missing_bid() -> None:
    payload = {
        "code": "0",
        "data": [{"instId": DEFAULT_INSTRUMENT_ID, "askPx": CURRENT_ASK, "ts": PROVIDER_TS}],
    }
    with pytest.raises(CoverUsdcCurrentTickerBidAskEvidenceError, match="bidPx"):
        extract_current_bid_ask_from_public_ticker_payload_v1(
            payload,
            expected_instrument_id=DEFAULT_INSTRUMENT_ID,
        )


def test_adjudication_is_observational_and_leaves_cover_usdc_uninstantiated() -> None:
    bound = _adjudicate()
    assert bound.bid_ask_term_status == BID_ASK_TERM_STATUS
    assert bound.bid_px_current_value == CURRENT_BID
    assert bound.ask_px_current_value == CURRENT_ASK
    assert bound.slippage_reserve_numeric_status == SLIPPAGE_RESERVE_NUMERIC_STATUS
    assert bound.cover_usdc_status == COVER_USDC_STATUS
    assert bound.numeric_funding_amount_produced is False
    assert bound.markpx_term_status == "OBSERVED_NOT_NORMATIVELY_BOUND"
    assert bound.markpx_okx_delivery_fee_operand_status == "UNPROVEN"
    assert bound.monetary_base_status == "UNPROVEN"
    assert bound.fx_status == "UNPROVEN"
    assert bound.rounding_status == "UNPROVEN"
    assert bound.get_request_count == 1
    assert bound.post_count == 0
    assert bound.live_authorized is False
    assert bound.next_canonical_pointer == NEXT_CANONICAL_POINTER


@pytest.mark.parametrize(
    "kwargs,needle",
    [
        ({"substitute_historical_bid_ask": True}, "HISTORICAL_BID_ASK_IS_NOT_CURRENT"),
        ({"substitute_ticker_markpx": True}, "TICKER_MARKPX_IS_NOT_MARK_PRICE_GET"),
        (
            {"instantiate_slippage_reserve_numeric": True},
            "SLIPPAGE_RESERVE_NUMERIC_REMAINS_UNINSTANTIATED",
        ),
        ({"instantiate_cover_usdc": True}, "COVER_USDC_REMAINS_UNINSTANTIATED"),
        ({"invent_monetary_base": True}, "MONETARY_BASE_REMAINS_UNPROVEN"),
        ({"apply_usd_usdc_conversion": True}, "USD_USDC_CONVERSION_UNPROVEN"),
        ({"assume_usd_equals_usdc": True}, "USD_USDC_CONVERSION_UNPROVEN"),
        ({"apply_rounding": True}, "USDC_ROUNDING_PRECISION_UNPROVEN"),
        ({"produce_numeric_funding_amount": True}, "NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN"),
        ({"collect_mmr": True}, "MMR_NOT_IN_THIS_GET_SCOPE"),
        ({"live_authorized": True}, "LIVE_NOT_AUTHORIZED"),
        ({"testnet_authorized": True}, "TESTNET_NOT_AUTHORIZED"),
        ({"post_count": 1}, "POST_NOT_AUTHORIZED"),
        ({"get_request_count": 2}, "GET_REQUEST_COUNT_NOT_ONE"),
    ],
)
def test_adjudication_fail_closed_guards(kwargs: dict, needle: str) -> None:
    with pytest.raises(CoverUsdcCurrentTickerBidAskEvidenceError, match=needle):
        _adjudicate(**kwargs)


def test_collect_uses_one_public_get_and_no_post() -> None:
    body = encode_fixture_ticker_payload_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID,
        bid_px=CURRENT_BID,
        ask_px=CURRENT_ASK,
        ts_ms=PROVIDER_TS,
    )
    transport = RecordingFakeCanaryTransportV1(body=body, venue_live_contact=True)
    bound, snapshot, response = collect_current_ticker_bid_ask_public_get_v1(
        transport=transport,
        receive_ts_unix=RECEIVE_TS,
    )
    assert len(transport.calls) == 1
    request = transport.calls[0]
    assert request.method == "GET"
    assert request.host == "eea.okx.com"
    assert request.endpoint == TICKER_QUERY_PATH
    assert request.body_text == ""
    assert bound.bid_px_current_value == CURRENT_BID
    assert bound.ask_px_current_value == CURRENT_ASK
    assert bound.get_request_count == 1
    assert bound.post_count == 0
    assert snapshot["POST_COUNT"] == 0
    assert snapshot["NO_POSITION_TIERS_GET_THIS_STEP"] is True
    assert response.status_code == 200


def test_z2h_go_does_not_authorize_live_order_or_funding() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert OWNER_GO in NON_EXECUTE_GO_TOKENS_FORBIDDEN_FOR_SUBMIT
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


def test_z2h_docs_bind_observational_bid_ask_without_cover_usdc() -> None:
    section = _z2h_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_ONLY",
        "BID_ASK_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND",
        "BID_PX_CURRENT_VALUE=64529.9",
        "ASK_PX_CURRENT_VALUE=64530",
        "SLIPPAGE_RESERVE_NUMERIC_STATUS=UNINSTANTIATED",
        "MARKPX_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND",
        "MARKPX_CURRENT_VALUE=64495.3",
        "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS=UNPROVEN",
        "HISTORICAL_BID_ASK_IS_NOT_CURRENT=true",
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
        "NO_SLIPPAGE_RESERVE_NUMERIC",
        "NO_NUMERIC_FUNDING_AMOUNT",
        "NO_FUNDING",
        "NO_EXECUTE",
        "/api/v5/market/ticker",
    )
    for marker in required:
        assert marker in section, f"missing Z2H marker: {marker}"
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
        "SLIPPAGE_RESERVE_NUMERIC_STATUS=PROVEN",
        "BID_ASK_TERM_STATUS=UNINSTANTIATED",
    )
    for assignment in forbidden:
        assert assignment not in section, f"forbidden assignment present: {assignment!r}"
    assert HISTORICAL_L_PACK_BID_PX not in section
    assert HISTORICAL_L_PACK_ASK_PX not in section
    assert HISTORICAL_S_PACK_BID_PX not in section
    assert HISTORICAL_S_PACK_ASK_PX not in section


def test_map_of_truth_and_spec_follow_z2h_current_pointer() -> None:
    mot = _read(MAP_OF_TRUTH)
    spec = _read(CANARY_SPEC)
    assert "§11.13.5.Z2H" in mot
    assert f"NEXT_CANONICAL_STEP_POINTER={NEXT_CANONICAL_POINTER}" in mot
    assert f"{OWNER_GO}_STATUS=CONSUMED_GET_ONLY_TICKER_BID_ASK_OBSERVED_NOT_COVER_USDC" in mot
    assert "COVER_USDC_STATUS=UNINSTANTIATED" in mot
    assert "BID_ASK_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND" in mot
    assert "SLIPPAGE_RESERVE_NUMERIC_STATUS=UNINSTANTIATED" in mot
    assert "Current SSOT: Master Runbook §11.13.5.Z2H." in spec
    assert OWNER_GO in spec
    assert NEXT_CANONICAL_POINTER in spec
    assert "Current SSOT: Master Runbook §11.13.5.Z2G." not in spec
    assert "CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_ONLY" in spec


def test_sealed_z2h_evidence_pack_verifies_without_cover_usdc() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
        verify_manifest_v1,
    )

    root = (
        REPO_ROOT
        / "evidence"
        / "ops"
        / "section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1"
        / "20260818T203435Z"
    )
    verify = verify_manifest_v1(root)
    assert verify["MANIFEST_VERIFY_RC"] == 0
    summary = _read(root / "SUMMARY.json")
    assert '"BID_PX_CURRENT_VALUE": "64529.9"' in summary
    assert '"ASK_PX_CURRENT_VALUE": "64530"' in summary
    assert '"COVER_USDC_STATUS": "UNINSTANTIATED"' in summary
    assert '"POST_COUNT": 0' in summary
    assert '"LIVE_AUTHORIZED": false' in summary
    zero = _read(root / "zero_write_assertions.json")
    assert '"ORDER_EXECUTED": false' in zero
    redaction = _read(root / "redaction_check.json")
    assert '"SECRET_VALUE_PERSISTED": false' in redaction
