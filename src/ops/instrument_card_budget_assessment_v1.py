"""Budget-relative measurements for the existing linear XPERP card sources.

This is a measurement of notional capacity, before fees and risk sizing. It
reuses the original quantity-bound liquidity owner. It cannot issue an entry
decision, size a risk position, reserve capital, or authorize execution.
"""

from decimal import Decimal, InvalidOperation, ROUND_FLOOR


def _amount(value, *, positive=False):
    try:
        if isinstance(value, bool):
            raise ValueError("CARD_BUDGET_AMOUNT_INVALID")
        value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("CARD_BUDGET_AMOUNT_INVALID") from exc
    if not value.is_finite() or value < 0 or (positive and value == 0):
        raise ValueError("CARD_BUDGET_AMOUNT_INVALID")
    return value


def assess_instrument_budget_v1(*, market, available_usdc, side, quantity_contracts=None):
    """Measure a current budget or an original sizing owner's explicit quantity.

    Budget capacity uses the existing Paper path's one-to-one notional limit;
    available collateral must not be interpreted as leveraged buying power.
    Every amount is converted through the supplied snapshot's USDC/USD index.
    Policy thresholds come exclusively from that snapshot's existing profile.
    """
    contract = market.native_contract
    if (
        side not in {"BUY", "SELL"}
        or contract.symbol != market.slot.native_id
        or contract.quote_currency != "USD"
        or contract.contract_type != "linear"
    ):
        raise ValueError("CARD_BUDGET_INSTRUMENT_OR_SIDE_INVALID")
    available = _amount(available_usdc)
    fx = _amount(market.usd_per_usdc, positive=True)
    mark = _amount(market.mark, positive=True)
    multiplier = _amount(contract.contract_size, positive=True)
    lot = _amount(market.lot_size, positive=True)
    adv = _amount(market.adv_usd, positive=True)
    limit = _amount(market.policy.adv_participation_limit, positive=True)
    if limit > 1:
        raise ValueError("CARD_BUDGET_ADV_PROFILE_INVALID")
    budget_usd = available * fx
    capacity = (
        min(budget_usd / (mark * multiplier), market.maximum_contracts) / lot
    ).to_integral_value(rounding=ROUND_FLOOR) * lot
    quantity = capacity if quantity_contracts is None else _amount(quantity_contracts)
    reasons = []
    liquidity = None
    if quantity < contract.min_qty:
        reasons.append("CARD_BUDGET_BELOW_MINIMUM_CONTRACT")
    else:
        # Original owner validates venue maximum, native lot grid, both book
        # sides, VWAP, spread, adverse slippage, and ADV participation.
        liquidity = market.assess_quantity_v1(side=side, quantity=quantity)
        reasons.extend(liquidity["reason_codes"])
    mark_notional = quantity * multiplier * mark
    price = None if liquidity is None else liquidity["open_price_usd"]
    book_notional = None if price is None else quantity * multiplier * Decimal(price)
    if max(mark_notional, book_notional or mark_notional) > budget_usd:
        reasons.append("CARD_ORDER_NOTIONAL_EXCEEDS_AVAILABLE_BUDGET")
    adverse_slippage = None
    if price is not None:
        direction = 1 if side == "BUY" else -1
        adverse_slippage = (
            quantity * multiplier * max(Decimal(0), direction * (Decimal(price) - mark))
        )
    return {
        "schema": "instrument_card_budget_assessment.v1",
        "instrument_id": market.slot.instrument_id,
        "venue_native_id": market.slot.native_id,
        "lane_id": market.slot.lane_id,
        "side": side,
        "observed_unix": market.observed_unix,
        "available_budget_usdc": str(available),
        "available_budget_usd": str(budget_usd),
        "usd_per_usdc": str(fx),
        "adv_usd": str(adv),
        "adv_days": market.policy.adv_days,
        "budget_to_adv_fraction": str(budget_usd / adv),
        "adv_participation_limit": str(limit),
        "adv_order_value_cap_usd": str(adv * limit),
        "budget_capacity_contracts_before_costs": str(capacity),
        "quantity_contracts": str(quantity),
        "quantity_source": (
            "BUDGET_NOTIONAL_CAPACITY_BEFORE_FEES_AND_RISK"
            if quantity_contracts is None
            else "EXPLICIT_ORIGINAL_SIZING_QUANTITY"
        ),
        "mark_notional_usd": str(mark_notional),
        "book_notional_usd": None if book_notional is None else str(book_notional),
        "adverse_slippage_usdc": (None if adverse_slippage is None else str(adverse_slippage / fx)),
        "liquidity": liquidity,
        "measurement_admitted": not reasons,
        "reason_codes": reasons,
        "fees_and_funding_included": False,
        "final_quantity_owner": "capital_risk_sizing_v1",
        "source_hashes": dict(market.source_hashes),
        "runtime_authorization_effect": "NONE",
        "productive_entry_admitted": False,
    }
