"""
Position-Sizing-Module: Konvertieren Exposure in konkrete Stückzahlen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from .base import BaseRiskModule


@dataclass
class FixedFractionalPositionSizer(BaseRiskModule):
    """
    Fixed-Fractional Position-Sizing.

    Wandelt Exposure-Signale (-1..+1) in Stückzahlen um, basierend auf
    einem festen Kapitalanteil pro Einheit Signal.

    Beispiel:
        initial_capital = 100_000
        risk_fraction = 0.01
        price = 100
        signal = +1.0

        → Ziel-Notional = 0.01 * 100_000 = 1_000
        → Stückzahl = 1_000 / 100 = 10

    Attributes:
        risk_fraction: Anteil des Kapitals pro 1.0 Exposure (default: 0.01)
    """

    risk_fraction: float = 0.01

    def apply(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        prices: pd.Series,
        initial_capital: float,
    ) -> pd.Series:
        """
        Berechnet Stückzahl basierend auf Fixed-Fractional-Sizing.

        Returns:
            pd.Series mit Stückzahlen (Units)
        """
        # Align auf df.index
        signals = signals.reindex(df.index).ffill().fillna(0.0).astype(float)
        prices = prices.reindex(df.index).ffill()

        # Validierung: Preise dürfen nicht <= 0 sein
        if (prices <= 0).any():
            raise ValueError("Preise müssen positiv sein für Position-Sizing.")

        # Notional pro Unit Signal
        notional_per_unit = self.risk_fraction * float(initial_capital)

        # Stückzahl berechnen
        units = (signals * notional_per_unit) / prices

        return units


@dataclass
class VolatilityTargetPositionSizer(BaseRiskModule):
    """
    Volatility-Targeting Position-Sizing.

    Passt Positionsgröße basierend auf historischer Volatilität an:
    - Hohe Volatilität → kleinere Positionen
    - Niedrige Volatilität → größere Positionen

    Ziel: Konstante Zielvolatilität (target_vol_annual) erreichen.

    Attributes:
        target_vol_annual: Zielvolatilität p.a. (default: 0.2 = 20%)
        lookback_days: Fenster für Volatilitätsschätzung (default: 20)
        max_leverage: Maximaler Hebel auf Kapital (default: 3.0)
    """

    target_vol_annual: float = 0.2
    lookback_days: int = 20
    max_leverage: float = 3.0

    def apply(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        prices: pd.Series,
        initial_capital: float,
    ) -> pd.Series:
        """
        Berechnet Stückzahl mit Volatility-Targeting.

        Returns:
            pd.Series mit volatilitäts-adjustierten Stückzahlen
        """
        # Align
        signals = signals.reindex(df.index).ffill().fillna(0.0).astype(float)
        prices = prices.reindex(df.index).ffill()

        # Validierung
        if (prices <= 0).any():
            raise ValueError("Preise müssen positiv sein für Position-Sizing.")

        # Volatilitätsschätzung
        if isinstance(df.index, pd.DatetimeIndex):
            # Daily resampling
            daily_px = prices.resample("1D").last().dropna()
            daily_ret = daily_px.pct_change().dropna()

            # Rolling Volatility (daily)
            vol_daily = daily_ret.rolling(window=self.lookback_days).std(ddof=1)
            vol_annual = vol_daily * np.sqrt(252)

            # Zurück auf df.index mappen
            vol_annual = vol_annual.reindex(df.index, method="ffill")
        else:
            # Fallback: Bar-basierte Returns
            bar_ret = prices.pct_change().dropna()
            vol = bar_ret.rolling(window=self.lookback_days).std(ddof=1)
            vol_annual = vol * np.sqrt(252)  # Annahme: ~252 Bars/Jahr
            vol_annual = vol_annual.reindex(df.index).ffill()

        # Leverage-Faktor berechnen
        leverage = pd.Series(0.0, index=df.index)
        valid_vol = vol_annual > 0
        leverage[valid_vol] = self.target_vol_annual / vol_annual[valid_vol]

        # Caps anwenden
        leverage = leverage.clip(lower=0.0, upper=self.max_leverage)

        # NaN → 0 Leverage
        leverage = leverage.fillna(0.0)

        # Notional berechnen
        capital = float(initial_capital)
        notional = capital * leverage * signals

        # Stückzahl
        units = notional / prices

        return units
