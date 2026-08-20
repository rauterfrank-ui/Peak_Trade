"""Offline LF-05 flatten LIMIT price contract.

PATH B: necessary quote-selection, freshness, finite-bound, and tick-rounding
semantics are not canonically proven. This module validates structured inputs
and fail-closes. It never issues an operational price and never POSTs.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    FLATTEN_LIMIT_PRICE_GATE_STATUS,
)


class LiveCanaryFlattenLimitPriceError(RuntimeError):
    """Fail-closed flatten LIMIT price-contract violation."""


LF_05_IMPLEMENTATION_STATUS = "PARTIAL_FAIL_CLOSED_CONTRACT"
FLATTEN_PRICE_POLICY_IMPLEMENTED = False
FLATTEN_PRICE_POLICY_OPERATIONALLY_USABLE = False
SIDE_AWARE_QUOTE_SELECTION_STATUS = "UNPROVEN"
QUOTE_FRESHNESS_STATUS = "UNPROVEN"
FINITE_PRICE_BOUND_STATUS = "UNPROVEN"
TICK_NORMALIZATION_STATUS = "UNPROVEN"
LIVE_FLATTEN_PROVABILITY_STATUS = "UNPROVEN"
LIFECYCLE_FLATTEN_RUNTIME_REACHABLE = False
NETWORK_EFFECT_NONE = "none"
ORDER_EFFECT_NONE = "none"
ACCOUNT_MUTATION_EFFECT_NONE = "none"

_ALLOWED_SIDES = frozenset({"BUY", "SELL"})


@dataclass(frozen=True)
class FlattenPriceInputV1:
    """Caller-supplied observed values. No network fetch. No hidden defaults."""

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
    """Not issuable while flatten LIMIT price policy remains unproven."""

    flatten_side: str
    limit_price: str
    selected_quote_side: str
    tick_sz: str

    def __post_init__(self) -> None:
        raise LiveCanaryFlattenLimitPriceError(
            "FLATTEN_PRICE_PERMIT_FORBIDDEN:" + LF_05_IMPLEMENTATION_STATUS
        )


@dataclass(frozen=True)
class FlattenPriceDecisionV1:
    """Offline price-contract result. Never a transport or execute authorization."""

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
            "permit": None,
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
    return "SELL" if signed_pos > 0 else "BUY"


def evaluate_canary_flatten_limit_price_contract_v1(
    price_input: FlattenPriceInputV1,
) -> FlattenPriceDecisionV1:
    """Evaluate an offline flatten LIMIT price. Never issues a usable price."""
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

    policy_reasons: list[str] = []
    if not _blank(price_input.freshness_threshold_ms):
        policy_reasons.append("FRESHNESS_THRESHOLD_NOT_CANONICALLY_BOUND")
    else:
        policy_reasons.append("QUOTE_FRESHNESS_THRESHOLD_UNPROVEN")
    if not _blank(price_input.finite_bound) or not _blank(price_input.bound_kind):
        policy_reasons.append("FINITE_BOUND_NOT_CANONICALLY_BOUND")
    else:
        policy_reasons.append("FINITE_PRICE_BOUND_UNPROVEN")
    policy_reasons.append("SIDE_AWARE_QUOTE_SELECTION_UNPROVEN")
    policy_reasons.append("TICK_NORMALIZATION_UNPROVEN")
    return _rejected(reasons=tuple(policy_reasons), flatten_side=side)
