"""Standing LIMIT slippage policy for the §11.14 exact-single fill.

Worst admissible fill for a LIMIT order is the limit price. Venue
price-limit is a separate band gate, not this slippage bound. Historical
0.0008 and COVER_USDC SLP-TOB-FLOOR-TICK are not current fill-price
authority. Does not POST.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.constants_v1 import (
    COVER_USDC_SLIPPAGE_RESERVE_IS_NOT_THIS_FILL_WORST_PRICE,
    HISTORICAL_SLIPPAGE_0_0008_IS_NOT_CURRENT,
    PRICE_LIMIT_BAND_IS_NOT_SLIPPAGE,
    SLIPPAGE_POLICY_ID,
    SLIPPAGE_POLICY_UNIT,
)


class StandingSlippagePolicyError(RuntimeError):
    """Fail-closed standing slippage-policy violation."""


def _dec(raw: Any, *, field: str) -> Decimal:
    text = str(raw if raw is not None else "").strip()
    if not text or text == "UNKNOWN":
        raise StandingSlippagePolicyError(f"SLIPPAGE_INPUT_UNKNOWN:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise StandingSlippagePolicyError(f"SLIPPAGE_INPUT_UNPARSEABLE:{field}") from exc
    if not value.is_finite() or value <= 0:
        raise StandingSlippagePolicyError(f"SLIPPAGE_INPUT_NON_POSITIVE:{field}")
    return value


@dataclass(frozen=True)
class StandingSlippagePolicyV1:
    policy_bound: bool
    policy_id: str
    side: str
    reference_price: str
    limit_price: str
    tick_sz: str
    worst_fill_price: str
    slippage_abs: str
    slippage_frac: str
    unit: str
    price_limit_used_as_slippage: bool
    historical_0008_used: bool
    cover_usdc_reserve_used: bool
    deny_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "POLICY_BOUND": self.policy_bound,
            "POLICY_ID": self.policy_id,
            "SIDE": self.side,
            "REFERENCE_PRICE": self.reference_price,
            "LIMIT_PRICE": self.limit_price,
            "TICK_SZ": self.tick_sz,
            "WORST_FILL_PRICE": self.worst_fill_price,
            "SLIPPAGE_ABS": self.slippage_abs,
            "SLIPPAGE_FRAC": self.slippage_frac,
            "UNIT": self.unit,
            "PRICE_LIMIT_USED_AS_SLIPPAGE": self.price_limit_used_as_slippage,
            "HISTORICAL_0008_USED": self.historical_0008_used,
            "COVER_USDC_RESERVE_USED": self.cover_usdc_reserve_used,
            "DENY_REASON": self.deny_reason,
        }


def bind_standing_limit_slippage_policy_v1(
    *,
    side: str,
    reference_price: str,
    limit_price: str,
    tick_sz: str,
) -> StandingSlippagePolicyV1:
    side_u = str(side or "").strip().upper()
    if side_u not in {"BUY", "SELL"}:
        raise StandingSlippagePolicyError(f"UNSUPPORTED_SIDE:{side}")
    ref = _dec(reference_price, field="reference_price")
    limit = _dec(limit_price, field="limit_price")
    tick = _dec(tick_sz, field="tick_sz")
    remainder = (limit / tick).to_integral_value()
    if remainder * tick != limit:
        raise StandingSlippagePolicyError("LIMIT_PRICE_NOT_ON_TICK")
    if side_u == "BUY":
        if limit > ref:
            raise StandingSlippagePolicyError("BUY_LIMIT_ABOVE_REFERENCE_NOT_BOUND")
        worst = limit
        slippage_abs = ref - limit
    else:
        if limit < ref:
            raise StandingSlippagePolicyError("SELL_LIMIT_BELOW_REFERENCE_NOT_BOUND")
        worst = limit
        slippage_abs = limit - ref
    frac = slippage_abs / ref
    return StandingSlippagePolicyV1(
        policy_bound=True,
        policy_id=SLIPPAGE_POLICY_ID,
        side=side_u,
        reference_price=format(ref, "f"),
        limit_price=format(limit, "f"),
        tick_sz=format(tick, "f"),
        worst_fill_price=format(worst, "f"),
        slippage_abs=format(slippage_abs, "f"),
        slippage_frac=format(frac, "f"),
        unit=SLIPPAGE_POLICY_UNIT,
        price_limit_used_as_slippage=not PRICE_LIMIT_BAND_IS_NOT_SLIPPAGE,
        historical_0008_used=not HISTORICAL_SLIPPAGE_0_0008_IS_NOT_CURRENT,
        cover_usdc_reserve_used=not COVER_USDC_SLIPPAGE_RESERVE_IS_NOT_THIS_FILL_WORST_PRICE,
        deny_reason="",
    )
