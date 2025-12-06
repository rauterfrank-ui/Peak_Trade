# src/portfolio/__init__.py
"""
Peak_Trade Portfolio Module (Phase 26)
======================================

Multi-Strategy Portfolio-Management und Portfolio-Strategie-Layer.

Dieses Package enthält:

1. **PortfolioManager** (manager.py):
   - Orchestriert mehrere Single-Strategien
   - Capital Allocation & Equity-Kombination

2. **Portfolio-Strategy-Layer** (Phase 26):
   - PortfolioContext: Datenklasse für Portfolio-Entscheidungen
   - PortfolioStrategy: Protocol/Interface für Portfolio-Strategien
   - BasePortfolioStrategy: Abstrakte Basisklasse

   Verfügbare Portfolio-Strategien:
   - EqualWeightPortfolioStrategy: Gleichverteilung über alle Symbole
   - FixedWeightsPortfolioStrategy: Feste Gewichte aus Config
   - VolTargetPortfolioStrategy: Inverse-Volatilität-Gewichtung

Usage:
    >>> # Portfolio-Manager (bestehend)
    >>> from src.portfolio import PortfolioManager
    >>> pm = PortfolioManager()
    >>> pm.add_strategy("ma_crossover", signal_fn, params)
    >>> result = pm.run_backtest(df)
    >>>
    >>> # Portfolio-Strategy-Layer (Phase 26)
    >>> from src.portfolio import make_portfolio_strategy, PortfolioContext
    >>> from src.portfolio.config import PortfolioConfig
    >>>
    >>> config = PortfolioConfig(enabled=True, name="equal_weight")
    >>> strategy = make_portfolio_strategy(config)
    >>> weights = strategy.generate_target_weights(context)
"""

# Legacy: Portfolio Manager
from .manager import PortfolioManager, PortfolioResult

# Phase 26: Portfolio Strategy Layer
from .base import (
    PortfolioContext,
    PortfolioStrategy,
    BasePortfolioStrategy,
    make_portfolio_strategy,
)
from .config import PortfolioConfig
from .equal_weight import EqualWeightPortfolioStrategy
from .fixed_weights import FixedWeightsPortfolioStrategy
from .vol_target import VolTargetPortfolioStrategy

__all__ = [
    # Legacy
    "PortfolioManager",
    "PortfolioResult",
    # Core (Phase 26)
    "PortfolioContext",
    "PortfolioStrategy",
    "BasePortfolioStrategy",
    "PortfolioConfig",
    # Factory
    "make_portfolio_strategy",
    # Strategies
    "EqualWeightPortfolioStrategy",
    "FixedWeightsPortfolioStrategy",
    "VolTargetPortfolioStrategy",
]
