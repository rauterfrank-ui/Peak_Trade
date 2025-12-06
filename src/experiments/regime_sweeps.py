# src/experiments/regime_sweeps.py
"""
Peak_Trade Regime Sweeps (Phase 29)
===================================

Vordefinierte Parameter-Sweeps für Regime-Detection und Strategy-Switching.

Verfügbare Funktionen:
- get_volatility_detector_sweeps(): VolatilityRegimeDetector Parameter
- get_range_compression_detector_sweeps(): RangeCompressionRegimeDetector Parameter
- get_regime_detector_sweeps(): Kombinierte Sweeps für beide Detectors
- get_strategy_switching_sweeps(): Strategy-Switching Parameter

Utility:
- REGIME_SWEEP_REGISTRY: Dict mit allen registrierten Regime-Sweeps

Example:
    >>> from src.experiments import (
    ...     get_volatility_detector_sweeps,
    ...     ExperimentConfig,
    ... )
    >>>
    >>> # Regime-Parameter in ExperimentConfig
    >>> config = ExperimentConfig(
    ...     name="Regime Optimization",
    ...     strategy_name="vol_breakout",
    ...     param_sweeps=[...],
    ...     regime_config={
    ...         "enabled": True,
    ...         "detector_name": "volatility_breakout",
    ...     },
    ... )
    >>>
    >>> # Regime-Parameter separat sweepen
    >>> regime_sweeps = get_volatility_detector_sweeps("medium")
"""
from __future__ import annotations

from typing import Callable, Dict, List, Literal, Optional

from .base import ParamSweep


# Type für Granularität
Granularity = Literal["coarse", "medium", "fine"]


# ============================================================================
# VOLATILITY REGIME DETECTOR SWEEPS
# ============================================================================

def get_volatility_detector_sweeps(
    granularity: Granularity = "medium",
    prefix: str = "regime_",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für VolatilityRegimeDetector zurück.

    Args:
        granularity: "coarse", "medium" oder "fine"
        prefix: Prefix für Parameter-Namen (für Namespacing)

    Returns:
        Liste von ParamSweep-Objekten

    Example:
        >>> sweeps = get_volatility_detector_sweeps("medium")
        >>> print([s.name for s in sweeps])
        ['regime_vol_window', 'regime_vol_percentile_breakout', ...]
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep(
            f"{prefix}vol_window",
            [10, 20, 30],
            "ATR/Volatilitäts-Fenster"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}vol_percentile_breakout",
            [0.7, 0.8, 0.9],
            "Perzentil für Breakout-Klassifikation"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}vol_percentile_ranging",
            [0.2, 0.3, 0.4],
            "Perzentil für Ranging-Klassifikation"
        ))
    elif granularity == "medium":
        sweeps.append(ParamSweep(
            f"{prefix}vol_window",
            [10, 14, 20, 25, 30],
            "ATR/Volatilitäts-Fenster"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}vol_percentile_breakout",
            [0.65, 0.7, 0.75, 0.8, 0.85],
            "Perzentil für Breakout-Klassifikation"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}vol_percentile_ranging",
            [0.15, 0.2, 0.25, 0.3, 0.35],
            "Perzentil für Ranging-Klassifikation"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}lookback_window",
            [30, 50, 75, 100],
            "Lookback für Perzentil-Berechnung"
        ))
    else:  # fine
        sweeps.append(ParamSweep.from_range(
            f"{prefix}vol_window",
            8, 40, 4,
            "ATR/Volatilitäts-Fenster"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}vol_percentile_breakout",
            [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9],
            "Perzentil für Breakout-Klassifikation"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}vol_percentile_ranging",
            [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
            "Perzentil für Ranging-Klassifikation"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}lookback_window",
            [20, 30, 50, 75, 100, 150],
            "Lookback für Perzentil-Berechnung"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}trending_slope_threshold",
            [0.001, 0.002, 0.003, 0.005, 0.01],
            "Slope-Threshold für Trending-Erkennung"
        ))

    return sweeps


# ============================================================================
# RANGE COMPRESSION DETECTOR SWEEPS
# ============================================================================

