# src/strategies/armstrong/__init__.py
"""
Armstrong-Strategien für Peak_Trade (Research-Track).

Diese Strategien basieren auf Martin Armstrongs Economic Confidence Model (ECM)
und sind ausschließlich für Research/Backtesting gedacht - NICHT für Live-Trading.

Module:
- cycle_model: Armstrong-Zyklus-Modell (ArmstrongPhase, ArmstrongCycleConfig, ArmstrongCycleModel)
- armstrong_cycle_strategy: Strategy-Implementierung (ArmstrongCycleStrategy)

⚠️ WICHTIG: R&D-TIER – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Siehe: docs/runbooks/R_AND_D_PLAYBOOK_ARMSTRONG_EL_KAROUI_V1.md
"""
from .cycle_model import (
    ArmstrongPhase,
    ArmstrongCycleConfig,
    ArmstrongCycleModel,
    get_phase_for_date,
    get_risk_multiplier_for_date,
)
from .armstrong_cycle_strategy import ArmstrongCycleStrategy

__all__ = [
    # Cycle Model
    "ArmstrongPhase",
    "ArmstrongCycleConfig",
    "ArmstrongCycleModel",
    "get_phase_for_date",
    "get_risk_multiplier_for_date",
    # Strategy
    "ArmstrongCycleStrategy",
]
