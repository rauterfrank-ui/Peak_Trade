"""
MA-Crossover-Strategie: OOP-Version mit BaseStrategy
=====================================================
Klassische Moving-Average-Crossover-Strategie:
- Long Entry: Fast MA kreuzt über Slow MA
- Exit: Fast MA kreuzt unter Slow MA
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


class MACrossoverStrategy(BaseStrategy):
    """
    Moving Average Crossover Strategy.

    Signale:
    - 1 (long): Fast MA > Slow MA (nach Crossover)
    - 0 (flat): Fast MA < Slow MA

    Args:
        fast_window: Periode für schnelle MA (default: 20)
        slow_window: Periode für langsame MA (default: 50)
        price_col: Spalte für Preisdaten (default: "close")
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = MACrossoverStrategy(fast_window=10, slow_window=30)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = MACrossoverStrategy.from_config(config, "strategy.ma_crossover")
    """

    KEY = "ma_crossover"

    def __init__(
        self,
        fast_window: int = 20,
        slow_window: int = 50,
        price_col: str = "close",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert MA-Crossover-Strategie.

        Args:
            fast_window: Schnelle MA-Periode
            slow_window: Langsame MA-Periode
            price_col: Preis-Spalte
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "fast_window": fast_window,
            "slow_window": slow_window,
            "price_col": price_col,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="MA-Crossover",
                description="Moving Average Crossover Strategy",
                version="1.0.0",
                author="Peak_Trade",
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren und validieren
        self.fast_window = self.config.get("fast_window", fast_window)
        self.slow_window = self.config.get("slow_window", slow_window)
        self.price_col = self.config.get("price_col", price_col)

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.fast_window >= self.slow_window:
            raise ValueError(
                f"fast_window ({self.fast_window}) muss < slow_window ({self.slow_window}) sein"
            )
        if self.fast_window < 2 or self.slow_window < 2:
            raise ValueError("MA-Perioden müssen >= 2 sein")

    @classmethod
    def from_config(
        cls,
        cfg: "PeakConfigLike",
        section: str = "strategy.ma_crossover",
    ) -> MACrossoverStrategy:
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            MACrossoverStrategy-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> config = load_config()
            >>> strategy = MACrossoverStrategy.from_config(config)
        """
        fast = cfg.get(f"{section}.fast_window", 20)
        slow = cfg.get(f"{section}.slow_window", 50)
        price = cfg.get(f"{section}.price_col", "close")
        return cls(fast_window=fast, slow_window=slow, price_col=price)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens self.price_col)

        Returns:
            Series mit Signalen (1=long, 0=flat, Index=data.index)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        # Validierung
        if self.price_col not in data.columns:
            raise ValueError(
                f"Spalte '{self.price_col}' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        if len(data) < self.slow_window:
            raise ValueError(
                f"Brauche mind. {self.slow_window} Bars, habe nur {len(data)}"
            )

        # Kopie für Berechnungen
        df = data.copy()

        # MAs berechnen
        df["fast_ma"] = df[self.price_col].rolling(
            self.fast_window, min_periods=self.fast_window
        ).mean()
        df["slow_ma"] = df[self.price_col].rolling(
            self.slow_window, min_periods=self.slow_window
        ).mean()

        # Crossover-Logik
        ma_diff = df["fast_ma"] - df["slow_ma"]
        cross_up = (ma_diff > 0) & (ma_diff.shift(1) <= 0)
        cross_down = (ma_diff < 0) & (ma_diff.shift(1) >= 0)

        # Event-Signale
        events = pd.Series(0, index=df.index, dtype=int)
        events[cross_up] = 1
        events[cross_down] = -1

        # Event → State (1=long, 0=flat)
        # -1 = Exit → 0
        state = events.replace({-1: 0})

        # Initiale Nullen nicht wegfüllen, nur "im Trade bleiben"
        # Fix für Pandas FutureWarning: verwende mask + ffill statt replace(0, NA)
        mask = state == 0
        state = state.where(~mask, other=pd.NA)
        state = state.ffill()
        # Explizit als int casten nach fillna(0) um Downcasting-Warning zu vermeiden
        state = state.fillna(0).astype(int)

        return state


# ============================================================================
# TYPE HINTS
# ============================================================================

class PeakConfigLike:
    """Typ-Hint für Config-Objekte (vermeidet Zirkularimporte)."""
    def get(self, path: str, default: Any = None) -> Any:  # pragma: no cover
        ...


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================

def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte MACrossoverStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict mit fast_period, slow_period

    Returns:
        Signal-Series (1=long, 0=flat)

    Example:
        >>> signals = generate_signals(df, {"fast_period": 10, "slow_period": 30})
    """
    # Alte Parameter-Namen auf neue mappen
    config = {
        "fast_window": params.get("fast_period", params.get("fast_window", 10)),
        "slow_window": params.get("slow_period", params.get("slow_window", 30)),
        "price_col": params.get("price_col", "close"),
    }

    # Strategie-Instanz erstellen und Signale generieren
    strategy = MACrossoverStrategy(config=config)
    return strategy.generate_signals(df)
