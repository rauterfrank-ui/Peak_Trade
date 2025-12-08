# src/strategies/el_karoui/__init__.py
"""
El-Karoui-Strategien für Peak_Trade (Research-Track).

Diese Strategien basieren auf stochastischen Volatilitätsmodellen und
mathematischer Finanztheorie nach Nicole El Karoui und sind ausschließlich
für Research/Backtesting gedacht - NICHT für Live-Trading.

Siehe: src/docs/nicole_el_karoui_notes.md
"""
from .el_karoui_vol_model_strategy import ElKarouiVolModelStrategy

__all__ = ["ElKarouiVolModelStrategy"]
