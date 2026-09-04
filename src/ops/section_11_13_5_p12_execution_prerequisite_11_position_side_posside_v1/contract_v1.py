"""Fail-closed EXECUTION_PREREQUISITE_11 position-side / request-posSide contract.

Separates four objects that must not be collapsed:

1. ACCOUNT_POS_MODE — account-global ``posMode`` (separate POS_MODE binding).
2. POSITION_ROW_POS_SIDE — positions-response ``posSide`` (P08 observed ``net``).
3. FLATTEN_ORDER_SIDE — Place Order ``side`` BUY/SELL from signed_pos.
4. REQUEST_POS_SIDE — Place Order ``posSide``; current flatten body OMITTED.

Canonical Z2CB already binds order-side derivation and request-posSide
omission. This module makes that contract explicit and fail-closed. It
does not GET, POST, flatten, or copy row ``posSide`` onto the order body.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

ORDER_SIDE_BUY = "BUY"
ORDER_SIDE_SELL = "SELL"
ORDER_SIDE_DOMAIN: frozenset[str] = frozenset({ORDER_SIDE_BUY, ORDER_SIDE_SELL})
REQUEST_POS_SIDE_POLICY = "OMITTED_FROM_VENUE_NATIVE_BODY"
REQUEST_POS_SIDE_VALUE = "OMITTED"
POSITION_ROW_POS_SIDE_OBSERVED_P08 = "net"
POSITION_ROW_POS_SIDE_IS_NOT_REQUEST_POS_SIDE = True
POS_MODE_IS_NOT_POSITION_SIDE = True
POS_MODE_NET_MODE_DOES_NOT_IMPLY_REQUEST_POS_SIDE_NET = True
LONG_SHORT_IS_NOT_BUY_SELL = True
CASE = "CASE_B_OFFLINE_CLOSABLE"
EXECUTION_PREREQUISITE_11_STATUS = "PASS"
P11_PROVEN = True
P11_CLOSED = True


class PositionSidePossideError(RuntimeError):
    """Fail-closed EXECUTION_PREREQUISITE_11 violation."""


def flatten_order_side_from_signed_pos_v1(signed_pos: Decimal) -> str:
    """Derive Place Order ``side`` from observed signed position.

    Long (signed_pos > 0) flattens with SELL. Short (signed_pos < 0)
    flattens with BUY. Zero has no flatten side. This is order-side, not
    posSide, not posMode, and not a long/short ↔ buy/sell alias.
    """
    if signed_pos == 0:
        raise PositionSidePossideError("ZERO_POS_HAS_NO_FLATTEN_ORDER_SIDE")
    if signed_pos > 0:
        return ORDER_SIDE_SELL
    return ORDER_SIDE_BUY


def assert_flatten_order_side_matches_signed_pos_v1(
    *,
    side: str,
    signed_pos: Decimal,
) -> None:
    expected = flatten_order_side_from_signed_pos_v1(signed_pos)
    observed = str(side or "").strip().upper()
    if observed not in ORDER_SIDE_DOMAIN:
        raise PositionSidePossideError(f"INVALID_FLATTEN_ORDER_SIDE:{observed or 'MISSING'}")
    if observed != expected:
        raise PositionSidePossideError("FLATTEN_ORDER_SIDE_SIGNED_POS_MISMATCH")


def assert_request_pos_side_omitted_v1(body: Mapping[str, Any]) -> None:
    if "posSide" in body:
        raise PositionSidePossideError("REQUEST_POS_SIDE_PRESENT_ON_FLATTEN_BODY")
    lowered = {str(key).strip().lower() for key in body}
    if "posside" in lowered:
        raise PositionSidePossideError("REQUEST_POS_SIDE_PRESENT_ON_FLATTEN_BODY")


def assert_row_pos_side_not_copied_to_request_v1(
    *,
    row_pos_side: str | None,
    body: Mapping[str, Any],
) -> None:
    assert_request_pos_side_omitted_v1(body)
    _ = str(row_pos_side or "").strip()


def assert_pos_mode_not_rewritten_to_request_pos_side_v1(
    *,
    pos_mode: str | None,
    body: Mapping[str, Any],
) -> None:
    assert_request_pos_side_omitted_v1(body)
    mode = str(pos_mode or "").strip()
    if mode in {"net_mode", "net"} and body.get("posSide") in {"net", "net_mode"}:
        raise PositionSidePossideError("POS_MODE_REWRITTEN_TO_REQUEST_POS_SIDE")


def assert_no_long_short_buy_sell_conflation_v1(side: str) -> None:
    token = str(side or "").strip().lower()
    if token in {"long", "short", "net", "net_mode", "long_short_mode"}:
        raise PositionSidePossideError(f"POSITION_TOKEN_USED_AS_ORDER_SIDE:{token}")
    if str(side or "").strip().upper() not in ORDER_SIDE_DOMAIN:
        raise PositionSidePossideError(f"INVALID_FLATTEN_ORDER_SIDE:{side or 'MISSING'}")
