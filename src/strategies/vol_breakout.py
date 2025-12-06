# src/strategies/vol_breakout.py
"""
Peak_Trade Volatility Breakout Strategy (Phase 27)
==================================================

Breakout-Strategie basierend auf Volatilitätskontraktion und -expansion.

Konzept (Coiled Spring):
- Identifiziere Phasen niedriger Volatilität (Kontraktion)
- Entry: Breakout über/unter Range bei steigender Volatilität
- Exit: Rückkehr in die Range oder Trailing-Stop

Diese Strategie eignet sich besonders für Märkte mit klaren
Konsolidierungs- und Ausbruchsphasen.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


class VolBreakoutStrategy(BaseStrategy):
    """
    Volatility Breakout Strategy (ATR/Range-basiert).

    Signale:
    - 1 (long): Breakout über das n-Bar-Hoch bei hoher Volatilität
    - -1 (short): Breakout unter das n-Bar-Tief bei hoher Volatilität
    - 0: Keine Änderung / Flat

    Die Strategie kombiniert zwei Elemente:
    1. Range-Breakout: Preis durchbricht n-Bar Hoch/Tief
    2. Volatilitäts-Filter: ATR muss über Schwelle sein (keine Breakouts bei zu niedriger Vol)

    Args:
        lookback_breakout: Lookback für Breakout-Range (default: 20)
        vol_window: Fenster für ATR-Berechnung (default: 14)
        vol_percentile: Volatilitäts-Perzentil für Filter (default: 50)
        atr_multiple: ATR-Multiple für Breakout-Bestätigung (default: 1.5)
        side: Trading-Richtung ("long", "short", "both") (default: "both")
        config: Optional Config-Dict (überschreibt Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = VolBreakoutStrategy(lookback_breakout=20, vol_window=14)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = VolBreakoutStrategy.from_config(config, "strategy.vol_breakout")
    """

    KEY = "vol_breakout"

    def __init__(
        self,
        lookback_breakout: int = 20,
        vol_window: int = 14,
        vol_percentile: float = 50.0,
        atr_multiple: float = 1.5,
        side: str = "both",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Volatility Breakout Strategy.

        Args:
            lookback_breakout: Lookback für Hoch/Tief-Range
            vol_window: Fenster für ATR-Berechnung
            vol_percentile: Perzentil für Vol-Filter (0-100)
            atr_multiple: ATR-Multiple für Breakout-Bestätigung
            side: "long", "short", oder "both"
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "lookback_breakout": lookback_breakout,
            "vol_window": vol_window,
            "vol_percentile": vol_percentile,
            "atr_multiple": atr_multiple,
            "side": side,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Volatility Breakout",
                description="ATR-basierte Breakout-Strategie nach Volatilitätskontraktion",
                version="1.0.0",
                author="Peak_Trade",
                regime="breakout",
                tags=["breakout", "volatility", "atr", "range"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.lookback_breakout = int(self.config.get("lookback_breakout", lookback_breakout))
        self.vol_window = int(self.config.get("vol_window", vol_window))
        self.vol_percentile = float(self.config.get("vol_percentile", vol_percentile))
        self.atr_multiple = float(self.config.get("atr_multiple", atr_multiple))
        self.side = str(self.config.get("side", side)).lower()

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.lookback_breakout < 2:
            raise ValueError(f"lookback_breakout ({self.lookback_breakout}) muss >= 2 sein")
        if self.vol_window < 2:
            raise ValueError(f"vol_window ({self.vol_window}) muss >= 2 sein")
        if not (0 <= self.vol_percentile <= 100):
            raise ValueError(f"vol_percentile ({self.vol_percentile}) muss zwischen 0 und 100 liegen")
        if self.atr_multiple <= 0:
            raise ValueError(f"atr_multiple ({self.atr_multiple}) muss > 0 sein")
        if self.side not in ("long", "short", "both"):
            raise ValueError(f"side ({self.side}) muss 'long', 'short' oder 'both' sein")

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.vol_breakout",
    ) -> "VolBreakoutStrategy":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            VolBreakoutStrategy-Instanz
        """
        lookback = cfg.get(f"{section}.lookback_breakout", 20)
        vol_window = cfg.get(f"{section}.vol_window", 14)
        vol_percentile = cfg.get(f"{section}.vol_percentile", 50.0)
        atr_multiple = cfg.get(f"{section}.atr_multiple", 1.5)
        side = cfg.get(f"{section}.side", "both")

        return cls(
            lookback_breakout=lookback,
            vol_window=vol_window,
            vol_percentile=vol_percentile,
            atr_multiple=atr_multiple,
            side=side,
        )

    def _compute_atr(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet Average True Range (ATR).

        Args:
            data: DataFrame mit high, low, close

        Returns:
            ATR als pd.Series
        """
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR (EMA des True Range)
        atr = tr.ewm(span=self.vol_window, min_periods=self.vol_window, adjust=False).mean()

        return atr

    def _compute_breakout_levels(self, data: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
        """
        Berechnet Breakout-Levels (n-Bar Hoch und Tief).

        Args:
            data: DataFrame mit high, low

        Returns:
            (upper_level, lower_level) als pd.Series
        """
        # Rolling High/Low (exklusive aktuelle Bar)
        upper_level = data["high"].shift(1).rolling(
            window=self.lookback_breakout, min_periods=self.lookback_breakout
        ).max()

        lower_level = data["low"].shift(1).rolling(
            window=self.lookback_breakout, min_periods=self.lookback_breakout
        ).min()

        return upper_level, lower_level

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit OHLCV-Daten (high, low, close erforderlich)

        Returns:
            Series mit Signalen (1=long, -1=short, 0=flat)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalten fehlen
        """
        # Validierung
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(
                    f"Spalte '{col}' nicht in DataFrame. "
                    f"Verfügbar: {list(data.columns)}"
                )

        min_bars = max(self.lookback_breakout, self.vol_window) + 10
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mind. {min_bars} Bars, habe nur {len(data)}"
            )

        # ATR berechnen
        atr = self._compute_atr(data)

        # Rolling ATR-Perzentil für Vol-Filter
        atr_percentile = atr.rolling(
            window=self.lookback_breakout * 2, min_periods=self.vol_window
        ).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100, raw=False)

        # Breakout-Levels
        upper_level, lower_level = self._compute_breakout_levels(data)

        # Vol-Filter: ATR muss über dem Perzentil liegen
        vol_filter = atr_percentile >= self.vol_percentile

        # Breakout-Bedingungen
        close = data["close"]
        high = data["high"]
        low = data["low"]

        # Long Breakout: Close über Upper Level UND Vol-Filter
        long_breakout = (close > upper_level) & vol_filter

        # Short Breakout: Close unter Lower Level UND Vol-Filter
        short_breakout = (close < lower_level) & vol_filter

        # Signale initialisieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Entry-Signale basierend auf side
        if self.side in ("long", "both"):
            # Long Entry: Neuer Breakout (vorher nicht im Breakout)
            prev_long = long_breakout.shift(1).infer_objects(copy=False).fillna(False)
            long_entry = long_breakout & ~prev_long
            signals[long_entry] = 1

        if self.side in ("short", "both"):
            # Short Entry: Neuer Breakout (vorher nicht im Breakout)
            prev_short = short_breakout.shift(1).infer_objects(copy=False).fillna(False)
            short_entry = short_breakout & ~prev_short
            signals[short_entry] = -1

        # State-Logik: Position halten bis Gegenrichtung
        # Fix für Pandas FutureWarning
        state = signals.replace(0, float('nan'))
        state = state.ffill()
        state = state.fillna(0).astype(int)

        return state


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte VolBreakoutStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (1=long, -1=short, 0=flat)
    """
    config = {
        "lookback_breakout": params.get("lookback_breakout", 20),
        "vol_window": params.get("vol_window", 14),
        "vol_percentile": params.get("vol_percentile", 50.0),
        "atr_multiple": params.get("atr_multiple", 1.5),
        "side": params.get("side", "both"),
    }

    strategy = VolBreakoutStrategy(config=config)
    return strategy.generate_signals(df)


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
Volatility Breakout Strategy
============================
Lookback Breakout: {params.get('lookback_breakout', 20)} Bars
Vol Window (ATR):  {params.get('vol_window', 14)} Bars
Vol Percentile:    {params.get('vol_percentile', 50.0)}%
ATR Multiple:      {params.get('atr_multiple', 1.5)}x
Side:              {params.get('side', 'both')}

Konzept:
- Entry Long:  Close > {params.get('lookback_breakout', 20)}-Bar High + Vol-Filter
- Entry Short: Close < {params.get('lookback_breakout', 20)}-Bar Low + Vol-Filter
- Vol-Filter:  ATR im {params.get('vol_percentile', 50.0)}. Perzentil
"""
