# src/regime/base.py
"""
Peak_Trade Regime Detection & Strategy Switching - Base Types (Phase 28)
========================================================================

Definiert die Core-Typen und Protokolle fuer den Regime-Layer:

- RegimeLabel: Literaltyp fuer Marktphasen
- RegimeContext: Kontext fuer einzelne Bar-Regime-Entscheidungen
- RegimeDetector: Protokoll fuer Regime-Erkennung (einzelne Bar)
- RegimeSeriesDetector: Protokoll fuer Regime-Erkennung (ganze Serie)
- StrategySwitchDecision: Ergebnis einer Switching-Entscheidung
- StrategySwitchingPolicy: Protokoll fuer Strategy Switching
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Literal, Dict, List, Any, Optional, runtime_checkable

import pandas as pd

# ============================================================================
# REGIME LABELS
# ============================================================================

RegimeLabel = Literal["breakout", "ranging", "trending", "unknown"]
"""
Regime-Labels fuer Marktphasen:

- breakout: Hohe Volatilitaet, starke Moves, Range-Ausbrueche
- ranging: Seitwaerts, geringe Volatilitaet, Mean-Reversion-tauglich
- trending: Starke Trendphasen (positiv oder negativ)
- unknown: Unbestimmtes Regime (z.B. bei zu wenig Historie)
"""


# ============================================================================
# REGIME CONTEXT
# ============================================================================


@dataclass
class RegimeContext:
    """
    Kontext fuer eine einzelne Regime-Entscheidung.

    Wird an den RegimeDetector uebergeben, um das aktuelle Regime
    zu bestimmen. Enthaelt alle relevanten Informationen fuer die
    Regime-Erkennung.

    Attributes:
        timestamp: Aktueller Zeitstempel
        window: Lokaler Ausschnitt der OHLCV-Daten (letzte N Bars)
        symbol: Optional: Trading-Symbol (z.B. "BTC/EUR")
        features: Optional: Vorab berechnete Features (ATR, RSI, etc.)

    Example:
        >>> context = RegimeContext(
        ...     timestamp=pd.Timestamp("2024-01-15"),
        ...     window=df.tail(50),
        ...     symbol="BTC/EUR",
        ...     features={"atr": 1500.0, "volatility_rank": 0.75},
        ... )
    """

    timestamp: pd.Timestamp
    window: pd.DataFrame
    symbol: Optional[str] = None
    features: Optional[Dict[str, Any]] = None


# ============================================================================
# REGIME DETECTOR PROTOCOLS
# ============================================================================


@runtime_checkable
class RegimeDetector(Protocol):
    """
    Protokoll fuer Regime-Erkennung (einzelne Bar/Kontext).

    Implementierungen muessen detect_regime() bereitstellen,
    das ein einzelnes RegimeLabel zurueckgibt.

    Example:
        >>> class MyDetector:
        ...     def detect_regime(self, context: RegimeContext) -> RegimeLabel:
        ...         if context.features["volatility"] > 0.8:
        ...             return "breakout"
        ...         return "ranging"
    """

    def detect_regime(self, context: RegimeContext) -> RegimeLabel:
        """
        Erkennt das Regime fuer einen einzelnen Zeitpunkt.

        Args:
            context: RegimeContext mit aktuellen Daten

        Returns:
            RegimeLabel ("breakout", "ranging", "trending", "unknown")
        """
        ...


@runtime_checkable
class RegimeSeriesDetector(Protocol):
    """
    Protokoll fuer Regime-Erkennung ueber eine komplette Serie.

    Effizienter als Einzelaufruf von detect_regime() fuer jeden Zeitpunkt,
    da die gesamte Serie vektorisiert verarbeitet werden kann.

    Example:
        >>> class MySeriesDetector:
        ...     def detect_regimes(self, df: pd.DataFrame) -> pd.Series:
        ...         regimes = pd.Series("unknown", index=df.index)
        ...         # Vektorisierte Berechnung
        ...         high_vol = df["atr"] > df["atr"].quantile(0.8)
        ...         regimes[high_vol] = "breakout"
        ...         return regimes
    """

    def detect_regimes(self, df: pd.DataFrame) -> pd.Series:
        """
        Erkennt Regime fuer eine komplette OHLCV-Serie.

        Args:
            df: OHLCV-DataFrame mit DatetimeIndex

        Returns:
            pd.Series mit RegimeLabels (Index = df.index)
        """
        ...


# ============================================================================
# STRATEGY SWITCHING
# ============================================================================


@dataclass
class StrategySwitchDecision:
    """
    Ergebnis einer Strategy-Switching-Entscheidung.

    Enthaelt die Liste der aktiven Strategien und optionale Gewichte
    fuer die Kombination mehrerer Strategien.

    Attributes:
        regime: Das aktuelle Regime-Label
        active_strategies: Liste von Strategy-Namen (STRATEGY_REGISTRY-Keys)
        weights: Optional: Gewichte je Strategie (Summe = 1.0)
        metadata: Optional: Zusaetzliche Informationen

    Example:
        >>> decision = StrategySwitchDecision(
        ...     regime="ranging",
        ...     active_strategies=["mean_reversion_channel", "rsi_reversion"],
        ...     weights={"mean_reversion_channel": 0.6, "rsi_reversion": 0.4},
        ... )
    """

    regime: RegimeLabel
    active_strategies: List[str]
    weights: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def get_weight(self, strategy_name: str) -> float:
        """
        Gibt das Gewicht fuer eine Strategie zurueck.

        Falls keine Gewichte definiert sind, wird Gleichverteilung angenommen.

        Args:
            strategy_name: Name der Strategie

        Returns:
            Gewicht (0.0 bis 1.0)
        """
        if self.weights is None:
            # Gleichverteilung
            n = len(self.active_strategies)
            return 1.0 / n if n > 0 else 0.0

        return self.weights.get(strategy_name, 0.0)

    @property
    def is_single_strategy(self) -> bool:
        """True wenn nur eine Strategie aktiv ist."""
        return len(self.active_strategies) == 1

    @property
    def primary_strategy(self) -> Optional[str]:
        """Gibt die primaere (erste/gewichtigste) Strategie zurueck."""
        if not self.active_strategies:
            return None

        if self.weights:
            # Strategie mit hoechstem Gewicht
            return max(self.active_strategies, key=lambda s: self.weights.get(s, 0.0))

        return self.active_strategies[0]


@runtime_checkable
class StrategySwitchingPolicy(Protocol):
    """
    Protokoll fuer Strategy-Switching-Logik.

    Mappt ein Regime-Label auf eine oder mehrere aktive Strategien.

    Example:
        >>> class MyPolicy:
        ...     def decide(
        ...         self,
        ...         regime: RegimeLabel,
        ...         available_strategies: List[str],
        ...     ) -> StrategySwitchDecision:
        ...         if regime == "breakout":
        ...             return StrategySwitchDecision(
        ...                 regime=regime,
        ...                 active_strategies=["vol_breakout"],
        ...             )
        ...         return StrategySwitchDecision(
        ...             regime=regime,
        ...             active_strategies=available_strategies,
        ...         )
    """

    def decide(
        self,
        regime: RegimeLabel,
        available_strategies: List[str],
    ) -> StrategySwitchDecision:
        """
        Entscheidet, welche Strategien fuer ein Regime aktiv sein sollen.

        Args:
            regime: Aktuelles Regime-Label
            available_strategies: Liste aller verfuegbaren Strategy-Namen

        Returns:
            StrategySwitchDecision mit aktiven Strategien und Gewichten
        """
        ...
