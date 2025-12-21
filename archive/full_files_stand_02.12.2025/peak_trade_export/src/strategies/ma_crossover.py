"""
MA-Crossover-Strategie: Long bei Fast > Slow, Short bei Fast < Slow.
"""

from typing import Any, Dict
import pandas as pd
from .base import BaseStrategy
from .registry import register_strategy


@register_strategy
class MaCrossoverStrategy(BaseStrategy):
    """
    Moving-Average-Crossover mit State-basierter Glättung.

    Parameter:
        fast: Periode für schnellen MA (default: 20)
        slow: Periode für langsamen MA (default: 50)
    """

    name = "ma_crossover"

    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """
        Generiert Signals basierend auf MA-Crossover.

        Returns:
            pd.Series mit -1 (short), 0 (flat), +1 (long)
        """
        # Parameter
        fast = params.get("fast", 20)
        slow = params.get("slow", 50)

        # Preise
        close = df["close"].astype(float)

        # Moving Averages
        ma_fast = close.rolling(window=fast).mean()
        ma_slow = close.rolling(window=slow).mean()

        # Rohsignale
        sig = pd.Series(0.0, index=df.index)
        sig[ma_fast > ma_slow] = 1.0
        sig[ma_fast < ma_slow] = -1.0

        # State-basierte Glättung (nur bei echtem Wechsel)
        last_pos = 0.0
        smoothed = []

        for v in sig.values:
            if not pd.isna(v) and v != last_pos:
                last_pos = v
            smoothed.append(last_pos)

        result = pd.Series(smoothed, index=df.index)

        # State speichern
        self._state["last_position"] = float(last_pos)

        return result
