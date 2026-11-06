# src/portfolio/base.py
"""
Portfolio Strategy Base Classes (Phase 26)
==========================================

Enthält die Kern-Interfaces und Basisklassen für Portfolio-Strategien.

Hauptkomponenten:
- PortfolioContext: Datenklasse mit allen Informationen für Portfolio-Entscheidungen
- PortfolioStrategy: Protocol (Interface) für alle Portfolio-Strategien
- BasePortfolioStrategy: Abstrakte Basisklasse mit Hilfsmethoden
- make_portfolio_strategy: Factory-Funktion zur Erstellung von Strategien
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .config import PortfolioConfig

logger = logging.getLogger(__name__)


@dataclass
class PortfolioContext:
    """
    Kontext-Daten für Portfolio-Entscheidungen.

    Diese Datenklasse enthält alle Informationen, die eine Portfolio-Strategie
    benötigt, um Zielgewichte zu berechnen.

    Attributes:
        timestamp: Aktueller Zeitstempel
        symbols: Liste der verfügbaren Symbole
        prices: Aktuelle Preise pro Symbol
        current_positions: Aktuelle Positionen (Stückzahl) pro Symbol
        current_weights: Aktuelle Gewichte pro Symbol (optional, berechnet)
        strategy_signals: Signale der Single-Strategien (-1, 0, +1) pro Symbol
        returns_history: Historische Returns (DataFrame mit Symbolen als Spalten)
        volatilities: Aktuelle Volatilitäten pro Symbol (optional)
        equity: Aktuelles Portfolio-Equity
        metadata: Zusätzliche Informationen
    """

    timestamp: pd.Timestamp
    symbols: List[str]
    prices: Dict[str, float]
    current_positions: Dict[str, float]
    current_weights: Optional[Dict[str, float]] = None
    strategy_signals: Optional[Dict[str, float]] = None
    returns_history: Optional[pd.DataFrame] = None
    volatilities: Optional[Dict[str, float]] = None
    equity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Berechnet abgeleitete Felder."""
        # Current Weights berechnen falls nicht gesetzt
        if self.current_weights is None and self.equity > 0:
            self.current_weights = {}
            for symbol in self.symbols:
                pos = self.current_positions.get(symbol, 0.0)
                price = self.prices.get(symbol, 0.0)
                value = pos * price
                self.current_weights[symbol] = value / self.equity if self.equity > 0 else 0.0

    def get_price(self, symbol: str) -> float:
        """Holt Preis für Symbol mit Fallback auf 0.0."""
        return self.prices.get(symbol, 0.0)

    def get_position(self, symbol: str) -> float:
        """Holt Position für Symbol mit Fallback auf 0.0."""
        return self.current_positions.get(symbol, 0.0)

    def get_signal(self, symbol: str) -> float:
        """Holt Signal für Symbol mit Fallback auf 0.0."""
        if self.strategy_signals is None:
            return 0.0
        return self.strategy_signals.get(symbol, 0.0)


class PortfolioStrategy(Protocol):
    """
    Protocol (Interface) für Portfolio-Strategien.

    Jede Portfolio-Strategie muss die Methode `generate_target_weights`
    implementieren.

    Example:
        >>> class MyPortfolioStrategy:
        ...     def generate_target_weights(
        ...         self, context: PortfolioContext
        ...     ) -> Dict[str, float]:
        ...         return {"BTC/EUR": 0.5, "ETH/EUR": 0.5}
    """

    def generate_target_weights(self, context: PortfolioContext) -> Dict[str, float]:
        """
        Generiert Zielgewichte für das Portfolio.

        Args:
            context: PortfolioContext mit aktuellen Marktdaten

        Returns:
            Dict[symbol -> weight] mit Zielgewichten.
            - Gewichte sollten in [-1.0, 1.0] liegen
            - Positive Werte = Long, negative = Short
            - Summe der positiven Gewichte sollte idealerweise ~1.0 sein
            - 0.0 bedeutet Flat (keine Position)
        """
        ...


