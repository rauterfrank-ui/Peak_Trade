"""
Peak_Trade MACD Strategy
=========================
MACD (Moving Average Convergence Divergence) Trend-Following.

Konzept:
- MACD Line = EMA(12) - EMA(26)
- Signal Line = EMA(9) von MACD Line
- Histogram = MACD Line - Signal Line
- Entry: MACD kreuzt Signal von unten
- Exit: MACD kreuzt Signal von oben
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any, Dict, Optional, Tuple

from .base import BaseStrategy, StrategyMetadata


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _calculate_macd(
    prices: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Berechnet MACD-Indikatoren (interne Helper-Funktion).

    Args:
        prices: Close-Preise
        fast_period: Schnelle EMA
        slow_period: Langsame EMA
        signal_period: Signal-Linie EMA

    Returns:
        (macd_line, signal_line, histogram)
    """
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


# ============================================================================
# OOP STRATEGIE-KLASSE
# ============================================================================


class MACDStrategy(BaseStrategy):
    """
    MACD Trend-Following-Strategie (OOP-Version).

    Signale:
    - 1 (long): MACD kreuzt Signal-Linie von unten
    - -1 (exit): MACD kreuzt Signal-Linie von oben
    - 0: Kein Signal

    Args:
        fast_ema: Schnelle EMA-Periode (default: 12)
        slow_ema: Langsame EMA-Periode (default: 26)
        signal_ema: Signal-Linie EMA-Periode (default: 9)
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = MACDStrategy(fast_ema=12, slow_ema=26, signal_ema=9)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = MACDStrategy.from_config(config, "strategy.macd")
    """

    KEY = "macd"

    def __init__(
        self,
        fast_ema: int = 12,
        slow_ema: int = 26,
        signal_ema: int = 9,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert MACD-Strategie.

        Args:
            fast_ema: Schnelle EMA-Periode
            slow_ema: Langsame EMA-Periode
            signal_ema: Signal-Linie EMA-Periode
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "fast_ema": fast_ema,
            "slow_ema": slow_ema,
            "signal_ema": signal_ema,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="MACD",
                description="MACD Trend-Following-Strategie",
                version="1.0.0",
                author="Peak_Trade",
                regime="trending",
                tags=["trend", "momentum", "macd"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.fast_ema = self.config.get("fast_ema", fast_ema)
        self.slow_ema = self.config.get("slow_ema", slow_ema)
        self.signal_ema = self.config.get("signal_ema", signal_ema)

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.fast_ema <= 0:
            raise ValueError(f"fast_ema ({self.fast_ema}) muss > 0 sein")
        if self.slow_ema <= 0:
            raise ValueError(f"slow_ema ({self.slow_ema}) muss > 0 sein")
        if self.signal_ema <= 0:
            raise ValueError(f"signal_ema ({self.signal_ema}) muss > 0 sein")
        if self.fast_ema >= self.slow_ema:
            raise ValueError(f"fast_ema ({self.fast_ema}) muss < slow_ema ({self.slow_ema}) sein")

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.macd",
    ) -> "MACDStrategy":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            MACDStrategy-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> config = load_config()
            >>> strategy = MACDStrategy.from_config(config)
        """
        fast = cfg.get(f"{section}.fast_ema", 12)
        slow = cfg.get(f"{section}.slow_ema", 26)
        signal = cfg.get(f"{section}.signal_ema", 9)

        return cls(
            fast_ema=fast,
            slow_ema=slow,
            signal_ema=signal,
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
            raise ValueError(f"Spalte 'close' nicht in DataFrame. Verfügbar: {list(data.columns)}")

        if len(data) < self.slow_ema:
            raise ValueError(f"Brauche mind. {self.slow_ema} Bars, habe nur {len(data)}")

        # MACD berechnen
        macd_line, signal_line, _ = _calculate_macd(
            data["close"],
            fast_period=self.fast_ema,
            slow_period=self.slow_ema,
            signal_period=self.signal_ema,
        )

        # Signale initialisieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Bullish Crossover: MACD kreuzt Signal von unten
        cross_up = (macd_line.shift(1) < signal_line.shift(1)) & (macd_line > signal_line)
        signals[cross_up] = 1

        # Bearish Crossover: MACD kreuzt Signal von oben
        cross_down = (macd_line.shift(1) > signal_line.shift(1)) & (macd_line < signal_line)
        signals[cross_down] = -1

        return signals


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================
# NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (Eintrag "Legacy-API Cleanup: macd.py")
# Legacy-Funktion für Backwards Compatibility. Sollte entfernt werden, sobald
# alle Pipelines auf MACDStrategy (OOP) umgestellt sind.


def calculate_macd(
    prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Berechnet MACD-Indikatoren.

    Args:
        prices: Close-Preise
        fast_period: Schnelle EMA
        slow_period: Langsame EMA
        signal_period: Signal-Linie EMA

    Returns:
        (macd_line, signal_line, histogram)
    """
    # EMAs berechnen
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

    # MACD Line = Fast EMA - Slow EMA
    macd_line = ema_fast - ema_slow

    # Signal Line = EMA der MACD Line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Histogram = Differenz
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Generiert MACD-basierte Signale.

    Args:
        df: OHLCV-DataFrame
        params: Dict mit 'fast_ema', 'slow_ema', 'signal_ema'

    Returns:
        Series mit Signalen (1 = Long, 0 = Neutral, -1 = Exit)
    """
    # Parameter
    fast = params.get("fast_ema", 12)
    slow = params.get("slow_ema", 26)
    signal = params.get("signal_ema", 9)

    # MACD berechnen
    macd_line, signal_line, histogram = calculate_macd(
        df["close"], fast_period=fast, slow_period=slow, signal_period=signal
    )

    # Signale initialisieren
    signals = pd.Series(0, index=df.index, dtype=int)

    # Bullish Crossover: MACD kreuzt Signal von unten
    cross_up = (macd_line.shift(1) < signal_line.shift(1)) & (macd_line > signal_line)
    signals[cross_up] = 1

    # Bearish Crossover: MACD kreuzt Signal von oben
    cross_down = (macd_line.shift(1) > signal_line.shift(1)) & (macd_line < signal_line)
    signals[cross_down] = -1

    return signals


def add_macd_indicators(df: pd.DataFrame, params: Dict) -> pd.DataFrame:
    """Fügt MACD-Indikatoren zum DataFrame hinzu."""
    df = df.copy()

    fast = params.get("fast_ema", 12)
    slow = params.get("slow_ema", 26)
    signal = params.get("signal_ema", 9)

    macd_line, signal_line, histogram = calculate_macd(
        df["close"], fast_period=fast, slow_period=slow, signal_period=signal
    )

    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_histogram"] = histogram

    return df


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
MACD Trend-Following
=====================
Fast EMA:          {params.get("fast_ema", 12)}
Slow EMA:          {params.get("slow_ema", 26)}
Signal EMA:        {params.get("signal_ema", 9)}
Stop-Loss:         {params.get("stop_pct", 0.025):.1%}

Konzept:
- Entry: MACD kreuzt Signal-Linie von unten (Bullish)
- Exit: MACD kreuzt Signal-Linie von oben (Bearish)
"""
