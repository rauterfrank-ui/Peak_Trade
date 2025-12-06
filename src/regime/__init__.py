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
    RegimeLabel,
    RegimeContext,
    RegimeDetector,
    RegimeSeriesDetector,
    StrategySwitchDecision,
    StrategySwitchingPolicy,
)

from .config import (
    RegimeDetectorConfig,
    StrategySwitchingConfig,
)

from .detectors import (
    VolatilityRegimeDetector,
    RangeCompressionRegimeDetector,
    make_regime_detector,
)

from .switching import (
    SimpleRegimeMappingPolicy,
    make_switching_policy,
)

__all__ = [
    # Base Types
    "RegimeLabel",
    "RegimeContext",
    "RegimeDetector",
    "RegimeSeriesDetector",
    "StrategySwitchDecision",
    "StrategySwitchingPolicy",
    # Config
    "RegimeDetectorConfig",
    "StrategySwitchingConfig",
    # Detectors
    "VolatilityRegimeDetector",
    "RangeCompressionRegimeDetector",
    "make_regime_detector",
    # Switching
    "SimpleRegimeMappingPolicy",
    "make_switching_policy",
]
