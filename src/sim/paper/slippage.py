from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlippageModel:
    # basis points applied against the trader (BUY pays more, SELL receives less)
    bps: float = 0.0

    def apply(self, side: str, mid_price: float) -> float:
        mult = 1.0 + (self.bps / 10_000.0) if side == "BUY" else 1.0 - (self.bps / 10_000.0)
        return mid_price * mult
