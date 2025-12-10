# src/strategies/lopez_de_prado/__init__.py
"""
López de Prado Strategien für Peak_Trade (Research-Track).

Diese Strategien basieren auf Marcos López de Prados Arbeiten zu
Machine Learning im Asset Management, insbesondere:
- Meta-Labeling
- Triple-Barrier Method
- Feature Engineering für ML

⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN

Kernkonzepte:
- Triple-Barrier: Definiert Take-Profit, Stop-Loss und Zeitlimit
- Meta-Labeling: ML-Modell entscheidet, ob Basis-Signal gehandelt wird
- Bet-Sizing: Positionsgröße basierend auf Modell-Confidence

Referenzen:
- "Advances in Financial Machine Learning" (Marcos López de Prado)
- "Machine Learning for Asset Managers" (Marcos López de Prado)
"""
from .meta_labeling_strategy import MetaLabelingStrategy

__all__ = ["MetaLabelingStrategy"]


