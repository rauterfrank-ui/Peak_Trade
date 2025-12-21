# src/regime/config.py
"""
Peak_Trade Regime Layer Configuration (Phase 28)
=================================================

Konfigurationsklassen fuer Regime Detection und Strategy Switching.

Diese Konfigurationen koennen aus config.toml geladen oder
programmatisch erstellt werden.

TOML-Struktur:
    [regime]
    enabled = true
    detector_name = "volatility_breakout"
    ...

    [strategy_switching]
    enabled = true
    policy_name = "simple_regime_mapping"
    ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.peak_config import PeakConfig

RegimeLabel = Literal["breakout", "ranging", "trending", "unknown"]


# ============================================================================
# REGIME DETECTOR CONFIG
# ============================================================================


@dataclass
class RegimeDetectorConfig:
    """
    Konfiguration fuer den Regime-Detector.

    Attributes:
        enabled: Ob Regime-Detection aktiviert ist
        detector_name: Name des Detectors ("volatility_breakout", "range_compression")
        lookback_window: Lookback fuer Regime-Berechnung in Bars
        min_history_bars: Minimum Bars bevor Regime berechnet wird

        # Volatility Detector Parameter
        vol_window: Fenster fuer Volatilitaets-Berechnung (ATR/Range)
        vol_percentile_breakout: Perzentil-Schwelle fuer Breakout (0.0-1.0)
        vol_percentile_ranging: Perzentil-Schwelle fuer Ranging (0.0-1.0)

        # Range Compression Parameter
        range_compression_window: Fenster fuer Range-Kompression
        compression_threshold: Schwelle fuer Kompression (0.0-1.0)

        # Trending Parameter
        trending_ma_window: MA-Fenster fuer Trend-Erkennung
        trending_slope_threshold: Slope-Schwelle fuer Trending

    Example:
        >>> config = RegimeDetectorConfig(
        ...     enabled=True,
        ...     detector_name="volatility_breakout",
        ...     vol_percentile_breakout=0.8,
        ... )
    """

    enabled: bool = False
    detector_name: str = "volatility_breakout"

    # Allgemeine Parameter
    lookback_window: int = 50
    min_history_bars: int = 100

    # Volatility Detector
    vol_window: int = 20
    vol_percentile_breakout: float = 0.75
    vol_percentile_ranging: float = 0.30

    # Range Compression Detector
    range_compression_window: int = 20
    compression_threshold: float = 0.3

    # Trending Detection
    trending_ma_window: int = 50
    trending_slope_threshold: float = 0.0002

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Config zu Dict."""
        return {
            "enabled": self.enabled,
            "detector_name": self.detector_name,
            "lookback_window": self.lookback_window,
            "min_history_bars": self.min_history_bars,
            "vol_window": self.vol_window,
            "vol_percentile_breakout": self.vol_percentile_breakout,
            "vol_percentile_ranging": self.vol_percentile_ranging,
            "range_compression_window": self.range_compression_window,
            "compression_threshold": self.compression_threshold,
            "trending_ma_window": self.trending_ma_window,
            "trending_slope_threshold": self.trending_slope_threshold,
        }

    @classmethod
    def from_peak_config(
        cls,
        cfg: "PeakConfig",
        section: str = "regime",
    ) -> "RegimeDetectorConfig":
        """
        Laedt Config aus PeakConfig (TOML).

        Args:
            cfg: PeakConfig-Instanz
            section: TOML-Sektion (default: "regime")

        Returns:
            RegimeDetectorConfig-Instanz
        """
        return cls(
            enabled=bool(cfg.get(f"{section}.enabled", False)),
            detector_name=str(cfg.get(f"{section}.detector_name", "volatility_breakout")),
            lookback_window=int(cfg.get(f"{section}.lookback_window", 50)),
            min_history_bars=int(cfg.get(f"{section}.min_history_bars", 100)),
            vol_window=int(cfg.get(f"{section}.vol_window", 20)),
            vol_percentile_breakout=float(cfg.get(f"{section}.vol_percentile_breakout", 0.75)),
            vol_percentile_ranging=float(cfg.get(f"{section}.vol_percentile_ranging", 0.30)),
            range_compression_window=int(cfg.get(f"{section}.range_compression_window", 20)),
            compression_threshold=float(cfg.get(f"{section}.compression_threshold", 0.3)),
            trending_ma_window=int(cfg.get(f"{section}.trending_ma_window", 50)),
            trending_slope_threshold=float(cfg.get(f"{section}.trending_slope_threshold", 0.0002)),
        )


# ============================================================================
# STRATEGY SWITCHING CONFIG
# ============================================================================


