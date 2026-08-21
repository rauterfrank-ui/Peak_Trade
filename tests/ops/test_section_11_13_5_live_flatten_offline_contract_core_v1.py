"""LF-01/LF-02 offline flatten contract-core tests. No network, no submit."""

from __future__ import annotations

import inspect
import json
from typing import Any, Mapping

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    REDUCE_ONLY_WIRE_TYPE_STATUS,
    OkxResponseMapperError,
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_CANCEL,
    ENDPOINT_SUBMIT,
    ORDER_COUNT_LIMIT,
    POST_ENDPOINTS_GATED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.lifecycle_v1 import (
    build_lifecycle_and_closeout_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    FLATTEN_LIMIT_PRICE_GATE_STATUS,
    LiveCanaryOrderPlanError,
    build_minimum_valid_canary_flatten_order_plan_v1,
    build_minimum_valid_canary_order_plan_v1,
    serialize_canary_clordid_v1,
    serialize_canary_flatten_clordid_v1,
    serialize_canary_flatten_venue_native_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    observe_target_position_flatten_candidate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    run_canary_submit_transport_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "aa421d84cd0223146ab63f94405e81ed813d40c3"
TARGET = DEFAULT_INSTRUMENT_ID
INSTRUMENTS = {
    "code": "0",
    "data": [
        {
            "instId": TARGET,
            "instType": "FUTURES",
            "ruleType": "xperp",
            "minSz": "1",
            "lotSz": "1",
            "tickSz": "0.1",
            "ctVal": "0.0001",
            "ctValCcy": "BTC",
        }
    ],
}
TICKER = {"code": "0", "data": [{"instId": TARGET, "last": "63028.1"}]}
ENTRY_BODY_KEYS = {
    "instId",
    "tdMode",
    "side",
    "ordType",
    "sz",
    "px",
    "clOrdId",
}


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _entry_body(**overrides: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "client_order_id": "c1",
        "instrument": TARGET,
        "order_type": "LIMIT",
        "side": "buy",
        "quantity": "1",
        "px": "10000",
    }
    kwargs.update(overrides)
    return build_venue_native_order_body_v1(**kwargs)


def test_entry_payload_omits_reduce_only_by_default() -> None:
    body = _entry_body()
    assert "reduceOnly" not in body
    assert set(body) == ENTRY_BODY_KEYS
    assert REDUCE_ONLY_WIRE_TYPE_STATUS == "UNPROVEN"


def test_entry_payload_omits_reduce_only_when_explicitly_false() -> None:
    body = _entry_body(reduce_only=False)
    assert "reduceOnly" not in body
    assert set(body) == ENTRY_BODY_KEYS


def test_existing_entry_body_contract_unchanged() -> None:
    body = _entry_body()
    assert body["clOrdId"] == "c1"
    assert body["instId"] == TARGET
    assert body["tdMode"] == "cross"
    assert body["side"] == "buy"
    assert body["ordType"] == "limit"
    assert body["sz"] == "1"
    assert body["px"] == "10000"
    assert "posSide" not in body
    assert "client_order_id" not in body


def test_explicit_flatten_serialization_contains_reduce_only_only_when_requested() -> None:
    omitted = _entry_body()
    requested = _entry_body(reduce_only=True)
    assert "reduceOnly" not in omitted
    assert requested["reduceOnly"] is True
    assert set(requested) == ENTRY_BODY_KEYS | {"reduceOnly"}
    assert requested["ordType"] == "limit"
    assert "posSide" not in requested
    wire = json.dumps(requested, separators=(",", ":"), ensure_ascii=True)
    assert '"reduceOnly":true' in wire
    assert REDUCE_ONLY_WIRE_TYPE_STATUS == "UNPROVEN"


def test_reduce_only_flag_rejects_non_bool() -> None:
    with pytest.raises(OkxResponseMapperError, match="REDUCE_ONLY_FLAG_INVALID"):
        _entry_body(reduce_only=1)  # type: ignore[arg-type]


def test_observed_positive_position_derives_sell() -> None:
    observed = observe_target_position_flatten_candidate_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "2"}),
    )
    assert observed.candidate_flatten_side == "SELL"
    assert observed.candidate_flatten_qty == observed.signed_pos == 2
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "2"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        submitted_entry_sz="1",
    )
    assert plan.side == "SELL"
    assert plan.quantity == "2"
    assert plan.reduce_only is True
    assert plan.submitted_entry_sz_used is False


