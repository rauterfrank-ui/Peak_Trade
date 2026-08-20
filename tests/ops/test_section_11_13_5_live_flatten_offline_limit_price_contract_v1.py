"""LF-05 offline flatten LIMIT price-contract tests. No network, no submit."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    REDUCE_ONLY_WIRE_TYPE_STATUS,
    build_venue_native_order_body_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_ORDER_TYPE,
    ENDPOINT_CANCEL,
    ENDPOINT_SUBMIT,
    GET_ENDPOINTS_PUBLIC,
    ORDER_COUNT_LIMIT,
    POST_ENDPOINTS_GATED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    ACCOUNT_MUTATION_EFFECT_NONE,
    FINITE_PRICE_BOUND_STATUS,
    FLATTEN_PRICE_POLICY_IMPLEMENTED,
    FLATTEN_PRICE_POLICY_OPERATIONALLY_USABLE,
    LF_05_IMPLEMENTATION_STATUS,
    LIFECYCLE_FLATTEN_RUNTIME_REACHABLE,
    LIVE_FLATTEN_PROVABILITY_STATUS,
    NETWORK_EFFECT_NONE,
    ORDER_EFFECT_NONE,
    QUOTE_FRESHNESS_STATUS,
    SIDE_AWARE_QUOTE_SELECTION_STATUS,
    TICK_NORMALIZATION_STATUS,
    FlattenPriceDecisionV1,
    FlattenPriceInputV1,
    FlattenPricePermitV1,
    LiveCanaryFlattenLimitPriceError,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_orchestration_contract_v1 import (
    evaluate_canary_flatten_orchestration_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.lifecycle_v1 import (
    build_lifecycle_and_closeout_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    FLATTEN_LIMIT_PRICE_GATE_STATUS,
    LiveCanaryOrderPlanError,
    serialize_canary_flatten_venue_native_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    observe_target_position_flatten_candidate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_transport_v1 import (
    run_canary_submit_transport_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "c6e4400c33fa3b4eb31dff202c936a61272486ed"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"


def _complete(**overrides: Any) -> FlattenPriceInputV1:
    payload: dict[str, Any] = {
        "flatten_side": "SELL",
        "observed_signed_pos": "1",
        "bid": "64805.6",
        "ask": "64805.7",
        "quote_timestamp_ms": QUOTE_TS,
        "evaluation_timestamp_ms": EVAL_TS,
        "tick_sz": "0.1",
    }
    payload.update(overrides)
    return FlattenPriceInputV1(**payload)


def _assert_fail_closed(decision: FlattenPriceDecisionV1) -> None:
    assert decision.permit_issued is False
    assert decision.permit is None
    assert decision.limit_price is None
    assert decision.selected_quote_side is None
    assert decision.operationally_usable is False
    assert decision.submit_reachable is False
    assert decision.implementation_status == LF_05_IMPLEMENTATION_STATUS
    assert decision.quote_selection_status == SIDE_AWARE_QUOTE_SELECTION_STATUS == "UNPROVEN"
    assert decision.freshness_status == QUOTE_FRESHNESS_STATUS == "UNPROVEN"
    assert decision.finite_bound_status == FINITE_PRICE_BOUND_STATUS == "UNPROVEN"
    assert decision.tick_normalization_status == TICK_NORMALIZATION_STATUS == "UNPROVEN"
    assert decision.price_gate_status == FLATTEN_LIMIT_PRICE_GATE_STATUS
    assert decision.network_effect == NETWORK_EFFECT_NONE == "none"
    assert decision.order_effect == ORDER_EFFECT_NONE == "none"
    assert decision.account_mutation_effect == ACCOUNT_MUTATION_EFFECT_NONE == "none"
    assert decision.live_flatten_provability == LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
    assert decision.lifecycle_flatten_runtime_reachable is False
    assert FLATTEN_PRICE_POLICY_IMPLEMENTED is False
    assert FLATTEN_PRICE_POLICY_OPERATIONALLY_USABLE is False
    assert LIFECYCLE_FLATTEN_RUNTIME_REACHABLE is False


CASE_MATRIX: list[tuple[str, FlattenPriceInputV1, str]] = [
    ("LONG_POSITION_SELL_SELECTION", _complete(), "QUOTE_FRESHNESS_THRESHOLD_UNPROVEN"),
    (
        "SHORT_POSITION_BUY_SELECTION",
        _complete(flatten_side="BUY", observed_signed_pos="-2"),
        "QUOTE_FRESHNESS_THRESHOLD_UNPROVEN",
    ),
    ("QUOTE_MISSING", _complete(bid=None, ask=None), "QUOTE_MISSING"),
    ("BID_MISSING", _complete(bid=None), "BID_MISSING"),
    ("ASK_MISSING", _complete(ask=""), "ASK_MISSING"),
    ("MALFORMED_QUOTE", _complete(bid="not-a-price"), "MALFORMED_QUOTE"),
    ("NON_FINITE_QUOTE", _complete(ask="inf"), "NON_FINITE_QUOTE"),
    ("ZERO_OR_NEGATIVE_QUOTE", _complete(bid="0"), "ZERO_OR_NEGATIVE_QUOTE"),
    ("FRESH_QUOTE", _complete(), "QUOTE_FRESHNESS_THRESHOLD_UNPROVEN"),
    ("STALE_QUOTE", _complete(quote_timestamp_ms="1000"), "QUOTE_FRESHNESS_THRESHOLD_UNPROVEN"),
    ("FRESHNESS_UNKNOWN", _complete(quote_timestamp_ms=None), "FRESHNESS_UNKNOWN"),
    ("MALFORMED_TIMESTAMP", _complete(evaluation_timestamp_ms="later"), "MALFORMED_TIMESTAMP"),
    (
        "FUTURE_TIMESTAMP",
        _complete(quote_timestamp_ms="1787145057000", evaluation_timestamp_ms=QUOTE_TS),
        "FUTURE_TIMESTAMP",
    ),
    ("TICK_SIZE_VALID", _complete(tick_sz="0.1"), "QUOTE_FRESHNESS_THRESHOLD_UNPROVEN"),
    ("TICK_SIZE_MISSING", _complete(tick_sz=None), "TICK_SIZE_MISSING"),
    ("TICK_SIZE_INVALID", _complete(tick_sz="-0.1"), "TICK_SIZE_INVALID"),
    (
        "BUY_TICK_NORMALIZATION",
        _complete(flatten_side="BUY", observed_signed_pos="-1"),
        "TICK_NORMALIZATION_UNPROVEN",
    ),
    ("SELL_TICK_NORMALIZATION", _complete(), "TICK_NORMALIZATION_UNPROVEN"),
    ("FINITE_BOUND_VALID", _complete(), "FINITE_PRICE_BOUND_UNPROVEN"),
    (
        "FINITE_BOUND_MISSING",
        _complete(finite_bound=None, bound_kind=None),
        "FINITE_PRICE_BOUND_UNPROVEN",
    ),
    (
        "FINITE_BOUND_EXCEEDED",
        _complete(finite_bound="1", bound_kind="TICKS"),
        "FINITE_BOUND_NOT_CANONICALLY_BOUND",
    ),
    ("ROUNDING_CAUSES_BOUND_VIOLATION", _complete(), "TICK_NORMALIZATION_UNPROVEN"),
    ("UNKNOWN_SIDE", _complete(flatten_side="FLAT"), "UNKNOWN_SIDE"),
    ("ZERO_POSITION", _complete(observed_signed_pos="0"), "ZERO_POSITION"),
    (
        "INCONSISTENT_POSITION",
        _complete(flatten_side="BUY", observed_signed_pos="1"),
        "INCONSISTENT_POSITION",
    ),
    ("DETERMINISTIC_REPEAT", _complete(), "QUOTE_FRESHNESS_THRESHOLD_UNPROVEN"),
]


@pytest.mark.parametrize(
    ("case", "price_input", "expected_reason"),
    CASE_MATRIX,
    ids=[row[0] for row in CASE_MATRIX],
)
def test_lf05_price_contract_fail_closed_matrix(
    case: str,
    price_input: FlattenPriceInputV1,
    expected_reason: str,
) -> None:
    decision = evaluate_canary_flatten_limit_price_contract_v1(price_input)
    _assert_fail_closed(decision)
    assert expected_reason in decision.reject_reasons
    if case == "LONG_POSITION_SELL_SELECTION":
        assert decision.flatten_side == "SELL"
    if case == "SHORT_POSITION_BUY_SELECTION":
        assert decision.flatten_side == "BUY"
    if case == "DETERMINISTIC_REPEAT":
        again = evaluate_canary_flatten_limit_price_contract_v1(price_input)
        assert again.to_dict() == decision.to_dict()


def test_long_observed_position_still_maps_to_sell_without_price_permit() -> None:
    observed = observe_target_position_flatten_candidate_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "2"}]},
    )
    assert observed.candidate_flatten_side == "SELL"
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        _complete(flatten_side=observed.candidate_flatten_side, observed_signed_pos="2")
    )
    _assert_fail_closed(decision)
    assert decision.flatten_side == "SELL"
    assert "SIDE_AWARE_QUOTE_SELECTION_UNPROVEN" in decision.reject_reasons


def test_short_observed_position_still_maps_to_buy_without_price_permit() -> None:
    observed = observe_target_position_flatten_candidate_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "-3"}]},
    )
    assert observed.candidate_flatten_side == "BUY"
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        _complete(flatten_side="BUY", observed_signed_pos="-3")
    )
    _assert_fail_closed(decision)
    assert decision.flatten_side == "BUY"


def test_invented_freshness_threshold_and_bound_are_rejected() -> None:
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        _complete(freshness_threshold_ms="5000", finite_bound="10", bound_kind="TICKS")
    )
    _assert_fail_closed(decision)
    assert "FRESHNESS_THRESHOLD_NOT_CANONICALLY_BOUND" in decision.reject_reasons
    assert "FINITE_BOUND_NOT_CANONICALLY_BOUND" in decision.reject_reasons
    assert decision.permit_issued is False


def test_price_permit_type_cannot_be_constructed() -> None:
    with pytest.raises(LiveCanaryFlattenLimitPriceError, match="FLATTEN_PRICE_PERMIT_FORBIDDEN"):
        FlattenPricePermitV1(
            flatten_side="SELL",
            limit_price="64805.6",
            selected_quote_side="BID",
            tick_sz="0.1",
        )


def test_existing_flatten_serialization_remains_unbound() -> None:
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.permit_issued is True
    assert verdict.submit_reachable is False
    assert verdict.flatten_plan is not None
    with pytest.raises(LiveCanaryOrderPlanError, match="FLATTEN_LIMIT_PRICE_POLICY_UNBOUND"):
        serialize_canary_flatten_venue_native_payload_v1(verdict.flatten_plan, px="64805.6")


def test_entry_semantics_and_policy_surfaces_unchanged() -> None:
    body = build_venue_native_order_body_v1(
        client_order_id="c1",
        instrument=TARGET,
        order_type="LIMIT",
        side="buy",
        quantity="1",
        px="10000",
    )
    assert "reduceOnly" not in body
    assert REDUCE_ONLY_WIRE_TYPE_STATUS == "UNPROVEN"
    assert DEFAULT_ORDER_TYPE == "LIMIT"
    assert ORDER_COUNT_LIMIT == 1
    assert POST_ENDPOINTS_GATED == (
        "/api/v5/trade/order",
        "/api/v5/trade/cancel-order",
    )
    assert ENDPOINT_SUBMIT == "/api/v5/trade/order"
    assert ENDPOINT_CANCEL == "/api/v5/trade/cancel-order"
    assert "/api/v5/trade/close-position" not in POST_ENDPOINTS_GATED
    assert "/api/v5/market/ticker" in GET_ENDPOINTS_PUBLIC
    lifecycle = build_lifecycle_and_closeout_contract_v1()
    assert lifecycle["ACTIVATED"] is False
    assert lifecycle["order_type_semantics"] == "LIMIT_ONLY_NO_MARKET"


def test_lf05_offline_path_is_not_wired_into_transport_or_runner() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import (
        flatten_limit_price_contract_v1,
        http_client_v1,
        runner_v1,
    )

    src = inspect.getsource(flatten_limit_price_contract_v1)
    transport_src = inspect.getsource(run_canary_submit_transport_v1)
    http_src = inspect.getsource(http_client_v1)
    runner_src = inspect.getsource(runner_v1)
    assert "urllib" not in src
    assert "post_flatten_order" not in src
    assert "post_entry_order" not in src
    for banned in (
        "evaluate_canary_flatten_limit_price_contract_v1",
        "FlattenPricePermitV1",
        "post_flatten_order",
    ):
        assert banned not in transport_src
        assert banned not in runner_src
        assert banned not in http_src
