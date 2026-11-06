from __future__ import annotations

from decimal import Decimal
from typing import Dict

from .models import Position, QuantizationPolicy
from .quantization import q_money, d


def unrealized_pnl_for_position(
    pos: Position, *, mark_price: Decimal, policy: QuantizationPolicy
) -> Decimal:
    """
    Deterministic unrealized PnL.

    Works for both long and short positions:
      (mark - avg_cost) * qty
    """
    if pos.quantity == 0:
        return Decimal("0")
    return q_money((mark_price - pos.avg_cost) * pos.quantity, policy=policy)


def total_unrealized_pnl(
    positions: Dict[str, Position],
    *,
    mark_prices: Dict[str, Decimal],
    policy: QuantizationPolicy,
) -> Decimal:
    total = Decimal("0")
    for sym, pos in positions.items():
        if sym not in mark_prices:
            continue
        total += unrealized_pnl_for_position(pos, mark_price=mark_prices[sym], policy=policy)
    return q_money(total, policy=policy)