def test_observed_negative_position_derives_buy() -> None:
    observed = observe_target_position_flatten_candidate_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "-3"}),
    )
    assert observed.candidate_flatten_side == "BUY"
    assert observed.signed_pos == -3
    assert observed.candidate_flatten_qty == 3
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "-3"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        submitted_entry_sz="1",
    )
    assert plan.side == "BUY"
    assert plan.quantity == "3"
    assert plan.reduce_only is True


def test_observed_zero_cannot_create_flatten_order() -> None:
    with pytest.raises(LiveCanaryPositionObservationError, match="ZERO_POSITION_NO_FLATTEN_ORDER"):
        observe_target_position_flatten_candidate_v1(
            positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        )
    with pytest.raises(LiveCanaryOrderPlanError, match="ZERO_POSITION_NO_FLATTEN_ORDER"):
        build_minimum_valid_canary_flatten_order_plan_v1(
            positions_payload=_positions({"instId": TARGET, "pos": "0"}),
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_flatten_qty_derives_from_observed_position_not_submitted_entry_sz() -> None:
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "4"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
        submitted_entry_sz="1",
    )
    assert plan.quantity == "4"
    assert plan.quantity != "1"
    assert plan.submitted_entry_sz_used is False
    source = inspect.getsource(build_minimum_valid_canary_flatten_order_plan_v1)
    assert "submitted_entry_sz" in source
    assert "del submitted_entry_sz" in source


