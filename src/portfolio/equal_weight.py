# src/portfolio/equal_weight.py
"""
Equal Weight Portfolio Strategy (Phase 26)
==========================================

Portfolio-Strategie, die alle Symbole im Universe gleichgewichtet.

Dies ist die einfachste Portfolio-Strategie und dient als Baseline.
"""

from __future__ import annotations

import logging
from typing import Dict, TYPE_CHECKING

from .base import BasePortfolioStrategy, PortfolioContext

if TYPE_CHECKING:
    from .config import PortfolioConfig

logger = logging.getLogger(__name__)


class EqualWeightPortfolioStrategy(BasePortfolioStrategy):
    """
    Equal-Weight Portfolio-Strategie.

    Verteilt das Kapital gleichmäßig auf alle Symbole im Universe.
    Jedes Symbol erhält ein Gewicht von 1/n.

    Regeln:
    - Long-only (alle Gewichte >= 0)
    - Nur Symbole aus dem aktiven Universe
    - Gewichte summieren zu 1.0

    Example:
        >>> from src.portfolio.config import PortfolioConfig
        >>> from src.portfolio.base import PortfolioContext
        >>> import pandas as pd
        >>>
        >>> config = PortfolioConfig(enabled=True, name="equal_weight")
        >>> strategy = EqualWeightPortfolioStrategy(config)
        >>>
        >>> context = PortfolioContext(
        ...     timestamp=pd.Timestamp.now(),
        ...     symbols=["BTC/EUR", "ETH/EUR", "LTC/EUR"],
        ...     prices={"BTC/EUR": 50000, "ETH/EUR": 3000, "LTC/EUR": 100},
        ...     current_positions={"BTC/EUR": 0, "ETH/EUR": 0, "LTC/EUR": 0},
        ... )
        >>> weights = strategy.generate_target_weights(context)
        >>> # weights ≈ {"BTC/EUR": 0.333, "ETH/EUR": 0.333, "LTC/EUR": 0.333}
    """

    def __init__(self, config: "PortfolioConfig") -> None:
        """
        Initialisiert Equal-Weight-Strategie.

        Args:
            config: PortfolioConfig-Instanz
        """
        super().__init__(config)
        self.name = "EqualWeightPortfolioStrategy"

    def _compute_raw_weights(self, context: PortfolioContext) -> Dict[str, float]:
        """
        Berechnet gleichverteilte Gewichte.

        Args:
            context: PortfolioContext

        Returns:
            Dict mit Gewicht 1/n für jedes Symbol
        """
        # Universe bestimmen
        universe = self.get_universe(context)

        if not universe:
            logger.warning(f"{self.name}: Leeres Universe, keine Gewichte berechnet")
            return {}

        n = len(universe)
        weight = 1.0 / n

        weights = {symbol: weight for symbol in universe}

        logger.debug(f"{self.name}: Equal weights für {n} Symbole: {weight:.4f} pro Symbol")

        return weights
