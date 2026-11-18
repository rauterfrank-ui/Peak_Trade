"""Budget changes, native units, and quantity-specific order-book impact."""

from dataclasses import replace
from decimal import Decimal
import socket

import pytest

from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_market_v1 import (
    IRYS_PAPER_SLOT,
    UP_PAPER_SLOT,
    ZKP_PAPER_SLOT,
    XperpPaperSlotV1,
)
from src.ops.bounded_peaktrade_system_composition_v1.zkp_paper_entry_v1 import ZkpPaperEntryV1
from src.ops.instrument_card_budget_assessment_v1 import assess_instrument_budget_v1
from tests.ops.test_zkp_lane1_paper_opening_v1 import REPO, _market


D = Decimal
SOPH = XperpPaperSlotV1("LANE_5", "SOPH", "310912")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("OFFLINE_ONLY")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)


def assess(market, budget="25", *, side="BUY", quantity=None):
    return assess_instrument_budget_v1(
        market=market, available_usdc=budget, side=side, quantity_contracts=quantity
    )


def test_historical_small_slot_to_adv_example_uses_current_profile():
    market = _market()
    market = replace(
        market,
        adv_usd=D("2009.390213333333333333333333"),
        policy=replace(market.policy, adv_participation_limit=D("0.005")),
    )
    full = assess(market)
    assert D(full["budget_to_adv_fraction"]) == D(25) / market.adv_usd
    assert D(full["budget_to_adv_fraction"]) * 100 == pytest.approx(D("1.24416"), abs=D("0.00001"))
    assert D(full["adv_order_value_cap_usd"]) == market.adv_usd * D("0.005")
    assert "ZKP_PAPER_ADV_PARTICIPATION_LIMIT" in full["reason_codes"]
    smaller = assess(market, "10")
    assert smaller["measurement_admitted"]
    assert "ZKP_PAPER_ADV_PARTICIPATION_LIMIT" not in smaller["reason_codes"]
    assert not full["productive_entry_admitted"]


@pytest.mark.parametrize("slot", [ZKP_PAPER_SLOT, UP_PAPER_SLOT, IRYS_PAPER_SLOT, SOPH])
def test_same_formula_uses_each_native_contract_and_changed_budget(slot):
    market = _market(slot=slot)
    big, small = assess(market, "25"), assess(market, "7")
    assert big["instrument_id"] == slot.instrument_id
    assert big["lane_id"] == slot.lane_id
    q = D(big["quantity_contracts"])
    unit = market.mark * market.native_contract.contract_size
    assert q * unit <= 25 < (q + market.lot_size) * unit
    assert D(small["quantity_contracts"]) < q
    assert D(small["budget_to_adv_fraction"]) == D(7) / market.adv_usd
    assert big["final_quantity_owner"] == "capital_risk_sizing_v1"


def test_currency_conversion_lot_grid_and_original_sizing_quantity():
    market = replace(_market(), usd_per_usdc=D("0.98"), lot_size=D("0.5"))
    capacity = assess(market, "25")
    assert D(capacity["available_budget_usd"]) == D("24.50")
    assert D(capacity["quantity_contracts"]) % D("0.5") == 0
    proposed = assess(market, "25", quantity=D("10.5"))
    assert proposed["quantity_source"] == "EXPLICIT_ORIGINAL_SIZING_QUANTITY"
    assert (
        D(proposed["mark_notional_usd"])
        == D("10.5") * market.mark * market.native_contract.contract_size
    )
    assert proposed["liquidity"] == market.assess_quantity_v1(side="BUY", quantity=D("10.5"))
    assert not proposed["fees_and_funding_included"]


def test_calculation_accepts_a_future_owner_budget_above_test_allocation():
    market = _market(depth=1000)
    test_phase = assess(market, "25")
    future_owner = assess(market, "50")
    assert D(future_owner["available_budget_usdc"]) == 50
    assert D(future_owner["quantity_contracts"]) > D(test_phase["quantity_contracts"])
    assert D(future_owner["budget_to_adv_fraction"]) == 2 * D(test_phase["budget_to_adv_fraction"])


def test_budget_quantity_consumes_book_depth_and_preserves_side_specific_impact():
    market = _market()
    tick = market.native_contract.tick_size
    market = replace(
        market,
        book=replace(
            market.book,
            asks=((market.mark + tick, D(5)), (market.mark + 2 * tick, D(100))),
            bids=((market.mark - tick, D(100)),),
        ),
    )
    buy, sell = assess(market), assess(market, side="SELL")
    assert D(buy["liquidity"]["open_price_usd"]) == market.mark + 2 * tick
    assert D(buy["adverse_slippage_usdc"]) > D(sell["adverse_slippage_usdc"])
    thin = replace(market, book=replace(market.book, asks=((market.mark + tick, D(5)),)))
    blocked = assess(thin)
    assert blocked["book_notional_usd"] is None
    assert "ZKP_PAPER_EXECUTABLE_DEPTH_INSUFFICIENT" in blocked["reason_codes"]
    assert not blocked["measurement_admitted"]


@pytest.mark.parametrize("budget", ["-1", "NaN", "Infinity", True])
def test_invalid_budget_does_not_produce_measurement(budget):
    with pytest.raises(ValueError, match="CARD_BUDGET_AMOUNT_INVALID"):
        assess(_market(), budget)


def test_zero_budget_and_unaffordable_original_quantity_are_explicitly_blocked():
    empty = assess(_market(), "0")
    assert empty["reason_codes"] == ["CARD_BUDGET_BELOW_MINIMUM_CONTRACT"]
    too_big = assess(_market(), "1", quantity=D(10))
    assert "CARD_ORDER_NOTIONAL_EXCEEDS_AVAILABLE_BUDGET" in too_big["reason_codes"]
    market = _market()
    with pytest.raises(ValueError, match="INSTRUMENT_OR_SIDE"):
        assess(
            replace(
                market, native_contract=replace(market.native_contract, contract_type="inverse")
            )
        )


@pytest.mark.parametrize("direction", [1, -1])
def test_original_paper_owner_retains_actual_quantity_budget_and_costs(tmp_path, direction):
    session = ZkpPaperEntryV1(
        root=tmp_path.resolve() / "paper-owner",
        repo=REPO,
        revision="f" * 40,
        initial_market=_market(direction=direction),
        duration=7200,
    )
    for step in range(7):
        market = _market(step, direction=direction)
        result = session.step_v1(market, clock=lambda: market.observed_unix + 0.01)
        if result["status"] == "FIRST_FILL_BOOKED":
            break
    assert result["status"] == "FIRST_FILL_BOOKED", result
    measurement = result["budget_assessment"]
    assert measurement["quantity_source"] == "EXPLICIT_ORIGINAL_SIZING_QUANTITY"
    assert measurement["quantity_contracts"] == result["fill"]["quantity"]
    assert D(measurement["available_budget_usdc"]) == 25
    assert measurement["side"] == result["fill"]["side"]
    assert D(measurement["book_notional_usd"]) == D(result["fill"]["notional"])
    assert result["costs"]["entry_notional"] == result["fill"]["notional"]
    assert result["orders_sent"] == result["permits_created"] == 0
    assert not measurement["productive_entry_admitted"]
