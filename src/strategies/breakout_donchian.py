# src/strategies/breakout_donchian.py
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from .base import BaseStrategy, StrategyMetadata


class DonchianBreakoutStrategy(BaseStrategy):
    """
    Donchian-Breakout-Strategie:

    - close > N-Tage-Hoch → Ziel-Position = +1 (long)
    - close < N-Tage-Tief → Ziel-Position = -1 (short)
    - sonst               → vorherige Position halten
    """

    KEY = "breakout_donchian"

    def __init__(
        self,
        lookback: int = 20,
        price_col: str = "close",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        base_cfg: Dict[str, Any] = {
            "lookback": lookback,
            "price_col": price_col,
        }
        if config:
            base_cfg.update(config)

        meta = metadata or StrategyMetadata(
            name="DonchianBreakoutStrategy",
            description="Donchian Channel Breakout-Strategie.",
            version="0.1.0",
        )

        super().__init__(config=base_cfg, metadata=meta)

        self.lookback = int(self.config["lookback"])
        self.price_col = str(self.config["price_col"])

    @classmethod
    def from_config(
        cls,
        cfg: "PeakConfigLike",
        section: str = "strategy.breakout_donchian",
    ) -> "DonchianBreakoutStrategy":
        lookback = cfg.get(f"{section}.lookback", 20)
        price = cfg.get(f"{section}.price_col", "close")
        return cls(
            lookback=lookback,
            price_col=price,
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if self.price_col not in data.columns:
            raise KeyError(
                f"Spalte {self.price_col!r} nicht im DataFrame. "
                f"Vorhandene Spalten: {list(data.columns)}"
            )

        price = data[self.price_col].astype(float)

        # Donchian-Bänder: High/Low der letzten N Perioden (exklusive aktuelle Kerze)
        rolling_high = price.shift(1).rolling(self.lookback, min_periods=self.lookback).max()
        rolling_low = price.shift(1).rolling(self.lookback, min_periods=self.lookback).min()

        # Roh-Signale: +1, -1, 0
        raw = pd.Series(0, index=data.index, dtype="int64")

        # Breakout nach oben (Long)
        raw = raw.where(~(price > rolling_high), 1)

        # Breakout nach unten (Short)
        raw = raw.where(~(price < rolling_low), -1)

        # State-Logik: 0 => halte vorige Position
        # Fix für Pandas FutureWarning: verwende numpy NaN statt pd.NA
        state = raw.replace(0, float('nan'))
        state = state.ffill()
        state = state.fillna(0).astype(int)

        state.name = "signal"
        return state


# Für Typ-Hints ohne harte Abhängigkeit auf core.config
class PeakConfigLike:
    def get(self, path: str, default: Any = None) -> Any:  # pragma: no cover - nur Doku
        ...
