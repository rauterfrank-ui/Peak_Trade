# src/strategies/armstrong/__init__.py
"""
Armstrong-Strategien für Peak_Trade (Research-Track).

Diese Strategien basieren auf Martin Armstrongs Economic Confidence Model (ECM)
und sind ausschließlich für Research/Backtesting gedacht - NICHT für Live-Trading.

Siehe: src/docs/armstrong_notes.md
"""
from .armstrong_cycle_strategy import ArmstrongCycleStrategy

__all__ = ["ArmstrongCycleStrategy"]
