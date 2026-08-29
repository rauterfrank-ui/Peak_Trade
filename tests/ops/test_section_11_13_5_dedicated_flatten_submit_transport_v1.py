"""Dedicated flatten submit/transport contract tests. Fake transport only; no network."""

from __future__ import annotations

import inspect
import json
from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_SUBMIT,
    ORDER_COUNT_LIMIT,
    POSITION_COUNT_LIMIT,
    POST_ENDPOINTS_GATED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_orchestration_contract_v1 import (
    CanaryFlattenSubmitPermitV1,
    evaluate_canary_flatten_orchestration_contract_v1,
    issue_canary_flatten_submit_permit_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    CLOSE_POSITION_ENDPOINT_ALLOWLISTED,
    DEDICATED_FLATTEN_TRANSPORT_IMPLEMENTED,
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
    LIVE_FLATTEN_PROVABILITY,
    REDUCE_ONLY_FLATTEN_INTENT_IMPLEMENTED,
    LiveCanaryFlattenSubmitTransportError,
    build_canary_flatten_submit_request_v1,
    run_canary_flatten_submit_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    CanaryEntrySubmitPermitV1,
    CanaryFlattenHttpPermitV1,
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    RecordingFakeCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    FLATTEN_LIMIT_PRICE_GATE_STATUS,
    build_minimum_valid_canary_order_plan_v1,
    serialize_canary_flatten_venue_native_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    run_canary_submit_transport_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "aa421d84cd0223146ab63f94405e81ed813d40c3"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _price_permit(*, side: str = "SELL", pos: str = "1") -> Any:
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        FlattenPriceInputV1(
            flatten_side=side,
            observed_signed_pos=pos,
            bid="0.8209",
            ask="0.8210",
            quote_timestamp_ms=QUOTE_TS,
            evaluation_timestamp_ms=EVAL_TS,
            tick_sz="0.0001",
            freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
        )
    )
    assert decision.permit is not None
    return decision.permit


def _flatten_bundle(*, pos: str = "1") -> tuple[Any, Any, Any]:
    payload = _positions({"instId": TARGET, "pos": pos})
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=payload,
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    side = "SELL" if Decimal_pos(pos) > 0 else "BUY"
    permit_px = _price_permit(side=side, pos=pos)
    assert verdict.permit is not None
    assert verdict.flatten_plan is not None
    return verdict.permit, verdict.flatten_plan, permit_px, payload


def Decimal_pos(raw: str) -> int:
    return int(raw)


def test_positive_position_serializes_reduce_only_sell() -> None:
    flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="2")
    body = build_canary_flatten_submit_request_v1(
        permit=flatten_permit,
        plan=plan,
        price_permit=price_permit,
        positions_payload=payload,
    )
    assert body["side"] == "sell"
    assert body["reduceOnly"] is True
    assert body["ordType"] == "limit"
    assert body["sz"] == "2"
    assert body["px"] == "0.8209"
    assert body["instId"] == TARGET
    assert "posSide" not in body


def test_negative_position_serializes_reduce_only_buy() -> None:
    flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="-3")
    body = build_canary_flatten_submit_request_v1(
        permit=flatten_permit,
        plan=plan,
        price_permit=price_permit,
        positions_payload=payload,
    )
    assert body["side"] == "buy"
    assert body["reduceOnly"] is True
    assert body["sz"] == "3"
    assert body["px"] == "0.8210"


def test_qty_exactly_abs_observed_pos() -> None:
    flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="4")
    body = build_canary_flatten_submit_request_v1(
        permit=flatten_permit,
        plan=plan,
        price_permit=price_permit,
        positions_payload=payload,
        requested_qty="4",
    )
    assert body["sz"] == "4"


def test_oversize_flatten_rejected() -> None:
    flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="1")
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="OVERSIZE_FLATTEN"):
        build_canary_flatten_submit_request_v1(
            permit=flatten_permit,
            plan=plan,
            price_permit=price_permit,
            positions_payload=payload,
            requested_qty="2",
        )


def test_zero_position_flatten_rejected() -> None:
    flatten_permit, plan, price_permit, _payload = _flatten_bundle(pos="1")
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="ZERO_POSITION"):
        build_canary_flatten_submit_request_v1(
            permit=flatten_permit,
            plan=plan,
            price_permit=price_permit,
            positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        )


def test_side_mismatch_rejected() -> None:
    flatten_permit, plan, _sell_price, payload = _flatten_bundle(pos="1")
    buy_price = _price_permit(side="BUY", pos="-1")
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="SIDE_MISMATCH"):
        build_canary_flatten_submit_request_v1(
            permit=flatten_permit,
            plan=plan,
            price_permit=buy_price,
            positions_payload=payload,
        )