@dataclass
class StrategySwitchingConfig:
    """
    Konfiguration fuer die Strategy-Switching-Policy.

    Attributes:
        enabled: Ob Strategy Switching aktiviert ist
        policy_name: Name der Policy ("simple_regime_mapping")
        regime_to_strategies: Mapping Regime -> Strategy-Liste
        regime_to_weights: Optionale Gewichte je Regime/Strategy
        default_strategies: Fallback-Strategien wenn Regime nicht gemappt

    Example:
        >>> config = StrategySwitchingConfig(
        ...     enabled=True,
        ...     policy_name="simple_regime_mapping",
        ...     regime_to_strategies={
        ...         "breakout": ["vol_breakout"],
        ...         "ranging": ["mean_reversion_channel", "rsi_reversion"],
        ...     },
        ...     regime_to_weights={
        ...         "ranging": {"mean_reversion_channel": 0.6, "rsi_reversion": 0.4},
        ...     },
        ... )
    """

    enabled: bool = False
    policy_name: str = "simple_regime_mapping"

    # Mapping: Regime -> Liste von Strategy-Namen
    regime_to_strategies: Optional[Dict[str, List[str]]] = None

    # Optionale Gewichte: Regime -> {Strategy -> Weight}
    regime_to_weights: Optional[Dict[str, Dict[str, float]]] = None

    # Fallback-Strategien (wenn Regime nicht gemappt)
    default_strategies: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Setzt Defaults fuer None-Werte."""
        if self.regime_to_strategies is None:
            self.regime_to_strategies = {
                "breakout": ["vol_breakout"],
                "ranging": ["mean_reversion_channel", "rsi_reversion"],
                "trending": ["trend_following"],
                "unknown": ["ma_crossover"],
            }
        if self.default_strategies is None:
            self.default_strategies = ["ma_crossover"]

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Config zu Dict."""
        return {
            "enabled": self.enabled,
            "policy_name": self.policy_name,
            "regime_to_strategies": self.regime_to_strategies,
            "regime_to_weights": self.regime_to_weights,
            "default_strategies": self.default_strategies,
        }

    def get_strategies_for_regime(self, regime: RegimeLabel) -> List[str]:
        """
        Gibt die Strategien fuer ein Regime zurueck.

        Args:
            regime: Regime-Label

        Returns:
            Liste von Strategy-Namen
        """
        if self.regime_to_strategies and regime in self.regime_to_strategies:
            return self.regime_to_strategies[regime]
        return self.default_strategies or []

    def get_weights_for_regime(self, regime: RegimeLabel) -> Optional[Dict[str, float]]:
        """
        Gibt die Gewichte fuer ein Regime zurueck.

        Args:
            regime: Regime-Label

        Returns:
            Dict {Strategy -> Weight} oder None
        """
        if self.regime_to_weights and regime in self.regime_to_weights:
            return self.regime_to_weights[regime]
        return None

    @classmethod
    def from_peak_config(
        cls,
        cfg: "PeakConfig",
        section: str = "strategy_switching",
    ) -> "StrategySwitchingConfig":
        """
        Laedt Config aus PeakConfig (TOML).

        TOML-Struktur:
            [strategy_switching]
            enabled = true
            policy_name = "simple_regime_mapping"

            [strategy_switching.regime_to_strategies]
            breakout = ["vol_breakout"]
            ranging = ["mean_reversion_channel", "rsi_reversion"]

            [strategy_switching.regime_to_weights.ranging]
            mean_reversion_channel = 0.6
            rsi_reversion = 0.4

        Args:
            cfg: PeakConfig-Instanz
            section: TOML-Sektion (default: "strategy_switching")

        Returns:
            StrategySwitchingConfig-Instanz
        """
        enabled = bool(cfg.get(f"{section}.enabled", False))
        policy_name = str(cfg.get(f"{section}.policy_name", "simple_regime_mapping"))

        # Regime -> Strategies Mapping
        regime_to_strategies_raw = cfg.get(f"{section}.regime_to_strategies", None)
        regime_to_strategies: Optional[Dict[str, List[str]]] = None

        if regime_to_strategies_raw and isinstance(regime_to_strategies_raw, dict):
            regime_to_strategies = {}
            for regime, strategies in regime_to_strategies_raw.items():
                if isinstance(strategies, list):
                    regime_to_strategies[str(regime)] = [str(s) for s in strategies]

        # Regime -> Weights Mapping
        regime_to_weights_raw = cfg.get(f"{section}.regime_to_weights", None)
        regime_to_weights: Optional[Dict[str, Dict[str, float]]] = None

        if regime_to_weights_raw and isinstance(regime_to_weights_raw, dict):
            regime_to_weights = {}
            for regime, weights_dict in regime_to_weights_raw.items():
                if isinstance(weights_dict, dict):
                    regime_to_weights[str(regime)] = {
                        str(k): float(v) for k, v in weights_dict.items()
                    }

        # Default Strategies
        default_strategies_raw = cfg.get(f"{section}.default_strategies", None)
        default_strategies: Optional[List[str]] = None

        if default_strategies_raw and isinstance(default_strategies_raw, list):
            default_strategies = [str(s) for s in default_strategies_raw]

        return cls(
            enabled=enabled,
            policy_name=policy_name,
            regime_to_strategies=regime_to_strategies,
            regime_to_weights=regime_to_weights,
            default_strategies=default_strategies,
        )
