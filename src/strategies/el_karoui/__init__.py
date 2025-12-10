# src/strategies/el_karoui/__init__.py
"""
El-Karoui-Strategien für Peak_Trade (Research-Track).

Diese Strategien basieren auf stochastischen Volatilitätsmodellen und
mathematischer Finanztheorie nach Nicole El Karoui und sind ausschließlich
für Research/Backtesting gedacht - NICHT für Live-Trading.

Module:
- vol_model: Volatilitäts-Modell mit Regime-Klassifikation
- el_karoui_vol_model_strategy: Vol-Regime-basierte Trading-Strategie

Tier: r_and_d (Research & Development)
Category: volatility

Siehe: docs/runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md
"""
from .vol_model import (
    VolRegime,
    ElKarouiVolConfig,
    ElKarouiVolModel,
    get_vol_regime,
    get_vol_scaling_factor,
)
from .el_karoui_vol_model_strategy import (
    ElKarouiVolatilityStrategy,
    ElKarouiVolModelStrategy,  # Alias für Backwards Compatibility
    generate_signals,
    DEFAULT_REGIME_POSITION_MAP,
    CONSERVATIVE_REGIME_POSITION_MAP,
    AGGRESSIVE_REGIME_POSITION_MAP,
)

__all__ = [
    # Vol Model
    "VolRegime",
    "ElKarouiVolConfig",
    "ElKarouiVolModel",
    "get_vol_regime",
    "get_vol_scaling_factor",
    # Strategy
    "ElKarouiVolatilityStrategy",
    "ElKarouiVolModelStrategy",  # Backwards Compatibility Alias
    "generate_signals",
    # Regime-Position Mappings
    "DEFAULT_REGIME_POSITION_MAP",
    "CONSERVATIVE_REGIME_POSITION_MAP",
    "AGGRESSIVE_REGIME_POSITION_MAP",
]
