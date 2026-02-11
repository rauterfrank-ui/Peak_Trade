from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .models import Fill, Order
from .slippage import SlippageModel


class PaperAccount:
    def __init__(self, cash: float) -> None:
        self.cash = float(cash)
        self.positions: Dict[str, float] = {}
        self.realized_pnl = 0.0


@dataclass(frozen=True)
class FeeModel:
    # proportional fee on notional (e.g. 0.001 = 10 bps)
    rate: float = 0.0

    def fee(self, notional: float) -> float:
        return abs(notional) * float(self.rate)


class PaperTradingSimulator:
    def __init__(
        self,
        fee_model: FeeModel | None = None,
        slippage: SlippageModel | None = None,
    ) -> None:
        self.fee_model = fee_model or FeeModel(0.0)
        self.slippage = slippage or SlippageModel(0.0)

    def execute(self, acct: PaperAccount, order: Order, mid_price: float) -> Fill:
        price = self.slippage.apply(order.side, float(mid_price))
        notional = price * float(order.qty)
        fee = self.fee_model.fee(notional)

        if order.side == "BUY":
            cost = notional + fee
            if acct.cash < cost:
                raise RuntimeError("INSUFFICIENT_CASH")
            acct.cash -= cost
            acct.positions[order.symbol] = acct.positions.get(order.symbol, 0.0) + float(order.qty)
        else:
            pos = acct.positions.get(order.symbol, 0.0)
            if pos < float(order.qty):
                raise RuntimeError("INSUFFICIENT_POSITION")
            proceeds = notional - fee
            acct.cash += proceeds
            acct.positions[order.symbol] = pos - float(order.qty)

        return Fill(
            symbol=order.symbol,
            side=order.side,
            qty=float(order.qty),
            price=price,
            fee=fee,
        )

    def reconcile(self, acct: PaperAccount) -> Tuple[float, Dict[str, float]]:
        # Minimal reconciliation: ensure no NaNs, positions non-negative
        for sym, q in acct.positions.items():
            if q < -1e-12:
                raise RuntimeError(f"NEGATIVE_POSITION:{sym}")
        if acct.cash != acct.cash:
            raise RuntimeError("CASH_NAN")
        return acct.cash, dict(acct.positions)
