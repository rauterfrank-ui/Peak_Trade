"""Offline flatten LIMIT price policy.

Quote-locked, side-aware, fail-closed. Issues a LIMIT px from caller-supplied
current bid/ask plus the Owner-ratified freshness threshold. Never POSTs,
never invents MARKET, never adds an extra deviation guard, and does not
prove live flatten.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_UP, InvalidOperation
from math import isfinite
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    FLATTEN_LIMIT_PRICE_GATE_STATUS,
)
from src.ops.section_11_13_5_p12_execution_prerequisite_11_position_side_posside_v1.contract_v1 import (
    flatten_order_side_from_signed_pos_v1,
)


class LiveCanaryFlattenLimitPriceError(RuntimeError):
    """Fail-closed flatten LIMIT price-contract violation."""


LF_05_IMPLEMENTATION_STATUS = "QUOTE_LOCKED_LIMIT_POLICY_V1"
FLATTEN_PRICE_POLICY_IMPLEMENTED = True
FLATTEN_PRICE_POLICY_FULLY_BOUND = True
FLATTEN_PRICE_POLICY_OPERATIONALLY_USABLE = True
SIDE_AWARE_QUOTE_SELECTION_STATUS = "IMPLEMENTED_BID_FOR_SELL_ASK_FOR_BUY"
FRESHNESS_THRESHOLD_MS = 5000
QUOTE_FRESHNESS_STATUS = "OWNER_RATIFIED_FRESHNESS_THRESHOLD_MS"
FINITE_PRICE_BOUND_STATUS = "QUOTE_LOCKED_NO_EXTRA_DEVIATION"
TICK_NORMALIZATION_STATUS = "IMPLEMENTED_SELL_ROUND_DOWN_BUY_ROUND_UP"
FLATTEN_LIMIT_PRICE_GATE_BOUND = "QUOTE_LOCKED_LIMIT_ISSUED"
LIVE_FLATTEN_PROVABILITY_STATUS = "UNPROVEN"
LIFECYCLE_FLATTEN_RUNTIME_REACHABLE = False
NETWORK_EFFECT_NONE = "none"
ORDER_EFFECT_NONE = "none"
ACCOUNT_MUTATION_EFFECT_NONE = "none"
OWNER_BINDING_STILL_REQUIRED = "LIVE_WIRE_AND_PRODUCTIVE_FLATTEN_SEPARATE_OWNER_GO"

_ALLOWED_SIDES = frozenset({"BUY", "SELL"})


@dataclass(frozen=True)
class FlattenPriceInputV1:
    """Caller-supplied observed values. No network fetch.

    Freshness uses the Owner-ratified canonical threshold when omitted;
    a supplied value must equal that canonical threshold.
    """

    flatten_side: str | None = None
    observed_signed_pos: str | None = None
    bid: str | None = None
    ask: str | None = None
    quote_timestamp_ms: str | None = None
    evaluation_timestamp_ms: str | None = None
    tick_sz: str | None = None
    freshness_threshold_ms: str | None = None
    finite_bound: str | None = None
    bound_kind: str | None = None


@dataclass(frozen=True)
class FlattenPricePermitV1:
    """Offline LIMIT price permit. Not live-submit authorization."""

    flatten_side: str
    limit_price: str
    selected_quote_side: str
    tick_sz: str

    def __post_init__(self) -> None:
        side = str(self.flatten_side or "").strip().upper()
        quote_side = str(self.selected_quote_side or "").strip().upper()
        if side not in _ALLOWED_SIDES:
            raise LiveCanaryFlattenLimitPriceError("FLATTEN_PRICE_PERMIT_SIDE_INVALID")
        if side == "SELL" and quote_side != "BID":
            raise LiveCanaryFlattenLimitPriceError("FLATTEN_PRICE_PERMIT_QUOTE_SIDE_INVALID")
        if side == "BUY" and quote_side != "ASK":
            raise LiveCanaryFlattenLimitPriceError("FLATTEN_PRICE_PERMIT_QUOTE_SIDE_INVALID")
        try:
            px = Decimal(str(self.limit_price))
            tick = Decimal(str(self.tick_sz))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise LiveCanaryFlattenLimitPriceError("FLATTEN_PRICE_PERMIT_NUMERIC_INVALID") from exc
        if px <= 0 or tick <= 0:
            raise LiveCanaryFlattenLimitPriceError("FLATTEN_PRICE_PERMIT_NUMERIC_INVALID")
        if (px / tick).to_integral_value() * tick != px:
            raise LiveCanaryFlattenLimitPriceError("FLATTEN_PRICE_PERMIT_NOT_ON_TICK")

    def to_dict(self) -> dict[str, Any]:
        return {
            "flatten_side": self.flatten_side,
            "limit_price": self.limit_price,
            "selected_quote_side": self.selected_quote_side,
            "tick_sz": self.tick_sz,
        }


@dataclass(frozen=True)
class FlattenPriceDecisionV1:
    """Offline price-contract result. Never a live execute authorization."""

    permit_issued: bool
    permit: FlattenPricePermitV1 | None
    flatten_side: str | None
    selected_quote_side: str | None
    limit_price: str | None
    reject_reasons: tuple[str, ...]
    operationally_usable: bool
    implementation_status: str
    quote_selection_status: str
    freshness_status: str
    finite_bound_status: str
    tick_normalization_status: str
    price_gate_status: str
    submit_reachable: bool
    network_effect: str
    order_effect: str
    account_mutation_effect: str
    live_flatten_provability: str
    lifecycle_flatten_runtime_reachable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "permit_issued": self.permit_issued,
            "permit": None if self.permit is None else self.permit.to_dict(),
            "flatten_side": self.flatten_side,
            "selected_quote_side": self.selected_quote_side,
            "limit_price": self.limit_price,
            "reject_reasons": list(self.reject_reasons),
            "operationally_usable": self.operationally_usable,
            "implementation_status": self.implementation_status,
            "quote_selection_status": self.quote_selection_status,
            "freshness_status": self.freshness_status,
            "finite_bound_status": self.finite_bound_status,
            "tick_normalization_status": self.tick_normalization_status,
            "price_gate_status": self.price_gate_status,
            "submit_reachable": self.submit_reachable,
            "network_effect": self.network_effect,
            "order_effect": self.order_effect,
            "account_mutation_effect": self.account_mutation_effect,
            "live_flatten_provability": self.live_flatten_provability,
            "lifecycle_flatten_runtime_reachable": self.lifecycle_flatten_runtime_reachable,
        }


def _rejected(
    *,
    reasons: tuple[str, ...],
    flatten_side: str | None = None,
) -> FlattenPriceDecisionV1:
    return FlattenPriceDecisionV1(
        permit_issued=False,
        permit=None,
        flatten_side=flatten_side,
        selected_quote_side=None,
        limit_price=None,
        reject_reasons=reasons,
        operationally_usable=False,
        implementation_status=LF_05_IMPLEMENTATION_STATUS,
        quote_selection_status=SIDE_AWARE_QUOTE_SELECTION_STATUS,
        freshness_status=QUOTE_FRESHNESS_STATUS,
        finite_bound_status=FINITE_PRICE_BOUND_STATUS,
        tick_normalization_status=TICK_NORMALIZATION_STATUS,
        price_gate_status=FLATTEN_LIMIT_PRICE_GATE_STATUS,
        submit_reachable=False,
        network_effect=NETWORK_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        account_mutation_effect=ACCOUNT_MUTATION_EFFECT_NONE,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        lifecycle_flatten_runtime_reachable=LIFECYCLE_FLATTEN_RUNTIME_REACHABLE,
    )


def _blank(raw: str | None) -> bool:
    return raw is None or str(raw).strip() == ""


def _parse_decimal(raw: str) -> Decimal | str:
    text = str(raw).strip()
    lowered = text.lower()
    if lowered in {"nan", "+nan", "-nan", "inf", "+inf", "-inf", "infinity", "-infinity"}:
        return "NON_FINITE"
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError):
        return "MALFORMED"
    try:
        if not isfinite(float(value)):
            return "NON_FINITE"
    except (OverflowError, ValueError):
        return "NON_FINITE"
    return value


def _parse_timestamp_ms(raw: str) -> int | str:
    text = str(raw).strip()
    try:
        value = int(text)
    except (TypeError, ValueError):
        return "MALFORMED"
    if value <= 0:
        return "MALFORMED"
    return value


def _expected_flatten_side(signed_pos: Decimal) -> str:
    return flatten_order_side_from_signed_pos_v1(signed_pos)


def _quantize_to_tick(px: Decimal, tick: Decimal, *, flatten_side: str) -> Decimal | None:
    steps = px / tick
    rounding = ROUND_DOWN if flatten_side == "SELL" else ROUND_UP
    quantized_steps = steps.to_integral_value(rounding=rounding)
    if quantized_steps <= 0:
        return None
    return quantized_steps * tick


def evaluate_canary_flatten_limit_price_contract_v1(
    price_input: FlattenPriceInputV1,
) -> FlattenPriceDecisionV1:
    """Evaluate a quote-locked flatten LIMIT price. Never authorizes live submit."""
    side_raw = None if price_input.flatten_side is None else str(price_input.flatten_side).strip()
    side = side_raw.upper() if side_raw else None
    if side not in _ALLOWED_SIDES:
        return _rejected(reasons=("UNKNOWN_SIDE",), flatten_side=side)

    if _blank(price_input.observed_signed_pos):
        return _rejected(reasons=("NO_OBSERVED_POSITION",), flatten_side=side)
    parsed_pos = _parse_decimal(str(price_input.observed_signed_pos))
    if parsed_pos in {"MALFORMED", "NON_FINITE"}:
        return _rejected(reasons=("INCONSISTENT_POSITION",), flatten_side=side)
    assert isinstance(parsed_pos, Decimal)
    if parsed_pos == 0:
        return _rejected(reasons=("ZERO_POSITION",), flatten_side=side)
    expected_side = _expected_flatten_side(parsed_pos)
    if side != expected_side:
        return _rejected(reasons=("INCONSISTENT_POSITION",), flatten_side=side)

    bid_blank = _blank(price_input.bid)
    ask_blank = _blank(price_input.ask)
    if bid_blank and ask_blank:
        return _rejected(reasons=("QUOTE_MISSING",), flatten_side=side)
    if bid_blank:
        return _rejected(reasons=("BID_MISSING",), flatten_side=side)
    if ask_blank:
        return _rejected(reasons=("ASK_MISSING",), flatten_side=side)

    bid_parsed = _parse_decimal(str(price_input.bid))
    ask_parsed = _parse_decimal(str(price_input.ask))
    quote_codes = {bid_parsed, ask_parsed}
    if "MALFORMED" in quote_codes:
        return _rejected(reasons=("MALFORMED_QUOTE",), flatten_side=side)
    if "NON_FINITE" in quote_codes:
        return _rejected(reasons=("NON_FINITE_QUOTE",), flatten_side=side)
    assert isinstance(bid_parsed, Decimal)
    assert isinstance(ask_parsed, Decimal)
    if bid_parsed <= 0 or ask_parsed <= 0:
        return _rejected(reasons=("ZERO_OR_NEGATIVE_QUOTE",), flatten_side=side)
    if ask_parsed < bid_parsed:
        return _rejected(reasons=("MALFORMED_QUOTE",), flatten_side=side)

    if _blank(price_input.tick_sz):
        return _rejected(reasons=("TICK_SIZE_MISSING",), flatten_side=side)
    tick_parsed = _parse_decimal(str(price_input.tick_sz))
    if tick_parsed == "MALFORMED":
        return _rejected(reasons=("TICK_SIZE_INVALID",), flatten_side=side)
    if tick_parsed == "NON_FINITE":
        return _rejected(reasons=("TICK_SIZE_INVALID",), flatten_side=side)
    assert isinstance(tick_parsed, Decimal)
    if tick_parsed <= 0:
        return _rejected(reasons=("TICK_SIZE_INVALID",), flatten_side=side)

    quote_ts_blank = _blank(price_input.quote_timestamp_ms)
    eval_ts_blank = _blank(price_input.evaluation_timestamp_ms)
    if quote_ts_blank or eval_ts_blank:
        return _rejected(reasons=("FRESHNESS_UNKNOWN",), flatten_side=side)
    quote_ts = _parse_timestamp_ms(str(price_input.quote_timestamp_ms))
    eval_ts = _parse_timestamp_ms(str(price_input.evaluation_timestamp_ms))
    if quote_ts == "MALFORMED" or eval_ts == "MALFORMED":
        return _rejected(reasons=("MALFORMED_TIMESTAMP",), flatten_side=side)
    assert isinstance(quote_ts, int)
    assert isinstance(eval_ts, int)
    if quote_ts > eval_ts:
        return _rejected(reasons=("FUTURE_TIMESTAMP",), flatten_side=side)

    if not _blank(price_input.finite_bound) or not _blank(price_input.bound_kind):
        return _rejected(reasons=("FINITE_BOUND_NOT_OWNER_RATIFIED",), flatten_side=side)

    if _blank(price_input.freshness_threshold_ms):
        threshold = FRESHNESS_THRESHOLD_MS
    else:
        parsed_threshold = _parse_timestamp_ms(str(price_input.freshness_threshold_ms))
        if parsed_threshold == "MALFORMED":
            return _rejected(reasons=("FRESHNESS_THRESHOLD_INVALID",), flatten_side=side)
        assert isinstance(parsed_threshold, int)
        if parsed_threshold != FRESHNESS_THRESHOLD_MS:
            return _rejected(reasons=("FRESHNESS_THRESHOLD_NOT_CANONICAL",), flatten_side=side)
        threshold = parsed_threshold
    age_ms = eval_ts - quote_ts
    if age_ms > threshold:
        return _rejected(reasons=("STALE_QUOTE",), flatten_side=side)

    selected_quote = bid_parsed if side == "SELL" else ask_parsed
    selected_quote_side = "BID" if side == "SELL" else "ASK"
    quantized = _quantize_to_tick(selected_quote, tick_parsed, flatten_side=side)
    if quantized is None:
        return _rejected(reasons=("LIMIT_PRICE_NON_POSITIVE_AFTER_TICK",), flatten_side=side)
    if side == "SELL" and quantized > bid_parsed:
        return _rejected(reasons=("SELL_LIMIT_ABOVE_BID_AFTER_TICK",), flatten_side=side)
    if side == "BUY" and quantized < ask_parsed:
        return _rejected(reasons=("BUY_LIMIT_BELOW_ASK_AFTER_TICK",), flatten_side=side)

    limit_price = format(quantized, "f")
    permit = FlattenPricePermitV1(
        flatten_side=side,
        limit_price=limit_price,
        selected_quote_side=selected_quote_side,
        tick_sz=format(tick_parsed, "f"),
    )
    return FlattenPriceDecisionV1(
        permit_issued=True,
        permit=permit,
        flatten_side=side,
        selected_quote_side=selected_quote_side,
        limit_price=limit_price,
        reject_reasons=(),
        operationally_usable=True,
        implementation_status=LF_05_IMPLEMENTATION_STATUS,
        quote_selection_status=SIDE_AWARE_QUOTE_SELECTION_STATUS,
        freshness_status=QUOTE_FRESHNESS_STATUS,
        finite_bound_status=FINITE_PRICE_BOUND_STATUS,
        tick_normalization_status=TICK_NORMALIZATION_STATUS,
        price_gate_status=FLATTEN_LIMIT_PRICE_GATE_BOUND,
        submit_reachable=False,
        network_effect=NETWORK_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        account_mutation_effect=ACCOUNT_MUTATION_EFFECT_NONE,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        lifecycle_flatten_runtime_reachable=LIFECYCLE_FLATTEN_RUNTIME_REACHABLE,
    )