class BasePortfolioStrategy(ABC):
    """
    Abstrakte Basisklasse für Portfolio-Strategien.

    Bietet gemeinsame Funktionalität wie Logging, Normalisierung
    und Constraint-Enforcement.

    Subklassen müssen `_compute_raw_weights` implementieren.

    Attributes:
        config: PortfolioConfig-Instanz
        name: Name der Strategie (für Logging)
    """

    def __init__(self, config: "PortfolioConfig") -> None:
        """
        Initialisiert die Portfolio-Strategie.

        Args:
            config: PortfolioConfig-Instanz
        """
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def _compute_raw_weights(self, context: PortfolioContext) -> Dict[str, float]:
        """
        Berechnet rohe (nicht-normalisierte) Gewichte.

        Muss von Subklassen implementiert werden.

        Args:
            context: PortfolioContext

        Returns:
            Dict mit rohen Gewichten
        """
        raise NotImplementedError

    def generate_target_weights(self, context: PortfolioContext) -> Dict[str, float]:
        """
        Generiert Zielgewichte mit Normalisierung und Constraints.

        Workflow:
        1. Ruft _compute_raw_weights auf
        2. Wendet Constraints an (max_single_weight, min_weight)
        3. Normalisiert auf Summe 1.0 (falls aktiviert)

        Args:
            context: PortfolioContext

        Returns:
            Dict[symbol -> weight] mit finalen Zielgewichten
        """
        # 1. Rohe Gewichte berechnen
        raw_weights = self._compute_raw_weights(context)

        if not raw_weights:
            logger.warning(f"{self.name}: Keine Gewichte berechnet, gebe leeres Dict zurück")
            return {}

        # 2. Constraints anwenden
        constrained = self._apply_constraints(raw_weights)

        # 3. Normalisieren
        if self.config.normalize_weights:
            final_weights = self._normalize_weights(constrained)
        else:
            final_weights = constrained

        logger.debug(
            f"{self.name}: Generated weights for {len(final_weights)} symbols: {final_weights}"
        )

        return final_weights

    def _apply_constraints(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Wendet Constraints auf Gewichte an.

        - max_single_weight: Kein Symbol > X%
        - min_weight: Symbole unter Minimum werden auf 0 gesetzt

        Args:
            weights: Rohe Gewichte

        Returns:
            Gewichte nach Constraint-Anwendung
        """
        constrained = {}

        for symbol, weight in weights.items():
            # Min-Weight-Check
            if abs(weight) < self.config.min_weight:
                logger.debug(
                    f"{self.name}: {symbol} weight {weight:.4f} "
                    f"< min {self.config.min_weight}, setze auf 0"
                )
                continue

            # Max-Weight-Cap
            if weight > self.config.max_single_weight:
                logger.debug(
                    f"{self.name}: {symbol} weight {weight:.4f} "
                    f"> max {self.config.max_single_weight}, cappe"
                )
                weight = self.config.max_single_weight
            elif weight < -self.config.max_single_weight:
                weight = -self.config.max_single_weight

            constrained[symbol] = weight

        return constrained

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Normalisiert Gewichte auf Summe 1.0.

        Für Long-Only-Portfolios: Summe der positiven Gewichte = 1.0
        Für Long/Short: Summe der absoluten Gewichte = 1.0 (optional)

        Args:
            weights: Constrained Gewichte

        Returns:
            Normalisierte Gewichte
        """
        if not weights:
            return {}

        # Berechne Summe der positiven Gewichte (Long-Exposure)
        long_sum = sum(w for w in weights.values() if w > 0)
        short_sum = abs(sum(w for w in weights.values() if w < 0))

        # Long-Only Normalisierung (Standard)
        if long_sum > 0:
            normalized = {}
            for symbol, weight in weights.items():
                if weight > 0:
                    normalized[symbol] = weight / long_sum
                else:
                    # Short-Gewichte werden proportional skaliert
                    normalized[symbol] = weight / long_sum if long_sum > 0 else weight
            return normalized

        # Falls nur Shorts vorhanden (ungewöhnlich)
        if short_sum > 0:
            return {s: w / short_sum for s, w in weights.items()}

        return weights

    def get_universe(self, context: PortfolioContext) -> List[str]:
        """
        Bestimmt das aktive Universe.

        Config-Symbole haben Priorität über Context-Symbole.

        Args:
            context: PortfolioContext

        Returns:
            Liste der zu berücksichtigenden Symbole
        """
        if self.config.symbols:
            # Config-Universe: Nur Symbole die auch im Context sind
            return [s for s in self.config.symbols if s in context.symbols]
        return context.symbols

    def __repr__(self) -> str:
        return f"<{self.name}(enabled={self.config.enabled}, strategy={self.config.name})>"


def make_portfolio_strategy(config: "PortfolioConfig") -> Optional[BasePortfolioStrategy]:
    """
    Factory-Funktion: Erstellt Portfolio-Strategie basierend auf Config.

    Args:
        config: PortfolioConfig-Instanz

    Returns:
        Portfolio-Strategie-Instanz oder None wenn disabled

    Raises:
        ValueError: Bei unbekannter Strategie

    Example:
        >>> from src.portfolio.config import PortfolioConfig
        >>> cfg = PortfolioConfig(enabled=True, name="equal_weight")
        >>> strategy = make_portfolio_strategy(cfg)
        >>> print(strategy)
        <EqualWeightPortfolioStrategy(...)>
    """
    if not config.enabled:
        logger.info("Portfolio-Layer ist deaktiviert")
        return None

    # Lazy imports um zirkuläre Abhängigkeiten zu vermeiden
    from .equal_weight import EqualWeightPortfolioStrategy
    from .fixed_weights import FixedWeightsPortfolioStrategy
    from .vol_target import VolTargetPortfolioStrategy

    strategy_map = {
        "equal_weight": EqualWeightPortfolioStrategy,
        "fixed_weights": FixedWeightsPortfolioStrategy,
        "vol_target": VolTargetPortfolioStrategy,
    }

    if config.name not in strategy_map:
        raise ValueError(
            f"Unbekannte Portfolio-Strategie: '{config.name}'. "
            f"Verfügbar: {list(strategy_map.keys())}"
        )

    strategy_cls = strategy_map[config.name]
    strategy = strategy_cls(config)

    logger.info(f"Portfolio-Strategie erstellt: {strategy}")

    return strategy
