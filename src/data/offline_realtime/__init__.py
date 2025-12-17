"""
Peak_Trade Offline Realtime Module
===================================
Synthetische Tick-Generierung für Offline-Simulation und Backtesting.

WICHTIG: Dieses Modul ist NUR für Offline-Simulation gedacht!
         Niemals für Live-Trading verwenden.

Enthält:
    - GARCH(1,1) + Markov-Regime-Switching Modell
    - OfflineRealtimeFeedV0: Synthetischer Tick-Generator

Alle generierten Ticks tragen is_synthetic=True.
"""

from .offline_realtime_feed_v0 import (
    OfflineRealtimeFeedV0,
    OfflineRealtimeFeedV0Config,
    RegimeParams,
    SyntheticTick,
)
from .synthetic_models.garch_regime_v0 import (
    GarchRegimeModelV0,
    GarchRegimeState,
)

__all__ = [
    # Model
    "GarchRegimeModelV0",
    "GarchRegimeState",
    "OfflineRealtimeFeedV0",
    "OfflineRealtimeFeedV0Config",
    "RegimeParams",
    # Feed
    "SyntheticTick",
]