def test_malformed_position_cannot_authorize_flatten() -> None:
    with pytest.raises(LiveCanaryPositionObservationError, match="POSITION_SIZE_UNPARSEABLE"):
        observe_target_position_flatten_candidate_v1(
            positions_payload=_positions({"instId": TARGET, "pos": "not-a-number"}),
        )
    with pytest.raises(LiveCanaryPositionObservationError, match="POSITION_SIZE_MISSING"):
        observe_target_position_flatten_candidate_v1(
            positions_payload=_positions({"instId": TARGET}),
        )
    with pytest.raises(LiveCanaryOrderPlanError, match="POSITION_SIZE_MISSING"):
        build_minimum_valid_canary_flatten_order_plan_v1(
            positions_payload=_positions({"instId": TARGET, "pos": ""}),
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_missing_target_instrument_cannot_authorize_flatten() -> None:
    with pytest.raises(LiveCanaryPositionObservationError, match="TARGET_INSTRUMENT_NOT_OBSERVED"):
        observe_target_position_flatten_candidate_v1(
            positions_payload=_positions({"instId": "BTC-USDT-SWAP", "pos": "1"}),
        )
    with pytest.raises(LiveCanaryOrderPlanError, match="TARGET_INSTRUMENT_NOT_OBSERVED"):
        build_minimum_valid_canary_flatten_order_plan_v1(
            positions_payload={"code": "0", "data": []},
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_ambiguous_multiple_authoritative_target_rows_cannot_authorize_flatten() -> None:
    payload = _positions(
        {"instId": TARGET, "pos": "1"},
        {"instId": TARGET, "pos": "1"},
    )
    with pytest.raises(LiveCanaryPositionObservationError, match="AMBIGUOUS_TARGET_POSITION_ROWS"):
        observe_target_position_flatten_candidate_v1(positions_payload=payload)
    with pytest.raises(LiveCanaryOrderPlanError, match="AMBIGUOUS_TARGET_POSITION_ROWS"):
        build_minimum_valid_canary_flatten_order_plan_v1(
            positions_payload=payload,
            owner_go=OWNER_GO,
            origin_main_sha=ORIGIN_SHA,
        )


def test_entry_and_flatten_clordid_identities_do_not_alias() -> None:
    entry = serialize_canary_clordid_v1(owner_go=OWNER_GO, origin_main_sha=ORIGIN_SHA)
    flatten = serialize_canary_flatten_clordid_v1(owner_go=OWNER_GO, origin_main_sha=ORIGIN_SHA)
    assert entry != flatten
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert plan.clordid == flatten
    assert plan.clordid != entry


def test_post_endpoints_gated_and_entry_order_count_limit_unchanged() -> None:
    assert POST_ENDPOINTS_GATED == (
        "/api/v5/trade/order",
        "/api/v5/trade/cancel-order",
    )
    assert ENDPOINT_SUBMIT == "/api/v5/trade/order"
    assert ENDPOINT_CANCEL == "/api/v5/trade/cancel-order"
    assert "/api/v5/trade/close-position" not in POST_ENDPOINTS_GATED
    assert ORDER_COUNT_LIMIT == 1


def test_entry_plan_remains_entry_only_and_omits_reduce_only() -> None:
    plan = build_minimum_valid_canary_order_plan_v1(
        instruments_payload=INSTRUMENTS,
        ticker_payload=TICKER,
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert plan.side == "BUY"
    assert plan.quantity == "1"
    assert "reduceOnly" not in plan.venue_native_payload
    assert set(plan.venue_native_payload) == ENTRY_BODY_KEYS
    source = inspect.getsource(build_minimum_valid_canary_order_plan_v1)
    assert "reduce_only" not in source


def test_testnet_and_entry_bodies_backward_compatible_without_explicit_reduce_only() -> None:
    testnet = build_venue_native_order_body_v1(
        client_order_id="c1",
        instrument="BTC-USD_UM_XPERP-310328",
        order_type="LIMIT",
        side="buy",
        quantity="1",
        px="10000",
    )
    assert "reduceOnly" not in testnet
    assert testnet["ordType"] == "limit"
    assert set(testnet) == ENTRY_BODY_KEYS


def test_flatten_plan_price_gate_fails_closed_and_is_not_wire_ready() -> None:
    plan = build_minimum_valid_canary_flatten_order_plan_v1(
        positions_payload=_positions({"instId": TARGET, "pos": "1"}),
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert plan.order_type == "LIMIT"
    assert plan.venue_native_payload is None
    assert plan.limit_price is None
    assert plan.price_gate_status == FLATTEN_LIMIT_PRICE_GATE_STATUS
    with pytest.raises(LiveCanaryOrderPlanError, match="FLATTEN_LIMIT_PRICE_POLICY_UNBOUND"):
        serialize_canary_flatten_venue_native_payload_v1(plan, px="63028.1")


def test_flatten_contract_is_not_wired_into_execute_or_lifecycle() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import http_client_v1

    lifecycle = build_lifecycle_and_closeout_contract_v1()
    assert lifecycle["ACTIVATED"] is False
    assert lifecycle["order_count_limit"] == 1
    assert lifecycle["order_type_semantics"] == "LIMIT_ONLY_NO_MARKET"
    transport_src = inspect.getsource(run_canary_submit_transport_v1)
    assert "build_minimum_valid_canary_flatten_order_plan_v1" not in transport_src
    assert "post_flatten_order" not in transport_src
    assert "issue_canary_flatten_submit_permit_v1" not in transport_src
    assert "evaluate_canary_flatten_orchestration_contract_v1" not in transport_src
    assert "evaluate_canary_flatten_lifecycle_failure_matrix_v1" not in transport_src
    http_src = inspect.getsource(http_client_v1)
    assert "post_flatten_order" in http_src
    assert "CanaryFlattenHttpPermitV1" in http_src
    assert "FLATTEN_SUBMIT" in http_src
