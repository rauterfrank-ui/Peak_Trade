# src/experiments/research_playground.py
"""
Peak_Trade Research Playground (Phase 41)
==========================================

Zentrale Schnittstelle für Strategy-Sweeps und Research-Experimente.

Dieses Modul bietet:
- StrategySweepConfig: Erweiterte Sweep-Definition mit Constraints
- Vordefinierte Sweep-Definitionen für alle Strategien
- Portfolio-Sweep-Unterstützung
- Batch-Execution von Sweeps

Usage:
    from src.experiments.research_playground import (
        StrategySweepConfig,
        get_predefined_sweep,
        list_predefined_sweeps,
        run_sweep_batch,
    )

    # Vordefinierte Sweeps nutzen
    sweep = get_predefined_sweep("ma_crossover_basic")
    result = run_sweep_batch(sweep, data)

    # Eigene Sweeps definieren
    sweep = StrategySweepConfig(
        name="custom_rsi_sweep",
        strategy_name="rsi_reversion",
        param_grid={
            "rsi_period": [7, 14, 21],
            "oversold_level": [20, 25, 30],
            "overbought_level": [70, 75, 80],
        },
        constraints=[("oversold_level", "<", "overbought_level")],
    )
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from itertools import product
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd

from .base import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    ParamSweep,
    SweepResultRow,
)
from .strategy_sweeps import (
    get_ma_crossover_sweeps,
    get_rsi_reversion_sweeps,
    get_vol_breakout_sweeps,
    get_momentum_sweeps,
    get_bollinger_sweeps,
    get_donchian_sweeps,
    Granularity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTRAINT TYPES
# =============================================================================

ConstraintOperator = str  # "<", ">", "<=", ">=", "==", "!="


@dataclass
class ParamConstraint:
    """
    Definiert eine Bedingung zwischen zwei Parametern.

    Example:
        # fast_window muss kleiner als slow_window sein
        ParamConstraint("fast_window", "<", "slow_window")

        # rsi_period muss mindestens 5 sein
        ParamConstraint("rsi_period", ">=", 5)
    """

    left_param: str
    operator: ConstraintOperator
    right: Union[str, int, float]

    def evaluate(self, params: Dict[str, Any]) -> bool:
        """
        Prüft ob die Constraint für gegebene Parameter erfüllt ist.

        Args:
            params: Parameter-Dictionary

        Returns:
            True wenn Constraint erfüllt
        """
        left_val = params.get(self.left_param)
        if left_val is None:
            return True  # Keine Einschränkung wenn Parameter fehlt

        # Right kann ein Parameter-Name oder ein Wert sein
        if isinstance(self.right, str) and self.right in params:
            right_val = params[self.right]
        else:
            right_val = self.right

        if right_val is None:
            return True

        # Operator anwenden
        if self.operator == "<":
            return left_val < right_val
        elif self.operator == ">":
            return left_val > right_val
        elif self.operator == "<=":
            return left_val <= right_val
        elif self.operator == ">=":
            return left_val >= right_val
        elif self.operator == "==":
            return left_val == right_val
        elif self.operator == "!=":
            return left_val != right_val
        else:
            raise ValueError(f"Unbekannter Operator: {self.operator}")


# =============================================================================
# STRATEGY SWEEP CONFIG
# =============================================================================


@dataclass
class StrategySweepConfig:
    """
    Erweiterte Sweep-Konfiguration mit Constraints und Portfolio-Support.

    Attributes:
        name: Eindeutiger Name des Sweeps
        strategy_name: Name der Strategie aus der Registry
        param_grid: Parameter-Grid als Dict {param_name: [values]}
        constraints: Liste von Constraints zwischen Parametern
        base_params: Feste Parameter die nicht gesweept werden
        description: Optionale Beschreibung
        tags: Tags für Kategorisierung
        symbols: Symbole für den Backtest (default: ["BTC/EUR"])
        timeframe: Timeframe (default: "1h")
        portfolio_config: Optional Config für Portfolio-Sweeps

    Example:
        >>> sweep = StrategySweepConfig(
        ...     name="ma_crossover_basic",
        ...     strategy_name="ma_crossover",
        ...     param_grid={
        ...         "fast_period": [5, 10, 20],
        ...         "slow_period": [50, 100, 200],
        ...     },
        ...     constraints=[("fast_period", "<", "slow_period")],
        ... )
        >>> combos = sweep.generate_param_combinations()
    """

    name: str
    strategy_name: str
    param_grid: Dict[str, List[Any]] = field(default_factory=dict)
    constraints: List[Union[ParamConstraint, Tuple[str, str, Any]]] = field(
        default_factory=list
    )
    base_params: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    symbols: List[str] = field(default_factory=lambda: ["BTC/EUR"])
    timeframe: str = "1h"
    portfolio_config: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validierung und Normalisierung."""
        if not self.name:
            raise ValueError("StrategySweepConfig.name darf nicht leer sein")
        if not self.strategy_name:
            raise ValueError("StrategySweepConfig.strategy_name darf nicht leer sein")

        # Konvertiere Tuple-Constraints zu ParamConstraint
        normalized_constraints: List[ParamConstraint] = []
        for c in self.constraints:
            if isinstance(c, ParamConstraint):
                normalized_constraints.append(c)
            elif isinstance(c, tuple) and len(c) == 3:
                normalized_constraints.append(ParamConstraint(c[0], c[1], c[2]))
            else:
                raise ValueError(f"Ungültiges Constraint-Format: {c}")
        self.constraints = normalized_constraints

    @property
    def num_raw_combinations(self) -> int:
        """Anzahl Kombinationen ohne Constraint-Filter."""
        if not self.param_grid:
            return 1
        n = 1
        for values in self.param_grid.values():
            n *= len(values)
        return n

    def _passes_constraints(self, params: Dict[str, Any]) -> bool:
        """Prüft ob alle Constraints für params erfüllt sind."""
        for constraint in self.constraints:
            if not constraint.evaluate(params):
                return False
        return True

    def generate_param_combinations(self) -> List[Dict[str, Any]]:
        """
        Generiert alle gültigen Parameter-Kombinationen.

        Kombinationen die Constraints verletzen werden gefiltert.

        Returns:
            Liste von Parameter-Dictionaries
        """
        if not self.param_grid:
            return [dict(self.base_params)]

        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())

        combinations = []
        for combo in product(*param_values):
            param_dict = dict(zip(param_names, combo))
            # Merge mit base_params
            full_params = {**self.base_params, **param_dict}

            # Constraints prüfen
            if self._passes_constraints(full_params):
                combinations.append(full_params)

        return combinations

    @property
    def num_combinations(self) -> int:
        """Anzahl gültiger Kombinationen (nach Constraint-Filter)."""
        return len(self.generate_param_combinations())

    def to_experiment_config(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_capital: float = 10000.0,
        output_dir: str = "reports/experiments",
    ) -> ExperimentConfig:
        """
        Konvertiert zu ExperimentConfig für ExperimentRunner.

        Args:
            start_date: Backtest-Startdatum
            end_date: Backtest-Enddatum
            initial_capital: Startkapital
            output_dir: Ausgabe-Verzeichnis

        Returns:
            ExperimentConfig-Objekt
        """
        # Erstelle ParamSweeps aus param_grid
        param_sweeps = []
        for param_name, values in self.param_grid.items():
            param_sweeps.append(ParamSweep(param_name, values))

        return ExperimentConfig(
            name=self.name,
            strategy_name=self.strategy_name,
            param_sweeps=param_sweeps,
            symbols=self.symbols,
            timeframe=self.timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            base_params=self.base_params,
            output_dir=output_dir,
            tags=self.tags + ["phase41", "research_playground"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "name": self.name,
            "strategy_name": self.strategy_name,
            "param_grid": self.param_grid,
            "constraints": [
                (c.left_param, c.operator, c.right) for c in self.constraints
            ],
            "base_params": self.base_params,
            "description": self.description,
            "tags": self.tags,
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "portfolio_config": self.portfolio_config,
            "num_combinations": self.num_combinations,
            "num_raw_combinations": self.num_raw_combinations,
        }


# =============================================================================
# PREDEFINED SWEEPS
# =============================================================================

# Registry der vordefinierten Sweeps
_PREDEFINED_SWEEPS: Dict[str, StrategySweepConfig] = {}


def register_predefined_sweep(sweep: StrategySweepConfig) -> None:
    """Registriert einen vordefinierten Sweep."""
    _PREDEFINED_SWEEPS[sweep.name] = sweep


def get_predefined_sweep(name: str) -> StrategySweepConfig:
    """
    Gibt einen vordefinierten Sweep zurück.

    Args:
        name: Name des Sweeps

    Returns:
        StrategySweepConfig

    Raises:
        KeyError: Wenn Sweep nicht gefunden
    """
    if name not in _PREDEFINED_SWEEPS:
        available = ", ".join(sorted(_PREDEFINED_SWEEPS.keys()))
        raise KeyError(
            f"Sweep '{name}' nicht gefunden. Verfügbar: {available}"
        )
    return _PREDEFINED_SWEEPS[name]


def list_predefined_sweeps() -> List[str]:
    """Gibt Liste aller vordefinierten Sweep-Namen zurück."""
    return sorted(_PREDEFINED_SWEEPS.keys())


def get_all_predefined_sweeps() -> Dict[str, StrategySweepConfig]:
    """Gibt alle vordefinierten Sweeps zurück."""
    return dict(_PREDEFINED_SWEEPS)


# -----------------------------------------------------------------------------
# MA Crossover Sweeps
# -----------------------------------------------------------------------------

register_predefined_sweep(
    StrategySweepConfig(
        name="ma_crossover_basic",
        strategy_name="ma_crossover",
        param_grid={
            "fast_period": [5, 10, 20],
            "slow_period": [50, 100, 200],
        },
        constraints=[("fast_period", "<", "slow_period")],
        description="Basic MA Crossover Sweep mit Standard-Fenstern",
        tags=["ma", "trend_following", "basic"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="ma_crossover_fine",
        strategy_name="ma_crossover",
        param_grid={
            "fast_period": [5, 8, 10, 12, 15, 20, 25, 30],
            "slow_period": [40, 50, 75, 100, 150, 200],
        },
        constraints=[("fast_period", "<", "slow_period")],
        description="Fine-grained MA Crossover Sweep",
        tags=["ma", "trend_following", "fine"],
    )
)


# -----------------------------------------------------------------------------
# RSI Reversion Sweeps
# -----------------------------------------------------------------------------

register_predefined_sweep(
    StrategySweepConfig(
        name="rsi_reversion_basic",
        strategy_name="rsi_reversion",
        param_grid={
            "rsi_period": [7, 14, 21],
            "oversold_level": [20, 25, 30],
            "overbought_level": [70, 75, 80],
        },
        constraints=[("oversold_level", "<", "overbought_level")],
        description="Basic RSI Reversion Sweep",
        tags=["rsi", "mean_reversion", "basic"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="rsi_reversion_aggressive",
        strategy_name="rsi_reversion",
        param_grid={
            "rsi_period": [5, 7, 10, 14],
            "oversold_level": [15, 20, 25],
            "overbought_level": [75, 80, 85],
        },
        constraints=[("oversold_level", "<", "overbought_level")],
        description="Aggressive RSI Reversion mit weiteren Levels",
        tags=["rsi", "mean_reversion", "aggressive"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="rsi_reversion_fine",
        strategy_name="rsi_reversion",
        param_grid={
            "rsi_period": [5, 7, 10, 14, 21, 28],
            "oversold_level": [15, 20, 25, 30, 35],
            "overbought_level": [65, 70, 75, 80, 85],
        },
        constraints=[("oversold_level", "<", "overbought_level")],
        description="Fine-grained RSI Reversion Sweep",
        tags=["rsi", "mean_reversion", "fine"],
    )
)


# -----------------------------------------------------------------------------
# Breakout Sweeps
# -----------------------------------------------------------------------------

register_predefined_sweep(
    StrategySweepConfig(
        name="breakout_basic",
        strategy_name="breakout",
        param_grid={
            "lookback_breakout": [20, 50, 100],
            "stop_loss_pct": [0.02, 0.03, 0.05],
        },
        description="Basic Breakout Sweep mit Stop-Loss-Varianten",
        tags=["breakout", "trend_following", "basic"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="breakout_with_tp",
        strategy_name="breakout",
        param_grid={
            "lookback_breakout": [15, 20, 30, 50],
            "stop_loss_pct": [0.02, 0.03, 0.04],
            "take_profit_pct": [0.04, 0.06, 0.08, 0.10],
        },
        constraints=[("stop_loss_pct", "<", "take_profit_pct")],
        description="Breakout Sweep mit Stop-Loss und Take-Profit",
        tags=["breakout", "trend_following", "sl_tp"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="breakout_trailing",
        strategy_name="breakout",
        param_grid={
            "lookback_breakout": [20, 30, 50],
            "trailing_stop_pct": [0.02, 0.03, 0.05, 0.08],
        },
        description="Breakout Sweep mit Trailing-Stop",
        tags=["breakout", "trend_following", "trailing"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="breakout_fine",
        strategy_name="breakout",
        param_grid={
            "lookback_breakout": [10, 15, 20, 30, 50, 75, 100],
            "stop_loss_pct": [0.01, 0.02, 0.03, 0.04, 0.05],
            "take_profit_pct": [0.03, 0.05, 0.08, 0.10, 0.15],
            "trailing_stop_pct": [None, 0.02, 0.03, 0.05],
        },
        constraints=[("stop_loss_pct", "<", "take_profit_pct")],
        description="Fine-grained Breakout Sweep",
        tags=["breakout", "trend_following", "fine"],
    )
)


# -----------------------------------------------------------------------------
# Vol Regime Filter Sweeps

# -----------------------------------------------------------------------------
# Regime-Aware Portfolio Sweeps
# -----------------------------------------------------------------------------

from .regime_aware_portfolio_sweeps import (
    get_regime_aware_aggressive_sweeps,
    get_regime_aware_conservative_sweeps,
    get_regime_aware_volmetric_sweeps,
)

# Aggressives Preset
aggressive_sweeps = get_regime_aware_aggressive_sweeps("medium")
aggressive_param_grid = {s.name: s.values for s in aggressive_sweeps}
register_predefined_sweep(
    StrategySweepConfig(
        name="regime_aware_portfolio_aggressive",
        strategy_name="regime_aware_portfolio",
        param_grid=aggressive_param_grid,
        base_params={
            "components": ["breakout", "rsi_reversion"],
            "base_weights": {"breakout": 0.6, "rsi_reversion": 0.4},
            "regime_strategy": "vol_regime_filter",
        },
        description="Aggressives Regime-Aware Portfolio: Breakout + RSI mit starkem Risk-On-Fokus",
        tags=["regime_aware", "portfolio", "aggressive", "breakout", "rsi"],
    )
)

# Konservatives Preset
conservative_sweeps = get_regime_aware_conservative_sweeps("medium")
conservative_param_grid = {s.name: s.values for s in conservative_sweeps}
register_predefined_sweep(
    StrategySweepConfig(
        name="regime_aware_portfolio_conservative",
        strategy_name="regime_aware_portfolio",
        param_grid=conservative_param_grid,
        base_params={
            "components": ["breakout", "ma_crossover"],
            "base_weights": {"breakout": 0.5, "ma_crossover": 0.5},
            "regime_strategy": "vol_regime_filter",
        },
        description="Konservatives Regime-Aware Portfolio: Breakout + MA mit Kapitalerhalt-Fokus",
        tags=["regime_aware", "portfolio", "conservative", "breakout", "ma"],
    )
)

# Vol-Metrik-Vergleich Preset
volmetric_sweeps = get_regime_aware_volmetric_sweeps("medium")
volmetric_param_grid = {s.name: s.values for s in volmetric_sweeps}
register_predefined_sweep(
    StrategySweepConfig(
        name="regime_aware_portfolio_volmetric",
        strategy_name="regime_aware_portfolio",
        param_grid=volmetric_param_grid,
        base_params={
            "components": ["breakout", "rsi_reversion"],
            "base_weights": {"breakout": 0.5, "rsi_reversion": 0.5},
            "regime_strategy": "vol_regime_filter",
            "risk_on_scale": 1.0,
            "neutral_scale": 0.5,
            "risk_off_scale": 0.0,
            "mode": "scale",
            "signal_threshold": 0.3,
        },
        description="Vol-Metrik-Vergleich: Fixes Portfolio, variierende Vol-Metriken (ATR/STD/REALIZED/RANGE)",
        tags=["regime_aware", "portfolio", "volmetric", "comparison"],
    )
)

# Neutral-Scale Sensitivity Sweep (aus TOML config/sweeps/regime_neutral_scale_sweep.toml)
register_predefined_sweep(
    StrategySweepConfig(
        name="regime_neutral_scale_sweep",
        strategy_name="regime_aware_portfolio",
        param_grid={
            "risk_on_scale": [1.0],
            "neutral_scale": [0.50, 0.60, 0.70, 0.80, 0.90, 1.00],
            "risk_off_scale": [0.0],
            "mode": ["filter"],
        },
        base_params={
            "components": ["breakout", "rsi_reversion"],
            "base_weights": {"breakout": 0.6, "rsi_reversion": 0.4},
            "regime_strategy": "vol_regime_filter",
        },
        description="Neutral-Scale Sensitivity Sweep bei risk_off_scale = 0.0",
        tags=["regime_aware", "portfolio", "neutral_scale", "sensitivity"],
    )
)

# Regime-Threshold Robustness Sweep (aus TOML config/sweeps/regime_threshold_robustness.toml)
register_predefined_sweep(
    StrategySweepConfig(
        name="regime_threshold_robustness",
        strategy_name="regime_aware_portfolio",
        param_grid={
            "vol_metric": ["atr", "std"],
            "low_vol_threshold": [0.15, 0.18, 0.20, 0.22, 0.25],
            "high_vol_threshold": [0.30, 0.35, 0.40, 0.45],
            "risk_on_scale": [1.0],
            "neutral_scale": [0.70],
            "risk_off_scale": [0.0],
        },
        base_params={
            "components": ["breakout", "rsi_reversion"],
            "base_weights": {"breakout": 0.6, "rsi_reversion": 0.4},
            "regime_strategy": "vol_regime_filter",
        },
        description="Regime-Threshold Robustness Sweep",
        tags=["regime_aware", "portfolio", "threshold", "robustness"],
    )
)
# -----------------------------------------------------------------------------

register_predefined_sweep(
    StrategySweepConfig(
        name="vol_regime_percentile",
        strategy_name="vol_regime_filter",
        param_grid={
            "vol_window": [10, 14, 20, 30],
            "vol_percentile_low": [10, 20, 30],
            "vol_percentile_high": [70, 80, 90],
        },
        constraints=[("vol_percentile_low", "<", "vol_percentile_high")],
        description="Vol Regime Filter mit Perzentil-Grenzen",
        tags=["volatility", "filter", "regime"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="vol_regime_atr",
        strategy_name="vol_regime_filter",
        param_grid={
            "vol_window": [10, 14, 20],
            "vol_method": ["atr", "std"],
            "lookback_percentile": [50, 100, 200],
        },
        description="Vol Regime Filter mit ATR/STD-Varianten",
        tags=["volatility", "filter", "regime", "atr"],
    )
)


# -----------------------------------------------------------------------------
# Donchian Channel Sweeps
# -----------------------------------------------------------------------------

register_predefined_sweep(
    StrategySweepConfig(
        name="donchian_basic",
        strategy_name="breakout_donchian",
        param_grid={
            "entry_period": [10, 20, 55],
            "exit_period": [5, 10, 20],
        },
        constraints=[("exit_period", "<", "entry_period")],
        description="Basic Donchian Channel Sweep",
        tags=["donchian", "trend_following", "channel"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="donchian_turtle",
        strategy_name="breakout_donchian",
        param_grid={
            "entry_period": [20, 55],
            "exit_period": [10, 20],
        },
        constraints=[("exit_period", "<=", "entry_period")],
        base_params={"side": "both"},
        description="Turtle Trading inspirierte Donchian-Varianten",
        tags=["donchian", "turtle", "trend_following"],
    )
)


# -----------------------------------------------------------------------------
# Momentum Sweeps
# -----------------------------------------------------------------------------

register_predefined_sweep(
    StrategySweepConfig(
        name="momentum_basic",
        strategy_name="momentum",
        param_grid={
            "lookback": [10, 20, 30, 50],
            "threshold": [0.0, 0.01, 0.02],
        },
        description="Basic Momentum Sweep",
        tags=["momentum", "trend_following", "basic"],
    )
)


# -----------------------------------------------------------------------------
# Bollinger Bands Sweeps
# -----------------------------------------------------------------------------

register_predefined_sweep(
    StrategySweepConfig(
        name="bollinger_basic",
        strategy_name="bollinger",
        param_grid={
            "period": [10, 20, 30],
            "num_std": [1.5, 2.0, 2.5, 3.0],
        },
        description="Basic Bollinger Bands Sweep",
        tags=["bollinger", "mean_reversion", "basic"],
    )
)


# -----------------------------------------------------------------------------
# Portfolio/Composite Sweeps
# -----------------------------------------------------------------------------

register_predefined_sweep(
    StrategySweepConfig(
        name="portfolio_2strat_weights",
        strategy_name="composite",
        param_grid={
            "weight_0": [0.3, 0.4, 0.5, 0.6, 0.7],
            # weight_1 = 1 - weight_0 (implizit)
        },
        base_params={
            "aggregation": "weighted",
            "signal_threshold": 0.3,
        },
        portfolio_config={
            "components": ["ma_crossover", "rsi_reversion"],
            "description": "2-Strategy Portfolio Weight Sweep",
        },
        description="Portfolio-Sweep mit 2 Strategien und Weight-Varianten",
        tags=["portfolio", "composite", "weight_sweep"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="portfolio_3strat_equal",
        strategy_name="composite",
        param_grid={
            "signal_threshold": [0.2, 0.3, 0.4, 0.5],
            "aggregation": ["weighted", "voting", "unanimous"],
        },
        base_params={
            "weights": [0.33, 0.33, 0.34],
        },
        portfolio_config={
            "components": ["ma_crossover", "rsi_reversion", "breakout"],
            "description": "3-Strategy Equal-Weight Portfolio",
        },
        description="Portfolio-Sweep mit 3 Strategien, verschiedene Aggregationen",
        tags=["portfolio", "composite", "aggregation_sweep"],
    )
)

register_predefined_sweep(
    StrategySweepConfig(
        name="portfolio_phase40_v1",
        strategy_name="composite",
        param_grid={
            "signal_threshold": [0.25, 0.3, 0.35, 0.4],
        },
        base_params={
            "aggregation": "weighted",
            "weights": [0.4, 0.3, 0.2, 0.1],
        },
        portfolio_config={
            "components": [
                "ma_crossover",
                "breakout",
                "rsi_reversion",
                "vol_regime_filter",
            ],
            "description": "Phase 40 Portfolio: 4 Strategien mit Vol-Filter",
        },
        description="Phase 40 Multi-Strategy Portfolio Sweep",
        tags=["portfolio", "composite", "phase40"],
    )
)


# =============================================================================
# SWEEP EXECUTION HELPERS
# =============================================================================


def run_sweep_batch(
    sweep_config: StrategySweepConfig,
    data: Optional[pd.DataFrame] = None,
    backtest_fn: Optional[Callable] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    initial_capital: float = 10000.0,
    max_runs: Optional[int] = None,
    dry_run: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> ExperimentResult:
    """
    Führt einen kompletten Sweep-Batch aus.

    Dies ist die zentrale Funktion für Strategy-Sweeps in Phase 41.

    Args:
        sweep_config: StrategySweepConfig mit Sweep-Definition
        data: Optional OHLCV-DataFrame (falls None, verwendet Engine defaults)
        backtest_fn: Custom Backtest-Funktion (optional)
        start_date: Backtest-Startdatum
        end_date: Backtest-Enddatum
        initial_capital: Startkapital
        max_runs: Optional Limit für Anzahl Runs
        dry_run: Wenn True, keine Backtests, nur Parameter generieren
        progress_callback: Optional Callback für Fortschrittsanzeige

    Returns:
        ExperimentResult mit allen Sweep-Ergebnissen

    Example:
        >>> sweep = get_predefined_sweep("rsi_reversion_basic")
        >>> result = run_sweep_batch(sweep, dry_run=True)
        >>> print(f"Würde {result.config.num_combinations} Runs ausführen")
    """
    # Generiere Parameter-Kombinationen (mit Constraint-Filterung)
    combinations = sweep_config.generate_param_combinations()

    if max_runs and len(combinations) > max_runs:
        logger.info(f"Limitiere auf {max_runs} von {len(combinations)} Kombinationen")
        combinations = combinations[:max_runs]

    # Erstelle ExperimentConfig
    exp_config = sweep_config.to_experiment_config(
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
    )

    # Runner erstellen
    runner = ExperimentRunner(
        backtest_fn=backtest_fn,
        progress_callback=progress_callback,
    )

    logger.info(
        f"Starte Sweep '{sweep_config.name}' mit {len(combinations)} Kombinationen "
        f"(von {sweep_config.num_raw_combinations} vor Constraint-Filter)"
    )

    # Ausführen
    return runner.run(exp_config, dry_run=dry_run)


def create_custom_sweep(
    name: str,
    strategy_name: str,
    param_grid: Dict[str, List[Any]],
    constraints: Optional[List[Tuple[str, str, Any]]] = None,
    **kwargs: Any,
) -> StrategySweepConfig:
    """
    Convenience-Funktion zum Erstellen eines Custom-Sweeps.

    Args:
        name: Name des Sweeps
        strategy_name: Name der Strategie
        param_grid: Parameter-Grid
        constraints: Optional Constraints als Tupel-Liste
        **kwargs: Weitere Argumente für StrategySweepConfig

    Returns:
        StrategySweepConfig

    Example:
        >>> sweep = create_custom_sweep(
        ...     name="my_custom_sweep",
        ...     strategy_name="ma_crossover",
        ...     param_grid={"fast_period": [5, 10], "slow_period": [50, 100]},
        ...     constraints=[("fast_period", "<", "slow_period")],
        ... )
    """
    return StrategySweepConfig(
        name=name,
        strategy_name=strategy_name,
        param_grid=param_grid,
        constraints=constraints or [],
        **kwargs,
    )


# =============================================================================
# SWEEP CATALOG / DISCOVERY
# =============================================================================


def get_sweeps_for_strategy(strategy_name: str) -> List[StrategySweepConfig]:
    """
    Gibt alle vordefinierten Sweeps für eine Strategie zurück.

    Args:
        strategy_name: Name der Strategie

    Returns:
        Liste von StrategySweepConfig
    """
    return [
        sweep
        for sweep in _PREDEFINED_SWEEPS.values()
        if sweep.strategy_name == strategy_name
    ]


def get_sweeps_by_tag(tag: str) -> List[StrategySweepConfig]:
    """
    Gibt alle Sweeps mit einem bestimmten Tag zurück.

    Args:
        tag: Tag zum Filtern

    Returns:
        Liste von StrategySweepConfig
    """
    return [
        sweep for sweep in _PREDEFINED_SWEEPS.values() if tag in sweep.tags
    ]


def print_sweep_catalog() -> str:
    """
    Gibt einen formatierten Katalog aller vordefinierten Sweeps zurück.

    Returns:
        Formatierter String mit Sweep-Übersicht
    """
    lines = [
        "=" * 70,
        "Peak_Trade Strategy Sweep Catalog (Phase 41)",
        "=" * 70,
        "",
    ]

    # Nach Strategie gruppieren
    by_strategy: Dict[str, List[StrategySweepConfig]] = {}
    for sweep in _PREDEFINED_SWEEPS.values():
        strategy = sweep.strategy_name
        if strategy not in by_strategy:
            by_strategy[strategy] = []
        by_strategy[strategy].append(sweep)

    for strategy in sorted(by_strategy.keys()):
        lines.append(f"\n### {strategy.upper()}")
        lines.append("-" * 40)

        for sweep in by_strategy[strategy]:
            raw = sweep.num_raw_combinations
            valid = sweep.num_combinations
            constraint_note = f" ({valid}/{raw} nach Constraints)" if raw != valid else ""

            lines.append(f"  {sweep.name}")
            lines.append(f"    Kombinationen: {valid}{constraint_note}")
            if sweep.description:
                lines.append(f"    {sweep.description}")
            lines.append("")

    lines.append("=" * 70)
    lines.append(f"Gesamt: {len(_PREDEFINED_SWEEPS)} vordefinierte Sweeps")

    return "\n".join(lines)
