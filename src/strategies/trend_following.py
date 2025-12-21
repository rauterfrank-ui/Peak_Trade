# src/strategies/trend_following.py
"""
Peak_Trade Trend Following Strategy
====================================
Trend-Following-Strategie basierend auf ADX (Average Directional Index)
und gleitenden Durchschnitten.

Konzept:
- Long-Entry: ADX > threshold UND +DI > -DI (starker Aufwärtstrend)
- Exit: ADX < exit_threshold ODER -DI > +DI (Trend schwächt sich ab)

Der ADX misst die Stärke eines Trends (unabhängig von der Richtung),
während +DI/-DI die Trendrichtung anzeigen.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


class TrendFollowingStrategy(BaseStrategy):
    """
    ADX-basierte Trend-Following-Strategie (OOP-Version).

    Signale:
    - 1 (long): ADX > adx_threshold UND +DI > -DI (starker Aufwärtstrend)
    - -1 (exit): ADX < exit_threshold ODER -DI > +DI (Trend endet/dreht)
    - 0: Keine Änderung

    Diese Strategie ist für Trending-Märkte optimiert und vermeidet
    Seitwärtsphasen durch den ADX-Filter.

    Args:
        adx_period: Periode für ADX-Berechnung (default: 14)
        adx_threshold: Mindest-ADX für starken Trend (default: 25)
        exit_threshold: ADX unter diesem Wert = Exit (default: 20)
        ma_period: Periode für Trendfilter-MA (default: 50)
        use_ma_filter: Ob zusätzlich MA-Filter verwendet wird (default: True)
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = TrendFollowingStrategy(adx_period=14, adx_threshold=25)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = TrendFollowingStrategy.from_config(config, "strategy.trend_following")
    """

    KEY = "trend_following"

    def __init__(
        self,
        adx_period: int = 14,
        adx_threshold: float = 25.0,
        exit_threshold: float = 20.0,
        ma_period: int = 50,
        use_ma_filter: bool = True,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Trend-Following-Strategie.

        Args:
            adx_period: Periode für ADX-Indikator
            adx_threshold: ADX muss über diesem Wert sein für Entry
            exit_threshold: ADX unter diesem Wert triggert Exit
            ma_period: Periode für gleitenden Durchschnitt (Trendfilter)
            use_ma_filter: Wenn True, muss Preis über MA sein für Long
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "adx_period": adx_period,
            "adx_threshold": adx_threshold,
            "exit_threshold": exit_threshold,
            "ma_period": ma_period,
            "use_ma_filter": use_ma_filter,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Trend Following",
                description="ADX-basierte Trend-Following-Strategie",
                version="1.0.0",
                author="Peak_Trade",
                regime="trending",
                tags=["trend", "adx", "momentum"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.adx_period = int(self.config.get("adx_period", adx_period))
        self.adx_threshold = float(self.config.get("adx_threshold", adx_threshold))
        self.exit_threshold = float(self.config.get("exit_threshold", exit_threshold))
        self.ma_period = int(self.config.get("ma_period", ma_period))
        self.use_ma_filter = bool(self.config.get("use_ma_filter", use_ma_filter))

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.adx_period <= 0:
            raise ValueError(f"adx_period ({self.adx_period}) muss > 0 sein")
        if self.adx_threshold <= 0:
            raise ValueError(f"adx_threshold ({self.adx_threshold}) muss > 0 sein")
        if self.exit_threshold >= self.adx_threshold:
            raise ValueError(
                f"exit_threshold ({self.exit_threshold}) muss < adx_threshold ({self.adx_threshold}) sein"
            )
        if self.ma_period <= 0:
            raise ValueError(f"ma_period ({self.ma_period}) muss > 0 sein")

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.trend_following",
    ) -> "TrendFollowingStrategy":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            TrendFollowingStrategy-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> config = load_config()
            >>> strategy = TrendFollowingStrategy.from_config(config)
        """
        adx_period = cfg.get(f"{section}.adx_period", 14)
        adx_threshold = cfg.get(f"{section}.adx_threshold", 25.0)
        exit_threshold = cfg.get(f"{section}.exit_threshold", 20.0)
        ma_period = cfg.get(f"{section}.ma_period", 50)
        use_ma_filter = cfg.get(f"{section}.use_ma_filter", True)

        return cls(
            adx_period=adx_period,
            adx_threshold=adx_threshold,
            exit_threshold=exit_threshold,
            ma_period=ma_period,
            use_ma_filter=use_ma_filter,
        )

    def _compute_adx(self, data: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Berechnet ADX, +DI und -DI.

        Args:
            data: DataFrame mit high, low, close

        Returns:
            (adx, plus_di, minus_di) als pd.Series
        """
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # +DM / -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()

        # Nur positive Werte behalten
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
        minus_dm = minus_dm.where(
            (minus_dm > plus_dm.where(plus_dm != 0, -1)) & (minus_dm > 0), 0.0
        )

        # Smoothed Averages (Wilder-Smoothing)
        atr = tr.ewm(alpha=1 / self.adx_period, min_periods=self.adx_period, adjust=False).mean()
        smoothed_plus_dm = plus_dm.ewm(
            alpha=1 / self.adx_period, min_periods=self.adx_period, adjust=False
        ).mean()
        smoothed_minus_dm = minus_dm.ewm(
            alpha=1 / self.adx_period, min_periods=self.adx_period, adjust=False
        ).mean()

        # +DI / -DI
        plus_di = 100 * smoothed_plus_dm / atr.replace(0, np.nan)
        minus_di = 100 * smoothed_minus_dm / atr.replace(0, np.nan)

        # DX und ADX
        di_sum = plus_di + minus_di
        di_diff = abs(plus_di - minus_di)
        dx = 100 * di_diff / di_sum.replace(0, np.nan)
        adx = dx.ewm(alpha=1 / self.adx_period, min_periods=self.adx_period, adjust=False).mean()

        return adx, plus_di, minus_di

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit OHLCV-Daten (high, low, close erforderlich)

        Returns:
            Series mit Signalen (1=long, -1=exit, 0=neutral, Index=data.index)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalten fehlen
        """
        # Validierung
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(
                    f"Spalte '{col}' nicht in DataFrame. Verfügbar: {list(data.columns)}"
                )

        min_bars = max(self.adx_period * 2, self.ma_period) + 10
        if len(data) < min_bars:
            raise ValueError(f"Brauche mind. {min_bars} Bars, habe nur {len(data)}")

        # ADX und DI berechnen
        adx, plus_di, minus_di = self._compute_adx(data)

        # MA für Trendfilter
        ma = data["close"].rolling(window=self.ma_period).mean()

        # Signale initialisieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Entry-Bedingungen: ADX stark UND +DI > -DI (Aufwärtstrend)
        adx_strong = adx > self.adx_threshold
        uptrend = plus_di > minus_di

        if self.use_ma_filter:
            price_above_ma = data["close"] > ma
            entry_condition = adx_strong & uptrend & price_above_ma
        else:
            entry_condition = adx_strong & uptrend

        # Exit-Bedingungen: ADX schwach ODER Abwärtstrend
        adx_weak = adx < self.exit_threshold
        downtrend = minus_di > plus_di
        exit_condition = adx_weak | downtrend

        # Entry: Vorherige Bar kein Entry, aktuelle Bar Entry
        entry_trigger = entry_condition & ~entry_condition.shift(1).fillna(False).astype(bool)
        signals[entry_trigger] = 1

        # Exit: Vorherige Bar kein Exit, aktuelle Bar Exit
        exit_trigger = exit_condition & ~exit_condition.shift(1).fillna(False).astype(bool)
        signals[exit_trigger] = -1

        return signals


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte TrendFollowingStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (1=long, -1=exit, 0=neutral)

    Example:
        >>> signals = generate_signals(df, {"adx_period": 14, "adx_threshold": 25})
    """
    config = {
        "adx_period": params.get("adx_period", 14),
        "adx_threshold": params.get("adx_threshold", 25.0),
        "exit_threshold": params.get("exit_threshold", 20.0),
        "ma_period": params.get("ma_period", 50),
        "use_ma_filter": params.get("use_ma_filter", True),
    }

    strategy = TrendFollowingStrategy(config=config)
    return strategy.generate_signals(df)


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
Trend Following Strategy (ADX-basiert)
=======================================
ADX-Periode:       {params.get("adx_period", 14)} Bars
ADX-Threshold:     {params.get("adx_threshold", 25.0)}
Exit-Threshold:    {params.get("exit_threshold", 20.0)}
MA-Periode:        {params.get("ma_period", 50)} Bars
MA-Filter:         {"Aktiv" if params.get("use_ma_filter", True) else "Inaktiv"}

Konzept:
- Entry: ADX > {params.get("adx_threshold", 25.0)} UND +DI > -DI (starker Trend)
- Exit: ADX < {params.get("exit_threshold", 20.0)} ODER Trendwechsel
"""
