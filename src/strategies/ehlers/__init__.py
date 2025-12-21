# src/strategies/ehlers/__init__.py
"""
Ehlers-Strategien für Peak_Trade (Research-Track).

Diese Strategien basieren auf John Ehlers' DSP-Techniken (Digital Signal Processing)
für Cycle-Detection und Filter-Design im Trading-Kontext.

Kernkonzepte:
- Super Smoother Filter (bessere Glättung als EMA/SMA)
- Instantaneous Trendline
- Cycle-Measurement (Dominant Cycle Period)
- Bandpass-Filter für Swing-Trading

⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN

Referenzen:
- "Cybernetic Analysis for Stocks and Futures" (John Ehlers)
- "Rocket Science for Traders" (John Ehlers)
"""

from .ehlers_cycle_filter_strategy import EhlersCycleFilterStrategy

__all__ = ["EhlersCycleFilterStrategy"]
