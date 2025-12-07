# src/strategies/mean_reversion.py
"""
Peak_Trade Mean Reversion Strategy
===================================
Mean-Reversion-Strategie basierend auf Z-Score.

Konzept:
- Der Z-Score misst, wie viele Standardabweichungen der aktuelle Preis
  vom gleitenden Durchschnitt entfernt ist.
- Long-Entry: Z-Score < -entry_threshold (Preis stark unter Durchschnitt)
- Exit: Z-Score > exit_threshold (Preis erreicht/überschreitet Durchschnitt)

Diese Strategie funktioniert am besten in Seitwärtsmärkten (Ranging)
und kann in starken Trends Verluste produzieren.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


class MeanReversionStrategy(BaseStrategy):
    """
    Z-Score-basierte Mean-Reversion-Strategie (OOP-Version).

    Signale:
    - 1 (long): Z-Score < -entry_threshold (überverkauft)
    - -1 (exit): Z-Score > exit_threshold (zurück zum Mittel)
    - 0: Keine Änderung

    Optional kann ein Volatilitätsfilter aktiviert werden, der
    nur in niedriger Volatilität handelt (typische Mean-Reversion-Umgebung).

    Args:
        lookback: Periode für gleitenden Durchschnitt und Std (default: 20)
        entry_threshold: Z-Score für Entry (negativ, default: -2.0)
        exit_threshold: Z-Score für Exit (default: 0.0 = Mittelwert)
        use_vol_filter: Ob Volatilitätsfilter verwendet wird (default: False)
        vol_window: Fenster für Volatilitätsberechnung (default: 20)
        max_vol_percentile: Maximale Volatilität für Entry (default: 70)
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = MeanReversionStrategy(lookback=20, entry_threshold=-2.0)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = MeanReversionStrategy.from_config(config, "strategy.mean_reversion")
    """

    KEY = "mean_reversion"

    def __init__(
        self,
        lookback: int = 20,
        entry_threshold: float = -2.0,
        exit_threshold: float = 0.0,
        use_vol_filter: bool = False,
        vol_window: int = 20,
        max_vol_percentile: float = 70.0,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Mean-Reversion-Strategie.

        Args:
            lookback: Lookback-Fenster für Z-Score-Berechnung
            entry_threshold: Entry bei Z-Score unter diesem Wert (negativ!)
            exit_threshold: Exit bei Z-Score über diesem Wert
            use_vol_filter: Wenn True, nur bei niedriger Volatilität handeln
            vol_window: Fenster für Volatilitätsberechnung
            max_vol_percentile: Maximale Volatilitäts-Perzentile für Entry
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "lookback": lookback,
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
            "use_vol_filter": use_vol_filter,
            "vol_window": vol_window,
            "max_vol_percentile": max_vol_percentile,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Mean Reversion",
                description="Z-Score-basierte Mean-Reversion-Strategie",
                version="1.0.0",
                author="Peak_Trade",
                regime="ranging",
                tags=["mean-reversion", "z-score", "contrarian"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.lookback = int(self.config.get("lookback", lookback))
        self.entry_threshold = float(self.config.get("entry_threshold", entry_threshold))
        self.exit_threshold = float(self.config.get("exit_threshold", exit_threshold))
        self.use_vol_filter = bool(self.config.get("use_vol_filter", use_vol_filter))
        self.vol_window = int(self.config.get("vol_window", vol_window))
        self.max_vol_percentile = float(self.config.get("max_vol_percentile", max_vol_percentile))

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.lookback <= 1:
            raise ValueError(f"lookback ({self.lookback}) muss > 1 sein")
        if self.entry_threshold >= self.exit_threshold:
            raise ValueError(
                f"entry_threshold ({self.entry_threshold}) muss < exit_threshold ({self.exit_threshold}) sein"
            )
        if self.vol_window <= 1:
            raise ValueError(f"vol_window ({self.vol_window}) muss > 1 sein")
        if not 0 < self.max_vol_percentile <= 100:
            raise ValueError(
                f"max_vol_percentile ({self.max_vol_percentile}) muss zwischen 0 und 100 sein"
            )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.mean_reversion",
    ) -> "MeanReversionStrategy":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            MeanReversionStrategy-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> config = load_config()
            >>> strategy = MeanReversionStrategy.from_config(config)
        """
        lookback = cfg.get(f"{section}.lookback", 20)
        entry_threshold = cfg.get(f"{section}.entry_threshold", -2.0)
        exit_threshold = cfg.get(f"{section}.exit_threshold", 0.0)
        use_vol_filter = cfg.get(f"{section}.use_vol_filter", False)
        vol_window = cfg.get(f"{section}.vol_window", 20)
        max_vol_percentile = cfg.get(f"{section}.max_vol_percentile", 70.0)

        return cls(
            lookback=lookback,
            entry_threshold=entry_threshold,
            exit_threshold=exit_threshold,
            use_vol_filter=use_vol_filter,
            vol_window=vol_window,
            max_vol_percentile=max_vol_percentile,
        )

    def _compute_zscore(self, prices: pd.Series) -> pd.Series:
        """
        Berechnet den Z-Score.

        Z-Score = (Price - MA) / Std

        Args:
            prices: Close-Preise

        Returns:
            Z-Score-Series
        """
        ma = prices.rolling(window=self.lookback, min_periods=self.lookback).mean()
        std = prices.rolling(window=self.lookback, min_periods=self.lookback).std()

        # Z-Score berechnen, Division durch 0 vermeiden
        zscore = (prices - ma) / std.replace(0, np.nan)

        return zscore

    def _compute_volatility_filter(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet Volatilitätsfilter.

        Returns True wenn aktuelle Volatilität unter max_vol_percentile liegt.

        Args:
            data: DataFrame mit close

        Returns:
            Boolean-Series (True = Volatilität niedrig genug)
        """
        # Realisierte Volatilität (Rolling Std of Returns)
        returns = data["close"].pct_change()
        vol = returns.rolling(window=self.vol_window).std()

        # Expanding Percentile der Volatilität
        vol_percentile = vol.expanding().apply(
            lambda x: (x.iloc[-1:].values[0] <= x).mean() * 100
            if len(x) > 0 else 50,
            raw=False
        )

        # Filter: Nur wenn Volatilität unter Schwelle
        return vol_percentile <= self.max_vol_percentile

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens 'close')

        Returns:
            Series mit Signalen (1=long, -1=exit, 0=neutral, Index=data.index)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        # Validierung
        if "close" not in data.columns:
            raise ValueError(
                f"Spalte 'close' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        min_bars = max(self.lookback, self.vol_window) + 10
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mind. {min_bars} Bars, habe nur {len(data)}"
            )

        # Z-Score berechnen
        zscore = self._compute_zscore(data["close"])

        # Signale initialisieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Entry-Bedingung: Z-Score stark negativ (überverkauft)
        entry_condition = zscore < self.entry_threshold

        # Volatilitätsfilter anwenden falls aktiviert
        if self.use_vol_filter:
            vol_ok = self._compute_volatility_filter(data)
            entry_condition = entry_condition & vol_ok

        # Exit-Bedingung: Z-Score zurück zum/über Mittelwert
        exit_condition = zscore > self.exit_threshold

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

    DEPRECATED: Bitte MeanReversionStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (1=long, -1=exit, 0=neutral)

    Example:
        >>> signals = generate_signals(df, {"lookback": 20, "entry_threshold": -2.0})
    """
    config = {
        "lookback": params.get("lookback", 20),
        "entry_threshold": params.get("entry_threshold", -2.0),
        "exit_threshold": params.get("exit_threshold", 0.0),
        "use_vol_filter": params.get("use_vol_filter", False),
        "vol_window": params.get("vol_window", 20),
        "max_vol_percentile": params.get("max_vol_percentile", 70.0),
    }

    strategy = MeanReversionStrategy(config=config)
    return strategy.generate_signals(df)


def add_zscore_indicators(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    """
    Fügt Z-Score-Indikatoren zum DataFrame hinzu (für Visualisierung).

    Args:
        df: OHLCV-DataFrame
        params: Dict mit 'lookback'

    Returns:
        DataFrame mit zusätzlichen Spalten: 'zscore', 'ma', 'upper_band', 'lower_band'
    """
    df = df.copy()

    lookback = params.get("lookback", 20)
    entry_threshold = params.get("entry_threshold", -2.0)
    exit_threshold = params.get("exit_threshold", 0.0)

    # MA und Std
    df["ma"] = df["close"].rolling(window=lookback).mean()
    std = df["close"].rolling(window=lookback).std()

    # Z-Score
    df["zscore"] = (df["close"] - df["ma"]) / std

    # Bands für Visualisierung
    df["upper_band"] = df["ma"] + (exit_threshold * std)
    df["lower_band"] = df["ma"] + (entry_threshold * std)

    return df


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
Mean Reversion Strategy (Z-Score)
==================================
Lookback:          {params.get('lookback', 20)} Bars
Entry-Threshold:   {params.get('entry_threshold', -2.0)} Std
Exit-Threshold:    {params.get('exit_threshold', 0.0)} Std
Vol-Filter:        {'Aktiv' if params.get('use_vol_filter', False) else 'Inaktiv'}

Konzept:
- Entry: Z-Score < {params.get('entry_threshold', -2.0)} (überverkauft)
- Exit: Z-Score > {params.get('exit_threshold', 0.0)} (zurück zum Mittel)

Geeignet für: Seitwärtsmärkte (Ranging)
Nicht geeignet für: Starke Trends
"""
