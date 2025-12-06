# src/experiments/strategy_sweeps.py
"""
Peak_Trade Strategy Sweeps (Phase 29)
=====================================

Vordefinierte Parameter-Sweeps für alle verfügbaren Strategien.

Jede Strategie hat eine get_*_sweeps() Funktion, die eine Liste von
ParamSweep-Objekten zurückgibt. Diese können direkt in ExperimentConfig
verwendet werden.

Verfügbare Funktionen:
- get_ma_crossover_sweeps(): MA Crossover
- get_bollinger_sweeps(): Bollinger Bands
- get_macd_sweeps(): MACD
- get_momentum_sweeps(): Momentum
- get_trend_following_sweeps(): Trend Following (ADX)
- get_vol_breakout_sweeps(): Volatility Breakout
- get_mean_reversion_sweeps(): Mean Reversion
- get_rsi_reversion_sweeps(): RSI Reversion

Utility:
- get_strategy_sweeps(strategy_name): Gibt Sweeps für beliebige Strategie
- STRATEGY_SWEEP_REGISTRY: Dict mit allen registrierten Sweeps

Example:
    >>> from src.experiments import get_ma_crossover_sweeps, ExperimentConfig
    >>>
    >>> config = ExperimentConfig(
    ...     name="MA Crossover Optimization",
    ...     strategy_name="ma_crossover",
    ...     param_sweeps=get_ma_crossover_sweeps(granularity="fine"),
    ... )
"""
from __future__ import annotations

from typing import Callable, Dict, List, Literal, Optional

from .base import ParamSweep


# Type für Granularität
Granularity = Literal["coarse", "medium", "fine"]


# ============================================================================
# MA CROSSOVER SWEEPS
# ============================================================================