def get_range_compression_detector_sweeps(
    granularity: Granularity = "medium",
    prefix: str = "regime_",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für RangeCompressionRegimeDetector zurück.

    Args:
        granularity: Sweep-Granularität
        prefix: Prefix für Parameter-Namen

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep(
            f"{prefix}range_compression_window",
            [10, 20, 30],
            "Fenster für Range-Berechnung"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}compression_threshold",
            [0.2, 0.3, 0.4],
            "Threshold für Kompression"
        ))
    elif granularity == "medium":
        sweeps.append(ParamSweep(
            f"{prefix}range_compression_window",
            [10, 15, 20, 25, 30],
            "Fenster für Range-Berechnung"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}compression_threshold",
            [0.15, 0.2, 0.25, 0.3, 0.35, 0.4],
            "Threshold für Kompression"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}lookback_window",
            [30, 50, 75, 100],
            "Lookback für Perzentil-Berechnung"
        ))
    else:  # fine
        sweeps.append(ParamSweep.from_range(
            f"{prefix}range_compression_window",
            5, 40, 5,
            "Fenster für Range-Berechnung"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}compression_threshold",
            [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5],
            "Threshold für Kompression"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}lookback_window",
            [20, 30, 50, 75, 100, 150],
            "Lookback für Perzentil-Berechnung"
        ))

    return sweeps


# ============================================================================
# COMBINED REGIME DETECTOR SWEEPS
# ============================================================================

