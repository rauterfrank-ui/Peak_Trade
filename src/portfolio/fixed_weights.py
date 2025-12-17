# src/portfolio/fixed_weights.py
"""
Fixed Weights Portfolio Strategy (Phase 26)
===========================================

Portfolio-Strategie mit festen, vordefinierten Gewichten aus der Config.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .base import BasePortfolioStrategy, PortfolioContext

if TYPE_CHECKING:
    from .config import PortfolioConfig

logger = logging.getLogger(__name__)


class FixedWeightsPortfolioStrategy(BasePortfolioStrategy):
    """
    Fixed-Weights Portfolio-Strategie.

    Verwendet vordefinierte Gewichte aus der Config (portfolio.fixed_weights).
    Symbole ohne definiertes Gewicht werden ignoriert.

    Regeln:
    - Gewichte werden aus Config geladen
    - Nur Symbole mit definierten Gewichten UND im aktuellen Context
    - Gewichte werden normalisiert falls Summe != 1

    Config-Beispiel (config.toml):
        [portfolio]
        enabled = true
        name = "fixed_weights"

        [portfolio.fixed_weights]
        "BTC/EUR" = 0.5
        "ETH/EUR" = 0.3
        "LTC/EUR" = 0.2

    Example:
        >>> from src.portfolio.config import PortfolioConfig
        >>> from src.portfolio.base import PortfolioContext
        >>> import pandas as pd
        >>>
        >>> config = PortfolioConfig(
        ...     enabled=True,
        ...     name="fixed_weights",
        ...     fixed_weights={"BTC/EUR": 0.6, "ETH/EUR": 0.4}
        ... )
        >>> strategy = FixedWeightsPortfolioStrategy(config)
        >>>
        >>> context = PortfolioContext(
        ...     timestamp=pd.Timestamp.now(),
        ...     symbols=["BTC/EUR", "ETH/EUR"],
        ...     prices={"BTC/EUR": 50000, "ETH/EUR": 3000},
        ...     current_positions={"BTC/EUR": 0, "ETH/EUR": 0},
        ... )
        >>> weights = strategy.generate_target_weights(context)
        >>> # weights = {"BTC/EUR": 0.6, "ETH/EUR": 0.4}
    """

    def __init__(self, config: PortfolioConfig) -> None:
        """
        Initialisiert Fixed-Weights-Strategie.

        Args:
            config: PortfolioConfig-Instanz

        Raises:
            ValueError: Wenn fixed_weights leer oder nicht gesetzt
        """
        super().__init__(config)
        self.name = "FixedWeightsPortfolioStrategy"

        # Validiere dass fixed_weights existiert
        if not config.fixed_weights:
            logger.warning(
                f"{self.name}: Keine fixed_weights in Config definiert, "
                "fallback auf Equal-Weight"
            )
            self._use_fallback = True
        else:
            self._use_fallback = False
            self._fixed_weights = config.fixed_weights.copy()

            # Log die konfigurierten Gewichte
            logger.info(
                f"{self.name}: Konfigurierte Gewichte: {self._fixed_weights}"
            )

    def _compute_raw_weights(
        self, context: PortfolioContext
    ) -> dict[str, float]:
        """
        Gibt feste Gewichte für verfügbare Symbole zurück.

        Args:
            context: PortfolioContext

        Returns:
            Dict mit festen Gewichten (nur für Symbole im Context)
        """
        # Fallback auf Equal-Weight
        if self._use_fallback:
            universe = self.get_universe(context)
            if not universe:
                return {}
            n = len(universe)
            return {symbol: 1.0 / n for symbol in universe}

        # Universe bestimmen (Intersection von Config und Context)
        universe = self.get_universe(context)

        # Nur Symbole mit definierten Gewichten UND im Universe
        weights = {}
        for symbol in universe:
            if symbol in self._fixed_weights:
                weights[symbol] = self._fixed_weights[symbol]
            else:
                logger.debug(
                    f"{self.name}: {symbol} hat kein definiertes Gewicht, ignoriere"
                )

        if not weights:
            logger.warning(
                f"{self.name}: Keine Symbole mit definierten Gewichten gefunden"
            )
            return {}

        # Log wenn nicht alle Config-Symbole im Context sind
        missing = set(self._fixed_weights.keys()) - set(universe)
        if missing:
            logger.debug(
                f"{self.name}: Symbole aus Config nicht im Context: {missing}"
            )

        return weights