def test_instrument_mismatch_rejected() -> None:
    flatten_permit, plan, price_permit, _payload = _flatten_bundle(pos="1")
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="INSTRUMENT"):
        build_canary_flatten_submit_request_v1(
            permit=flatten_permit,
            plan=plan,
            price_permit=price_permit,
            positions_payload=_positions(),
        )


def test_other_open_instrument_fails_account_wide_cap() -> None:
    flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="1")
    with pytest.raises(
        LiveCanaryFlattenSubmitTransportError,
        match="ACCOUNT_WIDE_OPEN_POSITION_CAP:DENY_OTHER_OPEN_INSTRUMENT_PRESENT",
    ):
        build_canary_flatten_submit_request_v1(
            permit=flatten_permit,
            plan=plan,
            price_permit=price_permit,
            positions_payload=_positions(
                {"instId": TARGET, "pos": "1"},
                {"instId": "BTC-USDT-SWAP", "pos": "1"},
            ),
        )


def test_missing_permit_rejected() -> None:
    _flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="1")
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="FLATTEN_PERMIT_MISSING"):
        run_canary_flatten_submit_transport_v1(
            permit=None,
            plan=plan,
            price_permit=price_permit,
            positions_payload=payload,
            transport=RecordingFakeCanaryTransportV1(),
        )


def test_malformed_permit_rejected() -> None:
    _flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="1")
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="FLATTEN_PERMIT"):
        build_canary_flatten_submit_request_v1(
            permit="not-a-permit",  # type: ignore[arg-type]
            plan=plan,
            price_permit=price_permit,
            positions_payload=payload,
        )


def test_dedicated_flatten_path_uses_fake_transport_and_trade_order() -> None:
    flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="1")
    fake = RecordingFakeCanaryTransportV1()
    result = run_canary_flatten_submit_transport_v1(
        permit=flatten_permit,
        plan=plan,
        price_permit=price_permit,
        positions_payload=payload,
        transport=fake,
    )
    assert DEDICATED_FLATTEN_TRANSPORT_IMPLEMENTED is True
    assert REDUCE_ONLY_FLATTEN_INTENT_IMPLEMENTED is True
    assert result["FLATTEN_SUBMIT_ENDPOINT"] == ENDPOINT_SUBMIT == "/api/v5/trade/order"
    assert result["CLOSE_POSITION_ENDPOINT_ALLOWLISTED"] is False
    assert CLOSE_POSITION_ENDPOINT_ALLOWLISTED is False
    assert result["MARKET_PATH_USED"] is False
    assert result["PRODUCTIVE_WIRE_SEND"] is False
    assert result["LIVE_FLATTEN_PROVABILITY"] == LIVE_FLATTEN_PROVABILITY == "UNPROVEN"
    assert fake.calls
    assert fake.calls[0].endpoint == ENDPOINT_SUBMIT
    assert fake.calls[0].method == "POST"
    wire = json.loads(fake.calls[0].body_text)
    assert wire["reduceOnly"] is True
    assert wire["ordType"] == "limit"
    assert "/trade/close-position" not in fake.calls[0].endpoint
    assert result["counters"]["FLATTEN_SUBMIT_COUNT"] == 1
    assert result["counters"]["ENTRY_SUBMIT_COUNT"] == 0


def test_entry_path_remains_separate_from_flatten() -> None:
    entry_src = inspect.getsource(run_canary_submit_transport_v1)
    flatten_src = inspect.getsource(run_canary_flatten_submit_transport_v1)
    assert "post_flatten_order" not in entry_src
    assert "build_minimum_valid_canary_flatten_order_plan_v1" not in entry_src
    assert "run_canary_submit_transport_v1" not in flatten_src
    assert "post_entry_order" not in flatten_src
    assert "post_flatten_order" in flatten_src


def test_flatten_transport_rejects_entry_permit() -> None:
    _flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="1")
    entry = CanaryEntrySubmitPermitV1(owner_go=OWNER_GO, clordid="entry", permit_id="e1")
    with pytest.raises(
        LiveCanaryFlattenSubmitTransportError, match="ENTRY_PERMIT_CANNOT_USE_FLATTEN_TRANSPORT"
    ):
        run_canary_flatten_submit_transport_v1(
            permit=_flatten_permit,
            plan=plan,
            price_permit=price_permit,
            positions_payload=payload,
            transport=RecordingFakeCanaryTransportV1(),
            entry_permit=entry,
        )


def test_entry_http_rejects_flatten_permit_and_reduce_only() -> None:
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=RecordingFakeCanaryTransportV1(),
    )
    flatten_http = CanaryFlattenHttpPermitV1(owner_go=OWNER_GO, clordid="flat", permit_id="f1")
    with pytest.raises(LiveCanaryHttpError, match="FLATTEN_PERMIT_CANNOT_USE_ENTRY_TRANSPORT"):
        client.post_entry_order(
            permit=flatten_http,  # type: ignore[arg-type]
            body_text='{"ordType":"limit","px":"1","sz":"1"}',
            headers={"User-Agent": "test"},
        )
    entry = CanaryEntrySubmitPermitV1(owner_go=OWNER_GO, clordid="entry", permit_id="e1")
    with pytest.raises(LiveCanaryHttpError, match="ENTRY_REDUCE_ONLY_FORBIDDEN"):
        client.post_entry_order(
            permit=entry,
            body_text='{"ordType":"limit","px":"1","sz":"1","reduceOnly":true}',
            headers={"User-Agent": "test"},
        )


