"""Evaluate current instrument cards independently before analytical entry confirmation."""

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from math import isfinite

from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.instrument_card_budget_assessment_v1 import assess_instrument_budget_v1
from src.ops.instrument_card_stream_v1 import validate_card_market_v1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


@dataclass(frozen=True)
class EntryCardV1:
    bound: BoundInstrumentV1
    market: object
    budget: dict


class CardEntryDeferredV1(ValueError):
    """No new entry evaluation for this observation; other cards remain independent."""


def _review(lane, card, now):
    market, budget = card.market, card.budget
    validate_card_market_v1(market, bound=card.bound, lane_id=lane, now=now)
    if (
        budget["status"] != "BOUND"
        or not budget.get("owner")
        or type(budget["observed_unix"]) not in (int, float)
        or not isfinite(budget["observed_unix"])
        or budget["lane_id"] != lane
        or budget["instrument_id"] != card.bound.instrument_id
        or budget["currency"] != "USDC"
        or not market.observed_unix <= budget["observed_unix"] <= now
        or budget["source_digest"] != canonical_digest_v1(budget["original_snapshot"])
    ):
        raise ValueError("CARD_ENTRY_BUDGET_BINDING_INVALID")
    available = Decimal(budget["available_for_new_entry"])
    amount = Decimal(budget["available_amount"])
    if not available.is_finite() or not amount.is_finite() or not 0 <= available <= amount:
        raise ValueError("CARD_ENTRY_FREE_AMOUNT_INVALID")
    sides = {}
    for side in ("BUY", "SELL"):
        # Capacity is an upper bound before costs. A smaller original sizing
        # may fit even when consuming the entire upper bound would not.
        capacity = assess_instrument_budget_v1(market=market, available_usdc=available, side=side)
        minimum = assess_instrument_budget_v1(
            market=market,
            available_usdc=available,
            side=side,
            quantity_contracts=market.native_contract.min_qty,
        )
        sides[side] = dict(
            eligible=minimum["measurement_admitted"],
            reasons=minimum["reason_codes"],
            minimum_contracts=minimum["quantity_contracts"],
            capacity_contracts=capacity["budget_capacity_contracts_before_costs"],
            capacity_admitted=capacity["measurement_admitted"],
            capacity_reasons=capacity["reason_codes"],
        )
    return dict(
        lane_id=lane,
        binding=card.bound.to_dict(),
        instrument_id=card.bound.instrument_id,
        venue_native_id=card.bound.venue_native_id,
        observed_unix=now,
        budget_digest=budget["source_digest"],
        available_usdc=str(available),
        mark_digest=market.source_hashes["mark"],
        book_digest=market.source_hashes["book"],
        sides=sides,
        reasons=[],
        authority="ANALYTICAL_CARD_REVIEW_ONLY",
    )


def review_entry_cards_v1(cards, *, now):
    """Return this decision-time review for each supplied slot, including missing inputs."""
    reviews = {}
    for lane, card in cards.items():
        try:
            if not isinstance(card, EntryCardV1) or not isinstance(card.bound, BoundInstrumentV1):
                raise ValueError("CARD_UNAVAILABLE")
            reviews[lane] = _review(lane, card, now)
        except (ValueError, KeyError, TypeError, ArithmeticError, AttributeError) as exc:
            reviews[lane] = dict(
                lane_id=lane, sides={}, reasons=[str(exc)], authority="ANALYTICAL_CARD_REVIEW_ONLY"
            )
    validated = [row for row in reviews.values() if row.get("binding")]
    by_canonical = Counter(row["instrument_id"] for row in validated)
    by_native = Counter(row["venue_native_id"] for row in validated)
    for row in validated:
        if by_canonical[row["instrument_id"]] != 1 or by_native[row["venue_native_id"]] != 1:
            row.update(sides={}, reasons=["CARD_DUPLICATE_INSTRUMENT"])
    return reviews
