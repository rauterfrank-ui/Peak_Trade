"""
Peak_Trade Momentum Strategy
==============================
Momentum-basierte Trading-Strategie.

Konzept:
- Long-Entry: Wenn Momentum > entry_threshold
- Exit: Wenn Momentum < exit_threshold
- Momentum = (close / close[lookback]) - 1
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any, Dict, Optional

from .base import BaseStrategy, StrategyMetadata


# ============================================================================
# OOP STRATEGIE-KLASSE
# ============================================================================


class MomentumStrategy(BaseStrategy):
    """
    Momentum-basierte Trading-Strategie (OOP-Version).

    Signale:
    - 1 (long): Momentum kreuzt entry_threshold von unten
    - -1 (exit): Momentum kreuzt exit_threshold von oben
    - 0: Kein Signal

    Args:
        lookback_period: Perioden für Momentum-Berechnung (default: 20)
        entry_threshold: Momentum-Schwelle für Entry (default: 0.02 = 2%)
        exit_threshold: Momentum-Schwelle für Exit (default: -0.01 = -1%)
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = MomentumStrategy(lookback_period=20, entry_threshold=0.02)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = MomentumStrategy.from_config(config, "strategy.momentum_1h")
    """

    KEY = "momentum_1h"

    def __init__(
        self,
        lookback_period: int = 20,
        entry_threshold: float = 0.02,
        exit_threshold: float = -0.01,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Momentum-Strategie.

        Args:
            lookback_period: Lookback-Fenster für Momentum
            entry_threshold: Entry-Schwelle (Momentum muss diesen Wert überschreiten)
            exit_threshold: Exit-Schwelle (Momentum muss diesen Wert unterschreiten)
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "lookback_period": lookback_period,
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Momentum",
                description="Momentum-basierte Trend-Following-Strategie",
                version="1.0.0",
                author="Peak_Trade",
                regime="trending",
                tags=["trend", "momentum"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.lookback_period = self.config.get("lookback_period", lookback_period)
        self.entry_threshold = self.config.get("entry_threshold", entry_threshold)
        self.exit_threshold = self.config.get("exit_threshold", exit_threshold)

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.lookback_period <= 0:
            raise ValueError(
                f"lookback_period ({self.lookback_period}) muss > 0 sein"
            )
        if self.entry_threshold <= self.exit_threshold:
            raise ValueError(
                f"entry_threshold ({self.entry_threshold}) muss > exit_threshold ({self.exit_threshold}) sein"
            )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.momentum_1h",
    ) -> "MomentumStrategy":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            MomentumStrategy-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> config = load_config()
            >>> strategy = MomentumStrategy.from_config(config)
        """
        lookback = cfg.get(f"{section}.lookback_period", 20)
        entry = cfg.get(f"{section}.entry_threshold", 0.02)
        exit_thresh = cfg.get(f"{section}.exit_threshold", -0.01)

        return cls(
            lookback_period=lookback,
            entry_threshold=entry,
            exit_threshold=exit_thresh,
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens 'close')

        Returns:
            Series mit Signalen (1=entry, -1=exit, 0=neutral, Index=data.index)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        # Validierung
        if "close" not in data.columns:
            raise ValueError(
                f"Spalte 'close' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        if len(data) < self.lookback_period:
            raise ValueError(
                f"Brauche mind. {self.lookback_period} Bars, habe nur {len(data)}"
            )

        # Momentum berechnen: (Close heute / Close vor N Tagen) - 1
        momentum = (data["close"] / data["close"].shift(self.lookback_period)) - 1

        # Signale initialisieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Entry-Logik: Momentum überschreitet Entry-Threshold
        cross_up = (momentum.shift(1) < self.entry_threshold) & (
            momentum > self.entry_threshold
        )
        signals[cross_up] = 1

        # Exit-Logik: Momentum fällt unter Exit-Threshold
        cross_down = (momentum.shift(1) > self.exit_threshold) & (
            momentum < self.exit_threshold
        )
        signals[cross_down] = -1

        return signals


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================
# TODO: Legacy-Funktion entfernen, sobald alle Pipelines auf
# MomentumStrategy (OOP) umgestellt sind.


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Generiert Momentum-basierte Signale.
    
    Args:
        df: OHLCV-DataFrame mit DatetimeIndex
        params: Dict mit 'lookback_period', 'entry_threshold', 'exit_threshold'
        
    Returns:
        Series mit Werten:
        - 1: Long-Signal
        - 0: Kein Signal (Neutral)
        - -1: Exit-Signal
        
    Example:
        >>> params = {
        ...     'lookback_period': 20,
        ...     'entry_threshold': 0.02,
        ...     'exit_threshold': -0.01
        ... }
        >>> signals = generate_signals(df, params)
    """
    # Parameter extrahieren
    lookback = params.get('lookback_period', 20)
    entry_threshold = params.get('entry_threshold', 0.02)
    exit_threshold = params.get('exit_threshold', -0.01)
    
    # Validierung
    if lookback <= 0:
        raise ValueError(f"lookback_period ({lookback}) muss > 0 sein")
    
    if len(df) < lookback:
        raise ValueError(f"DataFrame zu kurz ({len(df)} Bars), brauche min. {lookback}")
    
    # Momentum berechnen: (Close heute / Close vor N Tagen) - 1
    momentum = (df['close'] / df['close'].shift(lookback)) - 1
    
    # Signale initialisieren
    signals = pd.Series(0, index=df.index, dtype=int)
    
    # Entry-Logik: Momentum überschreitet Entry-Threshold
    # Bedingung: Momentum[t-1] < entry_threshold UND Momentum[t] > entry_threshold
    cross_up = (momentum.shift(1) < entry_threshold) & (momentum > entry_threshold)
    signals[cross_up] = 1
    
    # Exit-Logik: Momentum fällt unter Exit-Threshold
    cross_down = (momentum.shift(1) > exit_threshold) & (momentum < exit_threshold)
    signals[cross_down] = -1
    
    return signals


def add_momentum_indicators(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    """
    Fügt Momentum-Indikatoren zum DataFrame hinzu (für Visualisierung).
    
    Args:
        df: OHLCV-DataFrame
        params: Dict mit 'lookback_period'
        
    Returns:
        DataFrame mit zusätzlicher Spalte 'momentum'
        
    Example:
        >>> df_with_mom = add_momentum_indicators(df, {'lookback_period': 20})
        >>> print(df_with_mom[['close', 'momentum']].tail())
    """
    df = df.copy()
    
    lookback = params.get('lookback_period', 20)
    
    # Momentum berechnen
    df['momentum'] = (df['close'] / df['close'].shift(lookback)) - 1
    
    # Optional: Glättung mit EMA
    df['momentum_ema'] = df['momentum'].ewm(span=5, adjust=False).mean()
    
    return df


def get_strategy_description(params: Dict) -> str:
    """
    Gibt Strategie-Beschreibung zurück.
    
    Args:
        params: Strategie-Parameter
        
    Returns:
        Beschreibungstext
    """
    return f"""
Momentum-Strategie (1h)
=======================
Lookback-Period:   {params.get('lookback_period', 20)} Bars
Entry-Threshold:   {params.get('entry_threshold', 0.02):.1%}
Exit-Threshold:    {params.get('exit_threshold', -0.01):.1%}
Stop-Loss:         {params.get('stop_pct', 0.025):.1%}

Konzept:
- Long wenn Momentum > {params.get('entry_threshold', 0.02):.1%}
- Exit wenn Momentum < {params.get('exit_threshold', -0.01):.1%}
"""
