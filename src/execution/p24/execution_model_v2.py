"""P24 execution model v2 — deterministic partial fills."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional

from .config import ExecutionModelV2Config


Side = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT", "STOP_MARKET"]


@dataclass(frozen=True)
class MarketSnapshot:
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Order:
    order_id: str
    side: Side
    type: OrderType
    qty: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    remaining_qty: float = 0.0
    triggered: bool = False
    trigger_bar_ts: Optional[str] = None

    def __post_init__(self) -> None:
        self.remaining_qty = float(self.qty)


@dataclass(frozen=True)
class Fill:
    order_id: str
    bar_ts: str
    qty: float
    price: float
    fee: float


class ExecutionModelV2:
    def __init__(self, cfg: ExecutionModelV2Config) -> None:
        self.cfg = cfg
        self.cfg.partial_fills_v2.validate()

    def process_bar(self, bar: MarketSnapshot, orders: List[Order]) -> List[Fill]:
        fills: List[Fill] = []
        for o in orders:
            if o.remaining_qty <= 0:
                continue

            if o.type == "STOP_MARKET":
                self._maybe_trigger_stop(bar, o)

                if not o.triggered:
                    continue
                if (not self.cfg.partial_fills_v2.allow_partial_on_trigger_bar) and (
                    o.trigger_bar_ts == bar.ts
                ):
                    continue
                fill = self._fill_market(bar, o)
            elif o.type == "MARKET":
                fill = self._fill_market(bar, o)
            elif o.type == "LIMIT":
                fill = self._fill_limit(bar, o)
            else:
                raise ValueError(f"unsupported order type: {o.type}")

            if fill is not None:
                fills.append(fill)

        return fills

    def _maybe_trigger_stop(self, bar: MarketSnapshot, o: Order) -> None:
        if o.triggered:
            return
        if o.stop_price is None:
            raise ValueError("STOP_MARKET requires stop_price")
        tm = self.cfg.partial_fills_v2.touch_mode
        if o.side == "BUY":
            cond = (bar.high >= o.stop_price) if tm == "touch" else (bar.high > o.stop_price)
        else:
            cond = (bar.low <= o.stop_price) if tm == "touch" else (bar.low < o.stop_price)
        if cond:
            o.triggered = True
            o.trigger_bar_ts = bar.ts

    def _limit_eligible(self, bar: MarketSnapshot, o: Order) -> bool:
        if o.limit_price is None:
            raise ValueError("LIMIT requires limit_price")
        tm = self.cfg.partial_fills_v2.touch_mode
        if o.side == "BUY":
            return (bar.low <= o.limit_price) if tm == "touch" else (bar.low < o.limit_price)
        return (bar.high >= o.limit_price) if tm == "touch" else (bar.high > o.limit_price)

    def _compute_fill_qty(self, bar: MarketSnapshot, rem: float) -> float:
        pf = self.cfg.partial_fills_v2
        cap_ratio = rem * pf.max_fill_ratio_per_bar
        cap_vol = bar.volume * pf.volume_cap_ratio
        fill0 = min(rem, cap_ratio, cap_vol)

        if fill0 < pf.min_fill_qty:
            return 0.0

        if pf.rounding == "none":
            return float(fill0)

        step = pf.qty_step
        assert step is not None and step > 0
        q = fill0 / step
        if pf.rounding == "floor":
            q_int = int(q)
        elif pf.rounding == "ceil":
            q_int = int(q) if abs(q - int(q)) < 1e-12 else int(q) + 1
        else:
            raise ValueError(f"unknown rounding: {pf.rounding}")
        fill = q_int * step
        if fill > rem:
            fill = rem
        return float(fill)

    def _candidate_price(self, bar: MarketSnapshot, side: Side) -> float:
        rule = self.cfg.partial_fills_v2.price_rule
        if rule == "worst":
            return bar.high if side == "BUY" else bar.low
        if rule == "mid":
            return (bar.high + bar.low) / 2.0
        if rule == "close":
            return bar.close
        raise ValueError(f"unknown price_rule: {rule}")

    def _apply_slippage(self, price: float, side: Side) -> float:
        bps = self.cfg.slippage_bps
        if bps <= 0:
            return price
        mult = 1.0 + (bps / 10_000.0)
        return price * mult if side == "BUY" else price / mult

    def _fee(self, notional: float) -> float:
        return notional * self.cfg.fee_rate

    def _fill_market(self, bar: MarketSnapshot, o: Order) -> Optional[Fill]:
        fq = self._compute_fill_qty(bar, o.remaining_qty)
        if fq <= 0:
            return None

        cand = self._candidate_price(bar, o.side)
        price = self._apply_slippage(cand, o.side)

        notional = fq * price
        fee = self._fee(notional)

        o.remaining_qty -= fq
        return Fill(order_id=o.order_id, bar_ts=bar.ts, qty=fq, price=price, fee=fee)

    def _fill_limit(self, bar: MarketSnapshot, o: Order) -> Optional[Fill]:
        if not self._limit_eligible(bar, o):
            return None

        fq = self._compute_fill_qty(bar, o.remaining_qty)
        if fq <= 0:
            return None

        assert o.limit_price is not None
        cand = self._candidate_price(bar, o.side)

        if o.side == "BUY":
            price = min(cand, o.limit_price)
            price = self._apply_slippage(price, o.side)
            price = min(price, o.limit_price)
        else:
            price = max(cand, o.limit_price)
            price = self._apply_slippage(price, o.side)
            price = max(price, o.limit_price)

        notional = fq * price
        fee = self._fee(notional)

        o.remaining_qty -= fq
        return Fill(order_id=o.order_id, bar_ts=bar.ts, qty=fq, price=price, fee=fee)