def get_ma_crossover_sweeps(
    granularity: Granularity = "medium",
    include_ma_type: bool = False,
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für MA Crossover Strategie zurück.

    Args:
        granularity: "coarse" (wenig), "medium" (mittel), "fine" (viel)
        include_ma_type: Ob MA-Typ (sma/ema) gesweept werden soll

    Returns:
        Liste von ParamSweep-Objekten

    Example:
        >>> sweeps = get_ma_crossover_sweeps("fine")
        >>> print([s.name for s in sweeps])
        ['fast_period', 'slow_period']
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("fast_period", [5, 10, 20], "Schneller MA"))
        sweeps.append(ParamSweep("slow_period", [50, 100, 200], "Langsamer MA"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("fast_period", [5, 10, 15, 20, 30], "Schneller MA"))
        sweeps.append(ParamSweep("slow_period", [50, 75, 100, 150, 200], "Langsamer MA"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("fast_period", 5, 30, 5, "Schneller MA"))
        sweeps.append(ParamSweep.from_range("slow_period", 40, 200, 20, "Langsamer MA"))

    if include_ma_type:
        sweeps.append(ParamSweep("ma_type", ["sma", "ema"], "MA-Typ"))

    return sweeps


# ============================================================================
# BOLLINGER BANDS SWEEPS
# ============================================================================

def get_bollinger_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Bollinger Bands Strategie zurück.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("period", [10, 20, 30], "BB Periode"))
        sweeps.append(ParamSweep("num_std", [1.5, 2.0, 2.5], "Standardabweichungen"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("period", [10, 15, 20, 25, 30], "BB Periode"))
        sweeps.append(ParamSweep("num_std", [1.5, 1.75, 2.0, 2.25, 2.5], "Standardabweichungen"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("period", 10, 40, 5, "BB Periode"))
        sweeps.append(ParamSweep("num_std", [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0], "Standardabweichungen"))

    return sweeps


# ============================================================================
# MACD SWEEPS
# ============================================================================

def get_macd_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für MACD Strategie zurück.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("fast_period", [8, 12, 16], "MACD Fast"))
        sweeps.append(ParamSweep("slow_period", [20, 26, 32], "MACD Slow"))
        sweeps.append(ParamSweep("signal_period", [7, 9, 11], "MACD Signal"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("fast_period", [6, 9, 12, 15, 18], "MACD Fast"))
        sweeps.append(ParamSweep("slow_period", [18, 22, 26, 30, 34], "MACD Slow"))
        sweeps.append(ParamSweep("signal_period", [6, 8, 9, 10, 12], "MACD Signal"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("fast_period", 5, 20, 2, "MACD Fast"))
        sweeps.append(ParamSweep.from_range("slow_period", 16, 40, 3, "MACD Slow"))
        sweeps.append(ParamSweep.from_range("signal_period", 5, 15, 2, "MACD Signal"))

    return sweeps


# ============================================================================
# MOMENTUM SWEEPS
# ============================================================================

def get_momentum_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Momentum Strategie zurück.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("lookback", [10, 20, 30], "Momentum Lookback"))
        sweeps.append(ParamSweep("threshold", [0.0, 0.01, 0.02], "Entry-Threshold"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("lookback", [5, 10, 15, 20, 30, 50], "Momentum Lookback"))
        sweeps.append(ParamSweep("threshold", [0.0, 0.005, 0.01, 0.015, 0.02], "Entry-Threshold"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("lookback", 5, 60, 5, "Momentum Lookback"))
        sweeps.append(ParamSweep("threshold", [0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03], "Entry-Threshold"))

    return sweeps


# ============================================================================
# TREND FOLLOWING SWEEPS
# ============================================================================

def get_trend_following_sweeps(
    granularity: Granularity = "medium",
    include_ma_filter: bool = False,
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Trend Following (ADX) Strategie zurück.

    Args:
        granularity: Sweep-Granularität
        include_ma_filter: Ob MA-Filter Parameter inkludiert werden

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("adx_period", [10, 14, 20], "ADX Periode"))
        sweeps.append(ParamSweep("adx_threshold", [20, 25, 30], "ADX Threshold"))
        sweeps.append(ParamSweep("exit_threshold", [15, 20], "Exit Threshold"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("adx_period", [10, 12, 14, 16, 20], "ADX Periode"))
        sweeps.append(ParamSweep("adx_threshold", [18, 22, 25, 28, 32], "ADX Threshold"))
        sweeps.append(ParamSweep("exit_threshold", [12, 15, 18, 20], "Exit Threshold"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("adx_period", 8, 24, 2, "ADX Periode"))
        sweeps.append(ParamSweep.from_range("adx_threshold", 15, 40, 5, "ADX Threshold"))
        sweeps.append(ParamSweep.from_range("exit_threshold", 10, 25, 3, "Exit Threshold"))

    if include_ma_filter:
        sweeps.append(ParamSweep("ma_period", [20, 50, 100, 200], "MA Filter Periode"))
        sweeps.append(ParamSweep("use_ma_filter", [True, False], "MA Filter aktiv"))

    return sweeps


# ============================================================================
# VOLATILITY BREAKOUT SWEEPS
# ============================================================================

def get_vol_breakout_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Volatility Breakout Strategie zurück.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("atr_period", [10, 14, 20], "ATR Periode"))
        sweeps.append(ParamSweep("atr_multiplier", [1.5, 2.0, 2.5], "ATR Multiplier"))
        sweeps.append(ParamSweep("lookback_period", [10, 20, 30], "Lookback"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("atr_period", [10, 12, 14, 18, 22], "ATR Periode"))
        sweeps.append(ParamSweep("atr_multiplier", [1.0, 1.5, 2.0, 2.5, 3.0], "ATR Multiplier"))
        sweeps.append(ParamSweep("lookback_period", [10, 15, 20, 25, 30], "Lookback"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("atr_period", 8, 26, 3, "ATR Periode"))
        sweeps.append(ParamSweep("atr_multiplier", [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5], "ATR Multiplier"))
        sweeps.append(ParamSweep.from_range("lookback_period", 5, 40, 5, "Lookback"))

    return sweeps


# ============================================================================
# MEAN REVERSION SWEEPS
# ============================================================================

def get_mean_reversion_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Mean Reversion Strategie zurück.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("lookback", [10, 20, 30], "Lookback Periode"))
        sweeps.append(ParamSweep("entry_z_score", [1.5, 2.0, 2.5], "Entry Z-Score"))
        sweeps.append(ParamSweep("exit_z_score", [0.0, 0.5, 1.0], "Exit Z-Score"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("lookback", [10, 15, 20, 25, 30, 40], "Lookback Periode"))
        sweeps.append(ParamSweep("entry_z_score", [1.0, 1.5, 2.0, 2.5, 3.0], "Entry Z-Score"))
        sweeps.append(ParamSweep("exit_z_score", [0.0, 0.25, 0.5, 0.75, 1.0], "Exit Z-Score"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("lookback", 5, 50, 5, "Lookback Periode"))
        sweeps.append(ParamSweep("entry_z_score", [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5], "Entry Z-Score"))
        sweeps.append(ParamSweep("exit_z_score", [-0.5, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25], "Exit Z-Score"))

    return sweeps


# ============================================================================
# RSI REVERSION SWEEPS
# ============================================================================

def get_rsi_reversion_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für RSI Reversion Strategie zurück.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("rsi_period", [7, 14, 21], "RSI Periode"))
        sweeps.append(ParamSweep("oversold_level", [20, 30, 40], "Oversold Level"))
        sweeps.append(ParamSweep("overbought_level", [60, 70, 80], "Overbought Level"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("rsi_period", [5, 7, 10, 14, 21], "RSI Periode"))
        sweeps.append(ParamSweep("oversold_level", [15, 20, 25, 30, 35], "Oversold Level"))
        sweeps.append(ParamSweep("overbought_level", [65, 70, 75, 80, 85], "Overbought Level"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("rsi_period", 3, 25, 2, "RSI Periode"))
        sweeps.append(ParamSweep.from_range("oversold_level", 10, 40, 5, "Oversold Level"))
        sweeps.append(ParamSweep.from_range("overbought_level", 60, 90, 5, "Overbought Level"))

    return sweeps


# ============================================================================
# BREAKOUT SWEEPS (Phase 41)
# ============================================================================

def get_breakout_sweeps(
    granularity: Granularity = "medium",
    include_sl_tp: bool = True,
    include_trailing: bool = False,
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Breakout Strategie zurück.

    Args:
        granularity: Sweep-Granularität
        include_sl_tp: Ob Stop-Loss/Take-Profit Parameter inkludiert werden
        include_trailing: Ob Trailing-Stop Parameter inkludiert werden

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("lookback_breakout", [20, 50, 100], "Breakout Lookback"))
        if include_sl_tp:
            sweeps.append(ParamSweep("stop_loss_pct", [0.02, 0.03, 0.05], "Stop-Loss %"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("lookback_breakout", [15, 20, 30, 50, 75], "Breakout Lookback"))
        if include_sl_tp:
            sweeps.append(ParamSweep("stop_loss_pct", [0.02, 0.03, 0.04, 0.05], "Stop-Loss %"))
            sweeps.append(ParamSweep("take_profit_pct", [0.04, 0.06, 0.08, 0.10], "Take-Profit %"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("lookback_breakout", 10, 100, 10, "Breakout Lookback"))
        if include_sl_tp:
            sweeps.append(ParamSweep("stop_loss_pct", [0.01, 0.02, 0.03, 0.04, 0.05], "Stop-Loss %"))
            sweeps.append(ParamSweep("take_profit_pct", [0.03, 0.05, 0.08, 0.10, 0.15], "Take-Profit %"))

    if include_trailing:
        if granularity == "coarse":
            sweeps.append(ParamSweep("trailing_stop_pct", [0.02, 0.05], "Trailing-Stop %"))
        elif granularity == "medium":
            sweeps.append(ParamSweep("trailing_stop_pct", [0.02, 0.03, 0.05, 0.08], "Trailing-Stop %"))
        else:  # fine
            sweeps.append(ParamSweep("trailing_stop_pct", [0.01, 0.02, 0.03, 0.05, 0.08, 0.10], "Trailing-Stop %"))

    return sweeps


# ============================================================================
# VOL REGIME FILTER SWEEPS (Phase 41)
# ============================================================================

def get_vol_regime_filter_sweeps(
    granularity: Granularity = "medium",
    include_percentile: bool = True,
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Vol Regime Filter zurück.

    Args:
        granularity: Sweep-Granularität
        include_percentile: Ob Perzentil-basierte Parameter inkludiert werden

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("vol_window", [10, 14, 20], "Vol Window"))
        if include_percentile:
            sweeps.append(ParamSweep("vol_percentile_low", [20, 30], "Vol Percentile Low"))
            sweeps.append(ParamSweep("vol_percentile_high", [70, 80], "Vol Percentile High"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("vol_window", [10, 14, 20, 30], "Vol Window"))
        sweeps.append(ParamSweep("vol_method", ["atr", "std"], "Vol Method"))
        if include_percentile:
            sweeps.append(ParamSweep("vol_percentile_low", [10, 20, 30], "Vol Percentile Low"))
            sweeps.append(ParamSweep("vol_percentile_high", [70, 80, 90], "Vol Percentile High"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("vol_window", 8, 30, 4, "Vol Window"))
        sweeps.append(ParamSweep("vol_method", ["atr", "std", "realized"], "Vol Method"))
        if include_percentile:
            sweeps.append(ParamSweep("vol_percentile_low", [5, 10, 15, 20, 25, 30], "Vol Percentile Low"))
            sweeps.append(ParamSweep("vol_percentile_high", [70, 75, 80, 85, 90, 95], "Vol Percentile High"))
        sweeps.append(ParamSweep("lookback_percentile", [50, 100, 200], "Lookback Percentile"))

    return sweeps


# ============================================================================
# DONCHIAN CHANNEL SWEEPS
# ============================================================================

def get_donchian_sweeps(
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für Donchian Channel Strategie zurück.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten
    """
    sweeps = []

    if granularity == "coarse":
        sweeps.append(ParamSweep("entry_period", [10, 20, 55], "Entry Periode"))
        sweeps.append(ParamSweep("exit_period", [5, 10, 20], "Exit Periode"))
    elif granularity == "medium":
        sweeps.append(ParamSweep("entry_period", [10, 15, 20, 30, 40, 55], "Entry Periode"))
        sweeps.append(ParamSweep("exit_period", [5, 10, 15, 20, 25], "Exit Periode"))
    else:  # fine
        sweeps.append(ParamSweep.from_range("entry_period", 10, 60, 5, "Entry Periode"))
        sweeps.append(ParamSweep.from_range("exit_period", 5, 30, 5, "Exit Periode"))

    return sweeps


# ============================================================================
# STRATEGY SWEEP REGISTRY
# ============================================================================

# Registry aller Sweep-Funktionen
STRATEGY_SWEEP_REGISTRY: Dict[str, Callable[[Granularity], List[ParamSweep]]] = {
    "ma_crossover": lambda g: get_ma_crossover_sweeps(g),
    "bollinger": lambda g: get_bollinger_sweeps(g),
    "macd": lambda g: get_macd_sweeps(g),
    "momentum": lambda g: get_momentum_sweeps(g),
    "trend_following": lambda g: get_trend_following_sweeps(g),
    "vol_breakout": lambda g: get_vol_breakout_sweeps(g),
    "mean_reversion": lambda g: get_mean_reversion_sweeps(g),
    "mean_reversion_channel": lambda g: get_mean_reversion_sweeps(g),
    "rsi_reversion": lambda g: get_rsi_reversion_sweeps(g),
    "breakout_donchian": lambda g: get_donchian_sweeps(g),
    # Phase 41 Additions
    "breakout": lambda g: get_breakout_sweeps(g),
    "vol_regime_filter": lambda g: get_vol_regime_filter_sweeps(g),
}


def get_strategy_sweeps(
    strategy_name: str,
    granularity: Granularity = "medium",
) -> List[ParamSweep]:
    """
    Gibt Parameter-Sweeps für eine beliebige Strategie zurück.

    Args:
        strategy_name: Name der Strategie (aus Registry)
        granularity: Sweep-Granularität

    Returns:
        Liste von ParamSweep-Objekten

    Raises:
        ValueError: Bei unbekannter Strategie

    Example:
        >>> sweeps = get_strategy_sweeps("ma_crossover", "fine")
        >>> print(len(sweeps))
        2
    """
    # Normalisiere Namen
    name_lower = strategy_name.lower().replace("-", "_")

    if name_lower in STRATEGY_SWEEP_REGISTRY:
        return STRATEGY_SWEEP_REGISTRY[name_lower](granularity)

    # Alias-Handling
    aliases = {
        "ma": "ma_crossover",
        "moving_average": "ma_crossover",
        "bb": "bollinger",
        "bollinger_bands": "bollinger",
        "trend": "trend_following",
        "adx": "trend_following",
        "volatility": "vol_breakout",
        "vol": "vol_breakout",
        "reversion": "mean_reversion",
        "rsi": "rsi_reversion",
        "donchian": "breakout_donchian",
    }

    if name_lower in aliases:
        return STRATEGY_SWEEP_REGISTRY[aliases[name_lower]](granularity)

    available = ", ".join(sorted(STRATEGY_SWEEP_REGISTRY.keys()))
    raise ValueError(
        f"Unbekannte Strategie: '{strategy_name}'. "
        f"Verfügbar: {available}"
    )


def list_available_strategies() -> List[str]:
    """
    Gibt Liste aller Strategien mit verfügbaren Sweeps zurück.

    Returns:
        Sortierte Liste der Strategie-Namen
    """
    return sorted(STRATEGY_SWEEP_REGISTRY.keys())


def get_all_strategy_sweeps(
    granularity: Granularity = "medium",
) -> Dict[str, List[ParamSweep]]:
    """
    Gibt Sweeps für alle registrierten Strategien zurück.

    Args:
        granularity: Sweep-Granularität

    Returns:
        Dict {strategy_name -> sweeps}
    """
    return {
        name: func(granularity)
        for name, func in STRATEGY_SWEEP_REGISTRY.items()
    }
