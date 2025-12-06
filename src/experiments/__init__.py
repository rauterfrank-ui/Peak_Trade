# src/experiments/__init__.py
"""
Peak_Trade Experiments Package (Phase 29)
==========================================

Dieses Package implementiert einen Experiment-Layer für Parameter-Sweeps
über Strategien und Regime-Detection-Konfigurationen.

Kernkomponenten:
- ParamSweep: Definiert einen Parameter-Bereich für Sweeps
- ExperimentConfig: Konfiguration für einen Experiment-Durchlauf
- SweepResultRow: Ein einzelnes Ergebnis aus dem Sweep
- ExperimentRunner: Führt Sweeps aus und sammelt Ergebnisse

Helper-Module:
- strategy_sweeps: Vordefinierte Sweeps für Strategie-Parameter
- regime_sweeps: Vordefinierte Sweeps für Regime-Detection-Parameter

Example:
    >>> from src.experiments import ExperimentRunner, ExperimentConfig, ParamSweep
    >>>
    >>> config = ExperimentConfig(
    ...     name="MA Crossover Sweep",
    ...     strategy_name="ma_crossover",
    ...     param_sweeps=[
    ...         ParamSweep("fast_period", [5, 10, 20]),
    ...         ParamSweep("slow_period", [50, 100, 200]),
    ...     ],
    ...     symbols=["BTC/EUR"],
    ...     timeframe="1h",
    ... )
    >>>
    >>> runner = ExperimentRunner()
    >>> results = runner.run(config)
    >>> print(results.to_dataframe())
"""
from __future__ import annotations

from .base import (
    ParamSweep,
    ExperimentConfig,
    SweepResultRow,
    ExperimentResult,
    ExperimentRunner,
)

from .strategy_sweeps import (
    get_ma_crossover_sweeps,
    get_bollinger_sweeps,
    get_macd_sweeps,
    get_momentum_sweeps,
    get_trend_following_sweeps,
    get_vol_breakout_sweeps,
    get_mean_reversion_sweeps,
    get_rsi_reversion_sweeps,
    get_strategy_sweeps,
    list_available_strategies,
    STRATEGY_SWEEP_REGISTRY,
)

from .regime_sweeps import (
    get_volatility_detector_sweeps,
    get_range_compression_detector_sweeps,
    get_regime_detector_sweeps,
    get_strategy_switching_sweeps,
    get_combined_regime_strategy_sweeps,
    REGIME_SWEEP_REGISTRY,
)

__all__ = [
    # Base types
    "ParamSweep",
    "ExperimentConfig",
    "SweepResultRow",
    "ExperimentResult",
    "ExperimentRunner",
    # Strategy sweeps
    "get_ma_crossover_sweeps",
    "get_bollinger_sweeps",
    "get_macd_sweeps",
    "get_momentum_sweeps",
    "get_trend_following_sweeps",
    "get_vol_breakout_sweeps",
    "get_mean_reversion_sweeps",
    "get_rsi_reversion_sweeps",
    "get_strategy_sweeps",
    "list_available_strategies",
    "STRATEGY_SWEEP_REGISTRY",
    # Regime sweeps
    "get_volatility_detector_sweeps",
    "get_range_compression_detector_sweeps",
    "get_regime_detector_sweeps",
    "get_strategy_switching_sweeps",
    "get_combined_regime_strategy_sweeps",
    "REGIME_SWEEP_REGISTRY",
]
