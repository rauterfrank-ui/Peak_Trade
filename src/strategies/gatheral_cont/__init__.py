# src/strategies/gatheral_cont/__init__.py
"""
Gatheral & Cont Strategien für Peak_Trade (Research-Track).

Diese Strategien basieren auf Jim Gatherals und Rama Conts Arbeiten zu
Volatilitätsmodellen, Rough Volatility und Markt-Regime-Dynamiken.

Kernkonzepte:
- Stochastische Volatilitätsmodelle (Gatheral)
- Rough Volatility (Gatheral, Jaisson, Rosenbaum)
- Volatilitäts-Surface-Dynamik
- Markt-Regime-Erkennung und -Switching

⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN

Referenzen:
- "The Volatility Surface" (Jim Gatheral)
- "Volatility is Rough" (Gatheral, Jaisson, Rosenbaum)
- "A Rough Path Perspective on Volatility" (Bayer, Friz, Gatheral)
- "Empirical Properties of Asset Returns" (Rama Cont)
"""
from .vol_regime_overlay_strategy import VolRegimeOverlayStrategy

__all__ = ["VolRegimeOverlayStrategy"]