def get_regime_detector_sweeps(
    detector_name: str = "volatility_breakout",
    granularity: Granularity = "medium",
    prefix: str = "regime_",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für einen spezifischen Regime-Detector zurück.

    Args:
        detector_name: "volatility_breakout" oder "range_compression"
        granularity: Sweep-Granularität
        prefix: Prefix für Parameter-Namen

    Returns:
        Liste von ParamSweep-Objekten

    Raises:
        ValueError: Bei unbekanntem Detector-Namen
    """
    name_lower = detector_name.lower()

    if name_lower in ("volatility_breakout", "volatility", "vol"):
        return get_volatility_detector_sweeps(granularity, prefix)
    elif name_lower in ("range_compression", "range", "compression"):
        return get_range_compression_detector_sweeps(granularity, prefix)
    else:
        raise ValueError(
            f"Unbekannter Regime-Detector: '{detector_name}'. "
            f"Verfügbar: 'volatility_breakout', 'range_compression'"
        )


def get_all_regime_detector_sweeps(
    granularity: Granularity = "medium",
    prefix: str = "regime_",
) -> Dict[str, List[ParamSweep]]:
    """
    Gibt Sweeps für alle Regime-Detectors zurück.

    Args:
        granularity: Sweep-Granularität
        prefix: Prefix für Parameter-Namen

    Returns:
        Dict {detector_name -> sweeps}
    """
    return {
        "volatility_breakout": get_volatility_detector_sweeps(granularity, prefix),
        "range_compression": get_range_compression_detector_sweeps(granularity, prefix),
    }


# ============================================================================
# STRATEGY SWITCHING SWEEPS
# ============================================================================

def get_strategy_switching_sweeps(
    granularity: Granularity = "medium",
    prefix: str = "switching_",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Strategy-Switching zurück.

    Note:
        Strategy-Switching hat weniger numerische Parameter,
        hauptsächlich geht es um Regime-zu-Strategie-Mappings.
        Diese Funktion fokussiert auf die konfigurierbaren Weights.

    Args:
        granularity: Sweep-Granularität
        prefix: Prefix für Parameter-Namen

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    # Weight-Kombinationen für Multi-Strategy Regimes
    if granularity == "coarse":
        # Einfache Weight-Verhältnisse
        sweeps.append(ParamSweep(
            f"{prefix}primary_weight",
            [0.5, 0.6, 0.7],
            "Gewicht für primäre Strategie"
        ))
    elif granularity == "medium":
        sweeps.append(ParamSweep(
            f"{prefix}primary_weight",
            [0.4, 0.5, 0.6, 0.7, 0.8],
            "Gewicht für primäre Strategie"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}min_confidence",
            [0.5, 0.6, 0.7, 0.8],
            "Mindest-Confidence für Regime-Switch"
        ))
    else:  # fine
        sweeps.append(ParamSweep(
            f"{prefix}primary_weight",
            [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            "Gewicht für primäre Strategie"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}min_confidence",
            [0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            "Mindest-Confidence für Regime-Switch"
        ))
        sweeps.append(ParamSweep(
            f"{prefix}regime_persistence_bars",
            [1, 3, 5, 10],
            "Bars bevor Regime-Wechsel greift"
        ))

    return sweeps


def get_regime_mapping_variants() -> List[Dict[str, List[str]]]:
    """
    Gibt verschiedene Regime-zu-Strategie-Mapping-Varianten zurück.

    Diese können in ExperimentConfig.switching_config verwendet werden,
    um verschiedene Mapping-Strategien zu testen.

    Returns:
        Liste von Mapping-Dictionaries

    Example:
        >>> variants = get_regime_mapping_variants()
        >>> for mapping in variants:
        ...     config.switching_config["regime_to_strategies"] = mapping
        ...     # Run experiment...
    """
    return [
        # Variante 1: Aggressiv (Single Strategy pro Regime)
        {
            "breakout": ["vol_breakout"],
            "ranging": ["mean_reversion_channel"],
            "trending": ["trend_following"],
            "unknown": ["ma_crossover"],
        },
        # Variante 2: Konservativ (Multiple Strategies)
        {
            "breakout": ["vol_breakout", "trend_following"],
            "ranging": ["mean_reversion_channel", "rsi_reversion", "bollinger"],
            "trending": ["trend_following", "ma_crossover"],
            "unknown": ["ma_crossover", "momentum"],
        },
        # Variante 3: Momentum-Fokus
        {
            "breakout": ["vol_breakout", "momentum"],
            "ranging": ["rsi_reversion"],
            "trending": ["trend_following", "momentum"],
            "unknown": ["momentum"],
        },
        # Variante 4: Mean-Reversion-Fokus
        {
            "breakout": ["vol_breakout"],
            "ranging": ["mean_reversion_channel", "rsi_reversion", "bollinger"],
            "trending": ["ma_crossover"],
            "unknown": ["bollinger"],
        },
    ]


def get_weight_variants() -> List[Dict[str, Dict[str, float]]]:
    """
    Gibt verschiedene Weight-Konfigurationen für Multi-Strategy Regimes zurück.

    Returns:
        Liste von Weight-Dictionaries
    """
    return [
        # Variante 1: Gleichverteilung
        {
            "ranging": {"mean_reversion_channel": 0.5, "rsi_reversion": 0.5},
            "breakout": {"vol_breakout": 0.5, "trend_following": 0.5},
        },
        # Variante 2: Primary dominiert
        {
            "ranging": {"mean_reversion_channel": 0.7, "rsi_reversion": 0.3},
            "breakout": {"vol_breakout": 0.7, "trend_following": 0.3},
        },
        # Variante 3: Strong Primary
        {
            "ranging": {"mean_reversion_channel": 0.8, "rsi_reversion": 0.2},
            "breakout": {"vol_breakout": 0.8, "trend_following": 0.2},
        },
    ]


# ============================================================================
# COMBINED REGIME + STRATEGY SWEEPS
# ============================================================================

def get_combined_regime_strategy_sweeps(
    strategy_name: str,
    detector_name: str = "volatility_breakout",
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Kombiniert Strategie- und Regime-Sweeps für ein Experiment.

    Args:
        strategy_name: Name der Strategie
        detector_name: Name des Regime-Detectors
        granularity: Sweep-Granularität

    Returns:
        Kombinierte Liste von ParamSweeps

    Example:
        >>> sweeps = get_combined_regime_strategy_sweeps(
        ...     "vol_breakout",
        ...     "volatility_breakout",
        ...     "medium",
        ... )
    """
    from .strategy_sweeps import get_strategy_sweeps

    strategy_sweeps = get_strategy_sweeps(strategy_name, granularity)
    regime_sweeps = get_regime_detector_sweeps(detector_name, granularity)

    return strategy_sweeps + regime_sweeps


# ============================================================================
# REGIME SWEEP REGISTRY
# ============================================================================

REGIME_SWEEP_REGISTRY: Dict[str, Callable[[Granularity], List[ParamSweep]]] = {
    "volatility_breakout": lambda g: get_volatility_detector_sweeps(g),
    "range_compression": lambda g: get_range_compression_detector_sweeps(g),
    "strategy_switching": lambda g: get_strategy_switching_sweeps(g),
}


def list_available_regime_sweeps() -> List[str]:
    """
    Gibt Liste aller verfügbaren Regime-Sweep-Typen zurück.

    Returns:
        Sortierte Liste der Namen
    """
    return sorted(REGIME_SWEEP_REGISTRY.keys())
