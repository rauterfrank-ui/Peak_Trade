"""LF-05 quote-locked flatten LIMIT price-policy tests. No network, no submit."""

from __future__ import annotations

import inspect
from decimal import Decimal
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
    FLATTEN_LIMIT_PRICE_GATE_BOUND,
    FLATTEN_PRICE_POLICY_FULLY_BOUND,
    FLATTEN_PRICE_POLICY_IMPLEMENTED,
    FLATTEN_PRICE_POLICY_OPERATIONALLY_USABLE,
    LF_05_IMPLEMENTATION_STATUS,
    LIFECYCLE_FLATTEN_RUNTIME_REACHABLE,
    LIVE_FLATTEN_PROVABILITY_STATUS,
    NETWORK_EFFECT_NONE,
    ORDER_EFFECT_NONE,
    OWNER_BINDING_STILL_REQUIRED,
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
CALLER_FRESHNESS_MS = "5000"


def _complete(**overrides: Any) -> FlattenPriceInputV1:
    payload: dict[str, Any] = {
        "flatten_side": "SELL",
        "observed_signed_pos": "1",
        "bid": "64805.6",
        "ask": "64805.7",
        "quote_timestamp_ms": QUOTE_TS,
        "evaluation_timestamp_ms": EVAL_TS,
        "tick_sz": "0.1",
        "freshness_threshold_ms": CALLER_FRESHNESS_MS,
    }
    payload.update(overrides)
    return FlattenPriceInputV1(**payload)


def _assert_rejected(decision: FlattenPriceDecisionV1, reason: str) -> None:
    assert decision.permit_issued is False
    assert decision.permit is None
    assert decision.limit_price is None
    assert decision.selected_quote_side is None
    assert decision.operationally_usable is False
    assert decision.submit_reachable is False
    assert decision.live_flatten_provability == LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
    assert decision.lifecycle_flatten_runtime_reachable is False
    assert decision.network_effect == NETWORK_EFFECT_NONE == "none"
    assert decision.order_effect == ORDER_EFFECT_NONE == "none"
    assert decision.account_mutation_effect == ACCOUNT_MUTATION_EFFECT_NONE == "none"
    assert reason in decision.reject_reasons


def _assert_issued(
    decision: FlattenPriceDecisionV1,
    *,
    side: str,
    quote_side: str,
    px: str,
) -> None:
    assert decision.permit_issued is True
    assert decision.permit is not None
    assert decision.flatten_side == side
    assert decision.selected_quote_side == quote_side
    assert decision.limit_price == px
    assert decision.permit.limit_price == px
    assert decision.permit.flatten_side == side
    assert decision.operationally_usable is True
    assert decision.submit_reachable is False
    assert decision.price_gate_status == FLATTEN_LIMIT_PRICE_GATE_BOUND
    assert decision.live_flatten_provability == "UNPROVEN"
    assert FLATTEN_PRICE_POLICY_IMPLEMENTED is True
    assert FLATTEN_PRICE_POLICY_OPERATIONALLY_USABLE is True
    assert FLATTEN_PRICE_POLICY_FULLY_BOUND is False


REJECT_MATRIX: list[tuple[str, FlattenPriceInputV1, str]] = [
    ("QUOTE_MISSING", _complete(bid=None, ask=None), "QUOTE_MISSING"),
    ("BID_MISSING", _complete(bid=None), "BID_MISSING"),
    ("ASK_MISSING", _complete(ask=""), "ASK_MISSING"),
    ("MALFORMED_QUOTE", _complete(bid="not-a-price"), "MALFORMED_QUOTE"),
    ("NON_FINITE_QUOTE", _complete(ask="inf"), "NON_FINITE_QUOTE"),
    ("ZERO_OR_NEGATIVE_QUOTE", _complete(bid="0"), "ZERO_OR_NEGATIVE_QUOTE"),
    ("NEGATIVE_QUOTE", _complete(ask="-1"), "ZERO_OR_NEGATIVE_QUOTE"),
    ("FRESHNESS_UNKNOWN", _complete(quote_timestamp_ms=None), "FRESHNESS_UNKNOWN"),
    ("MALFORMED_TIMESTAMP", _complete(evaluation_timestamp_ms="later"), "MALFORMED_TIMESTAMP"),
    (
        "FUTURE_TIMESTAMP",
        _complete(quote_timestamp_ms="1787145057000", evaluation_timestamp_ms=QUOTE_TS),
        "FUTURE_TIMESTAMP",
    ),
    ("TICK_SIZE_MISSING", _complete(tick_sz=None), "TICK_SIZE_MISSING"),
    ("TICK_SIZE_INVALID", _complete(tick_sz="-0.1"), "TICK_SIZE_INVALID"),
    ("UNKNOWN_SIDE", _complete(flatten_side="FLAT"), "UNKNOWN_SIDE"),
    ("ZERO_POSITION", _complete(observed_signed_pos="0"), "ZERO_POSITION"),
    (
        "INCONSISTENT_POSITION",
        _complete(flatten_side="BUY", observed_signed_pos="1"),
        "INCONSISTENT_POSITION",
    ),
    (
        "FRESHNESS_THRESHOLD_REQUIRED",
        _complete(freshness_threshold_ms=None),
        "FRESHNESS_THRESHOLD_REQUIRED",
    ),
    (
        "FRESHNESS_THRESHOLD_INVALID",
        _complete(freshness_threshold_ms="nope"),
        "FRESHNESS_THRESHOLD_INVALID",
    ),
    ("STALE_QUOTE", _complete(quote_timestamp_ms="1000"), "STALE_QUOTE"),
    (
        "FINITE_BOUND_NOT_OWNER_RATIFIED",
        _complete(finite_bound="10", bound_kind="TICKS"),
        "FINITE_BOUND_NOT_OWNER_RATIFIED",
    ),
]


