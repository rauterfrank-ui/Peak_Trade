"""Synthetic Demo sources: target exposure and full net execution stay distinct."""

from dataclasses import replace
from decimal import Decimal
import json

import pytest

from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from tests.ops.test_btc_demo_entry_reservation_v1 import demo_entry as demo_entry
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


def prepared(demo_entry):
    host, entry, reads, movement, instant, _ = demo_entry
    result, _ = host.reserve_testnet_entry_v1(
        entry=entry,
        reads=reads,
        movement_input=movement,
        clock=instant.timestamp,
    )
    record = host.budget.owner.risk_snapshot_v1()["state"]["sizing_bindings"][
        result.reservation.reservation_id
    ]
    sizing = ReservationSizingBindingV1.from_dict_v1(record)
    opening = cost.EntryExecutionCostObservationV1.from_dict_v1(
        json.loads(sizing.entry_cost_binding.observation_json)
    )
    args = dict(
        monetary_source=sizing.monetary_source,
        applied_input=sizing.applied_input,
        decision=sizing.decision,
        account_identity=host.budget.account,
        slot_id="LANE_3",
        cycle_id=entry.cycle.cycle_id,
    )
    direction = 1 if sizing.applied_input.selected_side.upper() == "LONG" else -1
    current = -direction * sizing.decision.final_quantity
    return opening, args, current


def book_depth(opening, *, total):
    sources = json.loads(opening.sources_json)
    book = sources["book"]["payload"]["data"][0]
    for side, direction in (("asks", 1), ("bids", -1)):
        price = Decimal(book[side][0][0])
        book[side] = [[str(price), str(total / 3)], [str(price + direction), str(total * 2 / 3)]]
    # Synthetic fixture body and decoded payload retain the same digest.
    from hashlib import sha256

    sources["book"]["body_sha256"] = sha256(
        cost.canonical(sources["book"]["payload"]).encode()
    ).hexdigest()
    return replace(opening, sources_json=cost.canonical(sources))


def test_full_delta_walks_both_levels_and_charges_fee_for_close_plus_open(demo_entry):
    opening, args, current = prepared(demo_entry)
    quantity = args["decision"].final_quantity
    opening = book_depth(opening, total=quantity * 2)
    result = cost.assess_net_reversal_execution_cost_v1(opening, current_contracts=current, **args)
    order = result["order_cost"]
    sources = json.loads(opening.sources_json)
    side = "asks" if current < 0 else "bids"
    levels = sources["book"]["payload"]["data"][0][side]
    value = sum((Decimal(price) * Decimal(count) for price, count in levels), Decimal(0))
    assert (
        Decimal(order["quantity"]) == abs(Decimal(result["signed_order_contracts"])) == quantity * 2
    )
    assert Decimal(result["target_contracts"]) == -current
    assert Decimal(order["fee_usdc"]) == value * args[
        "applied_input"
    ].instrument.contract_multiplier * Decimal(order["charged_rate"])
    assert Decimal(order["book_vwap"]) == value / (quantity * 2)
    target = cost.bind_entry_execution_cost_v1(opening, **args)
    close = cost.assess_closing_execution_cost_v1(
        target,
        monetary_source=args["monetary_source"],
        applied_input=args["applied_input"],
        decision=args["decision"],
    )
    assert Decimal(close["quantity"]) == quantity
    assert Decimal(order["fee_usdc"]) > Decimal(json.loads(target.receipt_json)["fee_usdc"])


def test_depth_sufficient_for_target_cannot_authorize_the_larger_net_order(demo_entry):
    opening, args, current = prepared(demo_entry)
    opening = book_depth(opening, total=args["decision"].final_quantity)
    assert cost.assess_opening_execution_cost_v1(opening, **args)
    with pytest.raises(ValueError, match="EXECUTABLE_BOOK_DEPTH_INSUFFICIENT"):
        cost.assess_net_reversal_execution_cost_v1(opening, current_contracts=current, **args)


def test_reversal_pricing_refuses_a_same_direction_target(demo_entry):
    opening, args, current = prepared(demo_entry)
    with pytest.raises(ValueError, match="OPPOSITE_TARGET_REQUIRED"):
        cost.assess_net_reversal_execution_cost_v1(opening, current_contracts=-current, **args)
