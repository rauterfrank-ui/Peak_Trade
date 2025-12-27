# src/portfolio/vol_target.py
"""
Volatility Target Portfolio Strategy (Phase 26)
===============================================

Portfolio-Strategie basierend auf Inverse-Volatilität-Gewichtung.

Symbole mit niedriger Volatilität erhalten höhere Gewichte,
um das Risiko gleichmäßiger zu verteilen (Risk-Parity-Ansatz).
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, TYPE_CHECKING

import numpy as np
import pandas as pd

from .base import BasePortfolioStrategy, PortfolioContext

if TYPE_CHECKING:
    from .config import PortfolioConfig

logger = logging.getLogger(__name__)


class VolTargetPortfolioStrategy(BasePortfolioStrategy):
    """
    Volatility-Target Portfolio-Strategie (Inverse-Vol-Weighting).

    Berechnet Gewichte basierend auf der inversen realisierten Volatilität:
    - w_i ~ 1 / vol_i
    - Symbole mit niedriger Vol bekommen höhere Gewichte
    - Optional: Skalierung auf eine Ziel-Volatilität

    Dies ist ein einfacher Risk-Parity-Ansatz.

    Regeln:
    - Benötigt historische Returns (returns_history im Context)
    - Fallback auf Volatilitäten aus Context falls verfügbar
    - Fallback auf Equal-Weight falls keine Vol-Daten

    Example:
        >>> from src.portfolio.config import PortfolioConfig
        >>> from src.portfolio.base import PortfolioContext
        >>> import pandas as pd
        >>> import numpy as np
        >>>
        >>> config = PortfolioConfig(
        ...     enabled=True,
        ...     name="vol_target",
        ...     vol_lookback=20,
        ...     vol_target=0.15,  # 15% annualisierte Vol
        ... )
        >>> strategy = VolTargetPortfolioStrategy(config)
        >>>
        >>> # Beispiel: BTC hat höhere Vol als ETH
        >>> returns = pd.DataFrame({
        ...     "BTC/EUR": np.random.normal(0, 0.03, 100),  # ~3% daily vol
        ...     "ETH/EUR": np.random.normal(0, 0.02, 100),  # ~2% daily vol
        ... })
        >>>
        >>> context = PortfolioContext(
        ...     timestamp=pd.Timestamp.now(),
        ...     symbols=["BTC/EUR", "ETH/EUR"],
        ...     prices={"BTC/EUR": 50000, "ETH/EUR": 3000},
        ...     current_positions={"BTC/EUR": 0, "ETH/EUR": 0},
        ...     returns_history=returns,
        ... )
        >>> weights = strategy.generate_target_weights(context)
        >>> # ETH bekommt höheres Gewicht wegen niedrigerer Vol
    """

    def __init__(self, config: "PortfolioConfig") -> None:
        """
        Initialisiert Vol-Target-Strategie.

        Args:
            config: PortfolioConfig-Instanz
        """
        super().__init__(config)
        self.name = "VolTargetPortfolioStrategy"

        self.vol_lookback = config.vol_lookback
        self.vol_target = config.vol_target

        # Annualisierungsfaktor (Annahme: Daily Data, 252 Trading Days)
        self.annualization_factor = np.sqrt(252)

        logger.info(
            f"{self.name}: vol_lookback={self.vol_lookback}, vol_target={self.vol_target:.1%}"
        )

    def _compute_raw_weights(self, context: PortfolioContext) -> Dict[str, float]:
        """
        Berechnet inverse-volatilitäts-gewichtete Gewichte.

        Args:
            context: PortfolioContext

        Returns:
            Dict mit Vol-basierten Gewichten
        """
        universe = self.get_universe(context)

        if not universe:
            logger.warning(f"{self.name}: Leeres Universe")
            return {}

        # Volatilitäten berechnen
        volatilities = self._compute_volatilities(context, universe)

        if not volatilities:
            logger.warning(f"{self.name}: Keine Volatilitäten verfügbar, fallback auf Equal-Weight")
            n = len(universe)
            return {symbol: 1.0 / n for symbol in universe}

        # Inverse-Vol-Gewichte berechnen
        weights = self._inverse_vol_weights(volatilities)

        return weights

    def _compute_volatilities(
        self,
        context: PortfolioContext,
        universe: list[str],
    ) -> Dict[str, float]:
        """
        Berechnet Volatilitäten für alle Symbole.

        Priorität:
        1. Berechnung aus returns_history (falls vorhanden)
        2. Volatilitäten aus Context (falls vorhanden)
        3. Leeres Dict (führt zu Fallback)

        Args:
            context: PortfolioContext
            universe: Liste der zu berechnenden Symbole

        Returns:
            Dict[symbol -> volatility]
        """
        volatilities = {}

        # Option 1: Berechnung aus Returns-History
        if context.returns_history is not None and not context.returns_history.empty:
            returns_df = context.returns_history

            for symbol in universe:
                if symbol not in returns_df.columns:
                    logger.debug(f"{self.name}: {symbol} nicht in returns_history")
                    continue

                # Rolling Volatility berechnen
                symbol_returns = returns_df[symbol].dropna()

                if len(symbol_returns) < self.vol_lookback:
                    logger.debug(
                        f"{self.name}: {symbol} hat nur {len(symbol_returns)} "
                        f"Returns, brauche {self.vol_lookback}"
                    )
                    continue

                # Letzten vol_lookback Returns nehmen
                recent_returns = symbol_returns.iloc[-self.vol_lookback :]
                daily_vol = recent_returns.std()

                # Annualisieren
                annual_vol = daily_vol * self.annualization_factor

                if annual_vol > 0:
                    volatilities[symbol] = annual_vol

            if volatilities:
                logger.debug(f"{self.name}: Berechnete Volatilitäten: {volatilities}")
                return volatilities

        # Option 2: Volatilitäten aus Context
        if context.volatilities:
            for symbol in universe:
                if symbol in context.volatilities:
                    volatilities[symbol] = context.volatilities[symbol]

            if volatilities:
                logger.debug(f"{self.name}: Volatilitäten aus Context: {volatilities}")
                return volatilities

        return {}

    def _inverse_vol_weights(self, volatilities: Dict[str, float]) -> Dict[str, float]:
        """
        Berechnet Inverse-Volatilitäts-Gewichte.

        w_i = (1 / vol_i) / sum(1 / vol_j)

        Args:
            volatilities: Dict[symbol -> volatility]

        Returns:
            Dict mit normalisierten Inverse-Vol-Gewichten
        """
        if not volatilities:
            return {}

        # Inverse Volatilitäten
        inv_vols = {}
        for symbol, vol in volatilities.items():
            if vol > 0:
                inv_vols[symbol] = 1.0 / vol
            else:
                logger.warning(f"{self.name}: {symbol} hat Vol=0, überspringe")

        if not inv_vols:
            return {}

        # Normalisieren (Summe = 1)
        total_inv_vol = sum(inv_vols.values())
        weights = {symbol: inv_vol / total_inv_vol for symbol, inv_vol in inv_vols.items()}

        # Optional: Skalierung auf Ziel-Volatilität
        # (Für jetzt nur Inverse-Vol-Weighting ohne Leverage-Adjustment)

        logger.debug(f"{self.name}: Inverse-Vol-Gewichte: {weights}")

        return weights

    def compute_portfolio_vol(
        self,
        weights: Dict[str, float],
        volatilities: Dict[str, float],
        correlation_matrix: Optional[pd.DataFrame] = None,
    ) -> float:
        """
        Berechnet die erwartete Portfolio-Volatilität.

        Vereinfachte Formel (ohne Korrelationen):
        portfolio_vol ≈ sqrt(sum(w_i^2 * vol_i^2))

        Mit Korrelationsmatrix:
        portfolio_vol = sqrt(w' * Σ * w)

        Args:
            weights: Gewichte
            volatilities: Volatilitäten
            correlation_matrix: Optional Korrelationsmatrix

        Returns:
            Geschätzte Portfolio-Volatilität (annualisiert)
        """
        symbols = list(weights.keys())

        if correlation_matrix is not None:
            # Vollständige Berechnung mit Korrelationen
            n = len(symbols)
            w = np.array([weights[s] for s in symbols])
            vols = np.array([volatilities.get(s, 0) for s in symbols])

            # Kovarianzmatrix approximieren
            # cov_ij = vol_i * vol_j * corr_ij
            cov_matrix = np.zeros((n, n))
            for i, si in enumerate(symbols):
                for j, sj in enumerate(symbols):
                    if si in correlation_matrix.index and sj in correlation_matrix.columns:
                        corr = correlation_matrix.loc[si, sj]
                    else:
                        corr = 1.0 if i == j else 0.0
                    cov_matrix[i, j] = vols[i] * vols[j] * corr

            portfolio_var = w @ cov_matrix @ w
            return np.sqrt(portfolio_var)

        else:
            # Vereinfachte Berechnung (Annahme: unkorreliert)
            portfolio_var = sum(
                weights.get(s, 0) ** 2 * volatilities.get(s, 0) ** 2 for s in symbols
            )
            return np.sqrt(portfolio_var)
