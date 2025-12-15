"""
Synthetic Models for Offline Realtime Feed
==========================================
Stochastische Modelle für synthetische Preis-Generierung.

WICHTIG: NUR für Offline-Simulation!
"""

from .garch_regime_v0 import GarchRegimeModelV0, GarchRegimeState

__all__ = [
    "GarchRegimeModelV0",
    "GarchRegimeState",
]
