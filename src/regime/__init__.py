# src/regime/__init__.py
"""
Peak_Trade Regime Detection & Strategy Switching (Phase 28)
===========================================================

Dieses Package implementiert den Regime-Layer für marktphasenbasiertes
Strategy Switching im Research/Backtest/Shadow-Kontext.

Komponenten:
1. **RegimeDetector**: Erkennt Marktphasen (breakout, ranging, trending)
2. **StrategySwitchingPolicy**: Mappt Regime auf Strategien
3. **RegimeConfig**: Konfiguration für Detector und Switching

Workflow:
    Data -> RegimeDetector -> StrategySwitchingPolicy -> Strategies -> Backtest

Usage:
    >>> from src.regime import (
    ...     RegimeLabel,
    ...     RegimeContext,
    ...     make_regime_detector,
    ...     make_switching_policy,
    ...     RegimeDetectorConfig,
    ...     StrategySwitchingConfig,
    ... )
    >>>
    >>> # Detector erstellen
    >>> detector_config = RegimeDetectorConfig(enabled=True)
    >>> detector = make_regime_detector(detector_config)
    >>>
    >>> # Regime erkennen
    >>> regimes = detector.detect_regimes(df)
    >>>
    >>> # Switching Policy
    >>> switching_config = StrategySwitchingConfig(enabled=True)
    >>> policy = make_switching_policy(switching_config)
    >>> decision = policy.decide(regime="breakout", available_strategies=["vol_breakout"])

WICHTIG: Dieser Layer ist NUR fuer Research/Backtest/Shadow, NICHT fuer Live-Trading!
"""

from .base import (
    RegimeContext,
    RegimeDetector,
    RegimeLabel,
    RegimeSeriesDetector,
    StrategySwitchDecision,
    StrategySwitchingPolicy,
)
from .config import (
    RegimeDetectorConfig,
    StrategySwitchingConfig,
)
from .detectors import (
    RangeCompressionRegimeDetector,
    VolatilityRegimeDetector,
    make_regime_detector,
)
from .switching import (
    SimpleRegimeMappingPolicy,
    make_switching_policy,
)

__all__ = [
    "RangeCompressionRegimeDetector",
    "RegimeContext",
    "RegimeDetector",
    # Config
    "RegimeDetectorConfig",
    # Base Types
    "RegimeLabel",
    "RegimeSeriesDetector",
    # Switching
    "SimpleRegimeMappingPolicy",
    "StrategySwitchDecision",
    "StrategySwitchingConfig",
    "StrategySwitchingPolicy",
    # Detectors
    "VolatilityRegimeDetector",
    "make_regime_detector",
    "make_switching_policy",
]