@pytest.mark.parametrize(
    ("case", "price_input", "expected_reason"),
    REJECT_MATRIX,
    ids=[row[0] for row in REJECT_MATRIX],
)
def test_lf05_price_contract_rejects_invalid_inputs(
    case: str,
    price_input: FlattenPriceInputV1,
    expected_reason: str,
) -> None:
    del case
    decision = evaluate_canary_flatten_limit_price_contract_v1(price_input)
    _assert_rejected(decision, expected_reason)


def test_long_position_issues_sell_limit_at_bid() -> None:
    decision = evaluate_canary_flatten_limit_price_contract_v1(_complete())
    _assert_issued(decision, side="SELL", quote_side="BID", px="64805.6")


def test_short_position_issues_buy_limit_at_ask() -> None:
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        _complete(flatten_side="BUY", observed_signed_pos="-2")
    )
    _assert_issued(decision, side="BUY", quote_side="ASK", px="64805.7")


def test_sell_tick_rounding_rounds_down() -> None:
    decision = evaluate_canary_flatten_limit_price_contract_v1(_complete(bid="64805.65"))
    _assert_issued(decision, side="SELL", quote_side="BID", px="64805.6")
    assert Decimal(decision.limit_price) <= Decimal("64805.65")


def test_buy_tick_rounding_rounds_up() -> None:
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        _complete(flatten_side="BUY", observed_signed_pos="-1", ask="64805.65")
    )
    _assert_issued(decision, side="BUY", quote_side="ASK", px="64805.7")
    assert Decimal(decision.limit_price) >= Decimal("64805.65")


def test_non_finite_bid_rejected() -> None:
    decision = evaluate_canary_flatten_limit_price_contract_v1(_complete(bid="NaN"))
    _assert_rejected(decision, "NON_FINITE_QUOTE")


def test_missing_freshness_threshold_rejected_without_invented_default() -> None:
    src = inspect.getsource(evaluate_canary_flatten_limit_price_contract_v1)
    assert "5000" not in src
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        _complete(freshness_threshold_ms=None)
    )
    _assert_rejected(decision, "FRESHNESS_THRESHOLD_REQUIRED")
    assert "FRESHNESS_THRESHOLD_MS" in OWNER_BINDING_STILL_REQUIRED


def test_observed_long_maps_to_sell_with_price_permit() -> None:
    observed = observe_target_position_flatten_candidate_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "2"}]},
    )
    assert observed.candidate_flatten_side == "SELL"
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        _complete(flatten_side=observed.candidate_flatten_side, observed_signed_pos="2")
    )
    _assert_issued(decision, side="SELL", quote_side="BID", px="64805.6")


def test_observed_short_maps_to_buy_with_price_permit() -> None:
    observed = observe_target_position_flatten_candidate_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "-3"}]},
    )
    assert observed.candidate_flatten_side == "BUY"
    decision = evaluate_canary_flatten_limit_price_contract_v1(
        _complete(flatten_side="BUY", observed_signed_pos="-3")
    )
    _assert_issued(decision, side="BUY", quote_side="ASK", px="64805.7")


def test_deterministic_repeat_for_issued_permit() -> None:
    first = evaluate_canary_flatten_limit_price_contract_v1(_complete())
    second = evaluate_canary_flatten_limit_price_contract_v1(_complete())
    assert first.to_dict() == second.to_dict()


def test_naked_px_without_permit_still_unbound() -> None:
    verdict = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload={"code": "0", "data": [{"instId": TARGET, "pos": "1"}]},
        owner_go=OWNER_GO,
        origin_main_sha=ORIGIN_SHA,
    )
    assert verdict.flatten_plan is not None
    with pytest.raises(LiveCanaryOrderPlanError, match="FLATTEN_LIMIT_PRICE_POLICY_UNBOUND"):
        serialize_canary_flatten_venue_native_payload_v1(verdict.flatten_plan, px="64805.6")


def test_malformed_direct_permit_construction_rejected() -> None:
    with pytest.raises(LiveCanaryFlattenLimitPriceError, match="FLATTEN_PRICE_PERMIT"):
        FlattenPricePermitV1(
            flatten_side="SELL",
            limit_price="64805.6",
            selected_quote_side="ASK",
            tick_sz="0.1",
        )


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
    assert LF_05_IMPLEMENTATION_STATUS == "QUOTE_LOCKED_LIMIT_POLICY_V1"
    assert SIDE_AWARE_QUOTE_SELECTION_STATUS == "IMPLEMENTED_BID_FOR_SELL_ASK_FOR_BUY"
    assert QUOTE_FRESHNESS_STATUS == "CALLER_THRESHOLD_REQUIRED_NO_CANONICAL_DEFAULT"
    assert FINITE_PRICE_BOUND_STATUS == "QUOTE_LOCKED_NO_EXTRA_DEVIATION"
    assert TICK_NORMALIZATION_STATUS == "IMPLEMENTED_SELL_ROUND_DOWN_BUY_ROUND_UP"
    assert LIFECYCLE_FLATTEN_RUNTIME_REACHABLE is False


def test_lf05_offline_path_is_not_wired_into_entry_transport_or_runner() -> None:
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1 import (
        flatten_limit_price_contract_v1,
        runner_v1,
    )

    src = inspect.getsource(flatten_limit_price_contract_v1)
    transport_src = inspect.getsource(run_canary_submit_transport_v1)
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
    assert FLATTEN_LIMIT_PRICE_GATE_STATUS == "FAIL_CLOSED_UNTIL_SEPARATE_OWNER_GO"
