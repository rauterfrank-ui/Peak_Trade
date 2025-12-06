"""
Peak_Trade Bollinger Bands Strategy
====================================
Bollinger Bands-basierte Mean-Reversion-Strategie.

Konzept:
- Long-Entry: Preis berührt untere Band (überverkauft)
- Exit: Preis erreicht Mittel-Band
- Bollinger Bands = MA ± (Std * N)
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any, Dict, Optional, Tuple

from .base import BaseStrategy, StrategyMetadata


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Berechnet Bollinger Bands (interne Helper-Funktion).

    Args:
        prices: Close-Preise
        period: MA-Periode
        num_std: Anzahl Standard-Abweichungen

    Returns:
        (upper_band, middle_band, lower_band)
    """
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    return upper, middle, lower


# ============================================================================
# OOP STRATEGIE-KLASSE
# ============================================================================


class BollingerBandsStrategy(BaseStrategy):
    """
    Bollinger Bands Mean-Reversion-Strategie (OOP-Version).

    Signale:
    - 1 (long): Preis kreuzt entry_level (95% der unteren Band) von oben nach unten
    - -1 (exit): Preis kreuzt middle_band von unten nach oben
    - 0: Kein Signal

    Args:
        bb_period: Periode für Moving Average (default: 20)
        bb_std: Anzahl Standard-Abweichungen (default: 2.0)
        entry_threshold: Entry bei X% der unteren Band (default: 0.95)
        exit_threshold: Exit-Position (unused, für Konsistenz)
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = BollingerBandsStrategy(bb_period=20, bb_std=2.0)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = BollingerBandsStrategy.from_config(config, "strategy.bollinger_bands")
    """

    KEY = "bollinger_bands"

    def __init__(
        self,
        bb_period: int = 20,
        bb_std: float = 2.0,
        entry_threshold: float = 0.95,
        exit_threshold: float = 0.50,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Bollinger Bands-Strategie.

        Args:
            bb_period: Periode für Bollinger Bands
            bb_std: Anzahl Standard-Abweichungen
            entry_threshold: Entry bei X% der unteren Band
            exit_threshold: Für Konsistenz (unused)
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "bb_period": bb_period,
            "bb_std": bb_std,
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Bollinger Bands",
                description="Mean-Reversion-Strategie basierend auf Bollinger Bands",
                version="1.0.0",
                author="Peak_Trade",
                regime="ranging",
                tags=["mean-reversion", "volatility", "bollinger"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.bb_period = self.config.get("bb_period", bb_period)
        self.bb_std = self.config.get("bb_std", bb_std)
        self.entry_threshold = self.config.get("entry_threshold", entry_threshold)
        self.exit_threshold = self.config.get("exit_threshold", exit_threshold)

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.bb_period <= 0:
            raise ValueError(f"bb_period ({self.bb_period}) muss > 0 sein")
        if self.bb_std <= 0:
            raise ValueError(f"bb_std ({self.bb_std}) muss > 0 sein")
        if not 0 < self.entry_threshold <= 1:
            raise ValueError(
                f"entry_threshold ({self.entry_threshold}) muss zwischen 0 und 1 sein"
            )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.bollinger_bands",
    ) -> "BollingerBandsStrategy":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            BollingerBandsStrategy-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> config = load_config()
            >>> strategy = BollingerBandsStrategy.from_config(config)
        """
        period = cfg.get(f"{section}.bb_period", 20)
        std = cfg.get(f"{section}.bb_std", 2.0)
        entry = cfg.get(f"{section}.entry_threshold", 0.95)
        exit_thresh = cfg.get(f"{section}.exit_threshold", 0.50)

        return cls(
            bb_period=period,
            bb_std=std,
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

        if len(data) < self.bb_period:
            raise ValueError(
                f"Brauche mind. {self.bb_period} Bars, habe nur {len(data)}"
            )

        # Bollinger Bands berechnen
        upper, middle, lower = _calculate_bollinger_bands(
            data["close"],
            period=self.bb_period,
            num_std=self.bb_std,
        )

        # Entry-Level: X% der unteren Band (konservativer)
        entry_level = lower * self.entry_threshold

        # Exit-Level: Mittel-Band
        exit_level = middle

        # Signale initialisieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Entry: Preis kreuzt entry_level von oben nach unten
        cross_entry = (data["close"].shift(1) > entry_level.shift(1)) & (
            data["close"] <= entry_level
        )
        signals[cross_entry] = 1

        # Exit: Preis kreuzt exit_level von unten nach oben
        cross_exit = (data["close"].shift(1) < exit_level.shift(1)) & (
            data["close"] >= exit_level
        )
        signals[cross_exit] = -1

        return signals


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================
# TODO: Legacy-Funktion entfernen, sobald alle Pipelines auf
# BollingerBandsStrategy (OOP) umgestellt sind.


def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Berechnet Bollinger Bands.
    
    Args:
        prices: Close-Preise
        period: MA-Periode
        num_std: Anzahl Standard-Abweichungen
        
    Returns:
        (upper_band, middle_band, lower_band)
    """
    # Middle Band = Simple Moving Average
    middle = prices.rolling(window=period).mean()
    
    # Standard-Abweichung
    std = prices.rolling(window=period).std()
    
    # Upper/Lower Bands
    upper = middle + (std * num_std)
    lower = middle - (std * num_std)
    
    return upper, middle, lower


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Generiert Bollinger Bands-Signale.
    
    Args:
        df: OHLCV-DataFrame
        params: Dict mit 'bb_period', 'bb_std', 'entry_threshold', 'exit_threshold'
        
    Returns:
        Series mit Signalen (1 = Long, 0 = Neutral, -1 = Exit)
        
    Strategy:
        - Entry: Preis <= lower_band * entry_threshold (z.B. 95% der unteren Band)
        - Exit: Preis >= middle_band
    """
    # Parameter
    bb_period = params.get('bb_period', 20)
    bb_std = params.get('bb_std', 2.0)
    entry_threshold = params.get('entry_threshold', 0.95)
    exit_threshold = params.get('exit_threshold', 0.50)
    
    # Bollinger Bands berechnen
    upper, middle, lower = calculate_bollinger_bands(
        df['close'],
        period=bb_period,
        num_std=bb_std
    )
    
    # Entry-Level: 95% der unteren Band (konservativer)
    entry_level = lower * entry_threshold
    
    # Exit-Level: Mittel-Band
    exit_level = middle
    
    # Signale initialisieren
    signals = pd.Series(0, index=df.index, dtype=int)
    
    # Entry: Preis kreuzt entry_level von oben nach unten
    cross_entry = (df['close'].shift(1) > entry_level.shift(1)) & (df['close'] <= entry_level)
    signals[cross_entry] = 1
    
    # Exit: Preis kreuzt exit_level von unten nach oben
    cross_exit = (df['close'].shift(1) < exit_level.shift(1)) & (df['close'] >= exit_level)
    signals[cross_exit] = -1
    
    return signals


def add_bollinger_indicators(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    """Fügt Bollinger Bands zum DataFrame hinzu."""
    df = df.copy()
    
    bb_period = params.get('bb_period', 20)
    bb_std = params.get('bb_std', 2.0)
    
    upper, middle, lower = calculate_bollinger_bands(
        df['close'],
        period=bb_period,
        num_std=bb_std
    )
    
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower
    
    # Bandwidth (Volatilitäts-Indikator)
    df['bb_width'] = (upper - lower) / middle
    
    # %B (Position innerhalb der Bands)
    df['bb_percent'] = (df['close'] - lower) / (upper - lower)
    
    return df


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
Bollinger Bands Mean-Reversion
================================
BB-Periode:        {params.get('bb_period', 20)} Bars
Standard-Abw.:     {params.get('bb_std', 2.0)} σ
Entry-Threshold:   {params.get('entry_threshold', 0.95):.0%} untere Band
Exit-Threshold:    Mittel-Band
Stop-Loss:         {params.get('stop_pct', 0.03):.1%}

Konzept:
- Entry wenn Preis überverkauft (untere Band)
- Exit bei Mean-Reversion (Mittel-Band)
"""