def test_flatten_http_rejects_entry_permit_and_missing_reduce_only() -> None:
    client = LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=RecordingFakeCanaryTransportV1(),
    )
    entry = CanaryEntrySubmitPermitV1(owner_go=OWNER_GO, clordid="entry", permit_id="e1")
    with pytest.raises(LiveCanaryHttpError, match="FLATTEN_HTTP_PERMIT_KIND_INVALID"):
        client.post_flatten_order(
            permit=entry,  # type: ignore[arg-type]
            body_text='{"ordType":"limit","px":"1","sz":"1","reduceOnly":true}',
            headers={"User-Agent": "test"},
        )
    flatten_http = CanaryFlattenHttpPermitV1(owner_go=OWNER_GO, clordid="flat", permit_id="f1")
    with pytest.raises(LiveCanaryHttpError, match="FLATTEN_REDUCE_ONLY_REQUIRED"):
        client.post_flatten_order(
            permit=flatten_http,
            body_text='{"ordType":"limit","px":"1","sz":"1"}',
            headers={"User-Agent": "test"},
        )
    with pytest.raises(LiveCanaryHttpError, match="FLATTEN_MARKET_FORBIDDEN"):
        client.post_flatten_order(
            permit=flatten_http,
            body_text='{"ordType":"market","px":"1","sz":"1","reduceOnly":true}',
            headers={"User-Agent": "test"},
        )


def test_urllib_and_live_contact_transport_forbidden() -> None:
    flatten_permit, plan, price_permit, payload = _flatten_bundle(pos="1")
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="PRODUCTIVE_WIRE"):
        run_canary_flatten_submit_transport_v1(
            permit=flatten_permit,
            plan=plan,
            price_permit=price_permit,
            positions_payload=payload,
            transport=UrllibLiveCanaryTransportV1(wire_send_enabled=False),
        )
    liveish = RecordingFakeCanaryTransportV1()
    liveish.venue_live_contact = True
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="PRODUCTIVE_WIRE"):
        run_canary_flatten_submit_transport_v1(
            permit=flatten_permit,
            plan=plan,
            price_permit=price_permit,
            positions_payload=payload,
            transport=liveish,
        )
    with pytest.raises(LiveCanaryFlattenSubmitTransportError, match="PRODUCTIVE_WIRE"):
        run_canary_flatten_submit_transport_v1(
            permit=flatten_permit,
            plan=plan,
            price_permit=price_permit,
            positions_payload=payload,
            transport=RecordingFakeCanaryTransportV1(),
            allow_productive_wire_send=True,
        )


def test_global_invariants_unchanged() -> None:
    assert ORDER_COUNT_LIMIT == 1
    assert POSITION_COUNT_LIMIT == 1
    assert POST_ENDPOINTS_GATED == (
        "/api/v5/trade/order",
        "/api/v5/trade/cancel-order",
    )
    assert "/api/v5/trade/close-position" not in POST_ENDPOINTS_GATED
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    assert LIVE_FLATTEN_PROVABILITY == "UNPROVEN"
    instruments = {
        "code": "0",
        "data": [
            {
                "instId": TARGET,
                "instType": "FUTURES",
                "ruleType": "xperp",
                "minSz": "1",
                "lotSz": "1",
                "tickSz": "0.0001",
                "ctVal": "1",
                "ctValCcy": "SUI",
                "maxLmtSz": "100000000",
                "maxMktSz": "100000",
            }
        ],
    }
    ticker = {"code": "0", "data": [{"instId": TARGET, "last": "0.8209"}]}
    entry_plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=instruments,
        ticker_payload=ticker,
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        pretrade_decision_id="test-fresh-decision-dedicated-flatten",
    )
    assert "reduceOnly" not in entry_plan.venue_native_payload
    flatten_permit = issue_canary_flatten_submit_permit_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert flatten_permit.price_gate_status == FLATTEN_LIMIT_PRICE_GATE_STATUS
    assert (
        flatten_permit.kind
        != CanaryEntrySubmitPermitV1(owner_go=OWNER_GO, clordid="x", permit_id="y").kind
    )


def test_serialize_without_permit_still_unbound() -> None:
    _permit, plan, _price, _payload = _flatten_bundle(pos="1")
    with pytest.raises(Exception, match="FLATTEN_NAKED_PX_FAIL_CLOSED"):
        serialize_canary_flatten_venue_native_payload_v1(plan, px="0.8209")
