"""
Risk-Guards: Sicherheitsmechanismen zur Verlustbegrenzung.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .base import BaseRiskModule


@dataclass
class MaxDrawdownGuard(BaseRiskModule):
    """
    Max-Drawdown-Guard: Hard-Stop bei Drawdown-Schwelle.

    Deaktiviert alle Positionen, sobald der Preis eine bestimmte
    Drawdown-Schwelle von seinem bisherigen Hoch überschreitet.

    WICHTIG: Dies ist eine vereinfachte Preis-basierte Implementierung.
    Für echte Equity-basierte Drawdown-Logik wäre ein komplexeres
    State-Management nötig.

    Attributes:
        max_drawdown: Maximaler erlaubter Drawdown (default: 0.2 = -20%)
    """

    max_drawdown: float = 0.2

    def apply(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        prices: pd.Series,
        initial_capital: float,
    ) -> pd.Series:
        """
        Setzt Signale auf 0, sobald Drawdown-Schwelle überschritten wird.

        Returns:
            Modifizierte Signale (ab Drawdown-Breach = 0)
        """
        # Align
        signals = signals.reindex(df.index).ffill().fillna(0.0).astype(float)
        prices = prices.reindex(df.index).ffill()

        # Drawdown berechnen
        running_max = prices.cummax()
        dd = prices / running_max - 1.0  # negativ bei Drawdown

        # Hard-Stop: Ab erstem Breach alle Signale → 0
        breach_mask = dd <= -self.max_drawdown

        if breach_mask.any():
            # Index des ersten Breach
            first_breach_idx = breach_mask.idxmax()
            breach_loc = df.index.get_loc(first_breach_idx)

            # Alle Signale ab diesem Punkt → 0
            result = signals.copy()
            result.iloc[breach_loc:] = 0.0
            return result

        # Kein Breach → Signale unverändert
        return signals


@dataclass
class DailyLossGuard(BaseRiskModule):
    """
    Daily-Loss-Guard: Stoppt Trading bei Tagesverlusten.

    Schaltet Signale ab, wenn die (preisbasierte) Tagesrendite
    einen bestimmten negativen Schwellwert unterschreitet.

    Attributes:
        max_daily_loss: Maximaler erlaubter Tagesverlust (default: 0.05 = -5%)
    """

    max_daily_loss: float = 0.05

    def apply(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        prices: pd.Series,
        initial_capital: float,
    ) -> pd.Series:
        """
        Setzt Signale auf 0 an Tagen mit hohen Verlusten.

        Returns:
            Modifizierte Signale (an Loss-Tagen = 0)
        """
        # Align
        signals = signals.reindex(df.index).ffill().fillna(0.0).astype(float)
        prices = prices.reindex(df.index).ffill()

        result = signals.copy()

        if isinstance(df.index, pd.DatetimeIndex):
            # Daily resampling
            daily_px = prices.resample("1D").last().dropna()
            daily_ret = daily_px.pct_change().dropna()

            # Tage mit zu hohen Verlusten
            bad_days = daily_ret[daily_ret <= -self.max_daily_loss].index

            # Alle Timestamps an diesen Tagen → 0
            for bad_day in bad_days:
                day_mask = df.index.date == bad_day.date()
                result[day_mask] = 0.0
        else:
            # Fallback: Bar-basierte Returns
            bar_ret = prices.pct_change()
            bad_bars = bar_ret <= -self.max_daily_loss
            result[bad_bars] = 0.0

        return result
