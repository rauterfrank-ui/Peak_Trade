#!/usr/bin/env python3
"""
Peak_Trade Optuna Study Runner
===============================
Vollständige Optuna-Integration für hyperparameter optimization.

Nicht der J2-Placeholder: für den minimalen Toy-/Demo-Pfad siehe
``scripts/run_study_optuna_placeholder.py`` (Dry-Run default, kein Strategy-Backtest).

**Features**:
- Parameter-Schema → Optuna Search Space
- Single/Multi-Objective Optimization
- Pruning Support (Median, Hyperband)
- MLflow Integration für Trial Tracking
- Parallel Trials Support
- Storage Backend (SQLite, PostgreSQL)

**Usage**:
    # Basic optimization
    python scripts/run_optuna_study.py \\
        --strategy ma_crossover \\
        --n-trials 100

    # Multi-objective (Sharpe + Drawdown)
    python scripts/run_optuna_study.py \\
        --strategy ma_crossover \\
        --objectives sharpe,max_drawdown \\
        --n-trials 200

    # With persistent storage
    python scripts/run_optuna_study.py \\
        --strategy rsi_reversion \\
        --storage sqlite:///optuna_studies.db \\
        --study-name rsi_opt_v1 \\
        --n-trials 50

    # Parallel trials
    python scripts/run_optuna_study.py \\
        --strategy breakout_donchian \\
        --n-trials 100 \\
        --jobs 4

**See**: docs/STRATEGY_LAYER_VNEXT_PHASE2_REPORT.md
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

# Peak_Trade imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_backtest import _build_strategy_params_from_config, load_ohlcv_data
from src.backtest.engine import BacktestEngine
from src.backtest.result import BacktestResult
from src.core.peak_config import load_config
from src.core.tracking import build_tracker_from_config
from src.strategies import load_strategy
from src.strategies.parameters import Param
from src.strategies.registry import get_strategy_spec

# Optuna (lazy import with graceful error)
try:
    import optuna
    from optuna.pruners import MedianPruner, HyperbandPruner, NopPruner
    from optuna.samplers import TPESampler, RandomSampler, GridSampler
    from optuna.trial import Trial, TrialState

    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    optuna = None
    Trial = Any

logger = logging.getLogger(__name__)

_STOP_PCT_RANGE_GT_EXCLUSIVE = 0.0
_STOP_PCT_RANGE_LE_INCLUSIVE = 0.10


class ObjectiveMetricError(ValueError):
    """Fail-closed rejection for missing or invalid objective metrics."""


def _validate_stop_pct_value(value: Any) -> float:
    if value is None:
        raise ValueError("stop_pct value is None")
    if isinstance(value, bool):
        raise ValueError("bool is not a valid numeric stop_pct")
    if not isinstance(value, (int, float)):
        raise ValueError(f"non-numeric stop_pct: {type(value).__name__}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite stop_pct: {result!r}")
    if not (result > _STOP_PCT_RANGE_GT_EXCLUSIVE and result <= _STOP_PCT_RANGE_LE_INCLUSIVE):
        raise ValueError(
            f"stop_pct {result!r} outside canonical range "
            f"({_STOP_PCT_RANGE_GT_EXCLUSIVE}, {_STOP_PCT_RANGE_LE_INCLUSIVE}]"
        )
    return result


def _bind_engine_strategy_params(
    cfg: Any,
    strategy_key: str,
    trial_params: Dict[str, Any],
) -> Dict[str, Any]:
    if "stop_pct" in trial_params:
        raise ValueError("stop_pct must not be a trial search parameter")
    stop_pct = _validate_stop_pct_value(
        _build_strategy_params_from_config(cfg, strategy_key)["stop_pct"]
    )
    return {**trial_params, "stop_pct": stop_pct}


def _extract_objective_metric(stats: Dict[str, Any], objective_name: str) -> float:
    if objective_name not in stats:
        raise ObjectiveMetricError(f"missing metric: {objective_name!r}")
    raw = stats[objective_name]
    if raw is None:
        raise ObjectiveMetricError("metric value is None")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ObjectiveMetricError(f"non-numeric metric: {type(raw).__name__}")
    value = float(raw)
    if not math.isfinite(value):
        raise ObjectiveMetricError(f"non-finite metric: {value!r}")
    if objective_name == "max_drawdown":
        value = -abs(value)
    return value


@dataclass
class StudyConfig:
    """Configuration for Optuna Study."""

    strategy_name: str
    config_path: Path
    n_trials: int
    study_name: Optional[str]
    objectives: List[str]
    storage: Optional[str]
    pruner_type: str
    sampler_type: str
    timeout: Optional[int]
    n_jobs: int
    load_if_exists: bool = True
    direction: Optional[str] = None  # "maximize" | "minimize" for single objective


def check_optuna_available() -> None:
    """Raise helpful error if Optuna not installed."""
    if not OPTUNA_AVAILABLE:
        print("❌ Optuna is not installed.")
        print()
        print("Installation:")
        print("  pip install optuna")
        print("  # or with uv:")
        print("  uv pip install optuna")
        print()
        print("Optional: Install with visualization support:")
        print("  pip install optuna[visualization]")
        print()
        sys.exit(1)


def _grid_search_space_from_schema(schema: List[Param]) -> Dict[str, List[Any]]:
    """
    Build a finite discrete search space for GridSampler from strategy parameter_schema.

    Uses up to three values per numeric parameter (low / mid / high) to keep the grid tractable.
    """
    space: Dict[str, List[Any]] = {}
    for p in schema:
        if p.kind == "int":
            lo, hi = int(p.low), int(p.high)
            if lo == hi:
                space[p.name] = [lo]
            else:
                mid = (lo + hi) // 2
                space[p.name] = sorted({lo, mid, hi})
        elif p.kind == "float":
            lo_f, hi_f = float(p.low), float(p.high)
            if lo_f == hi_f:
                space[p.name] = [lo_f]
            else:
                mid_f = (lo_f + hi_f) / 2.0
                space[p.name] = [lo_f, mid_f, hi_f]
        elif p.kind == "choice":
            space[p.name] = list(p.choices or [])
        elif p.kind == "bool":
            space[p.name] = [False, True]
    return space


def create_pruner(pruner_type: str) -> Any:
    """Create Optuna Pruner."""
    if pruner_type == "none":
        return NopPruner()
    elif pruner_type == "median":
        return MedianPruner(n_startup_trials=5, n_warmup_steps=10)
    elif pruner_type == "hyperband":
        return HyperbandPruner()
    else:
        raise ValueError(f"Unknown pruner type: {pruner_type}")


def create_sampler(
    sampler_type: str,
    seed: Optional[int] = None,
    *,
    grid_search_space: Optional[Dict[str, List[Any]]] = None,
) -> Any:
    """Create Optuna Sampler.

    Optuna 3.6+ requires ``search_space`` for :class:`optuna.samplers.GridSampler`.
    For ``grid``, pass ``grid_search_space`` from ``_grid_search_space_from_schema`` when
    running a real study; tests may omit it (minimal placeholder space).
    """
    if sampler_type == "tpe":
        return TPESampler(seed=seed)
    elif sampler_type == "random":
        return RandomSampler(seed=seed)
    elif sampler_type == "grid":
        if grid_search_space is None:
            grid_search_space = {"_optuna_grid_placeholder": [0.0, 1.0]}
        return GridSampler(grid_search_space, seed=seed)
    else:
        raise ValueError(f"Unknown sampler type: {sampler_type}")


def suggest_params_from_schema(trial: Trial, schema: List[Param]) -> Dict[str, Any]:
    """
    Extract parameter suggestions from a strategy parameter_schema.

    Args:
        trial: Optuna Trial
        schema: Strategy parameter_schema entries

    Returns:
        Dict of suggested parameters
    """
    if not schema:
        raise ValueError("Strategy has no parameter_schema. Cannot optimize parameters.")

    params = {}
    for param in schema:
        value = param.to_optuna_suggest(trial)
        params[param.name] = value

    return params


def run_backtest_trial(
    df: pd.DataFrame,
    cfg: Any,
    strategy_key: str,
    strategy_signal_fn: Callable[[pd.DataFrame, Dict[str, Any]], pd.Series],
    trial_params: Dict[str, Any],
    trial: Optional[Trial] = None,
) -> BacktestResult:
    """
    Run a single backtest trial with given parameters.

    Args:
        df: OHLCV DataFrame (reused by reference across trials)
        cfg: Peak config
        strategy_key: Strategy registry key
        strategy_signal_fn: Functional signal adapter from load_strategy()
        trial_params: Parameters for this trial
        trial: Optional Optuna Trial for intermediate reporting

    Returns:
        BacktestResult with stats for objective extraction
    """
    strategy_params = _bind_engine_strategy_params(cfg, strategy_key, trial_params)
    tracker = build_tracker_from_config(cfg)
    engine = BacktestEngine(tracker=tracker)
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_signal_fn,
        strategy_params=strategy_params,
    )

    if trial is not None and hasattr(trial, "report"):
        sharpe_value = _extract_objective_metric(result.stats, "sharpe")
        trial.report(sharpe_value, step=0)
        if trial.should_prune():
            raise optuna.TrialPruned()

    return result


def objective_single(
    trial: Trial,
    study_cfg: StudyConfig,
    cfg: Any,
    df: pd.DataFrame,
    strategy_key: str,
    strategy_signal_fn: Callable[[pd.DataFrame, Dict[str, Any]], pd.Series],
    schema: List[Param],
    objective_name: str,
) -> float:
    """
    Optuna objective function for single-objective optimization.

    Args:
        trial: Optuna Trial
        study_cfg: Study configuration
        cfg: Peak config
        df: Shared OHLCV DataFrame
        strategy_key: Strategy registry key
        strategy_signal_fn: Functional signal adapter
        schema: Strategy parameter_schema
        objective_name: Metric to optimize (e.g., "sharpe")

    Returns:
        Objective value (higher is better for maximize)
    """
    trial_params = suggest_params_from_schema(trial, schema)

    for k, v in trial_params.items():
        trial.set_user_attr(f"param_{k}", v)

    result = run_backtest_trial(
        df=df,
        cfg=cfg,
        strategy_key=strategy_key,
        strategy_signal_fn=strategy_signal_fn,
        trial_params=trial_params,
        trial=trial,
    )

    for metric_name, metric_value in result.stats.items():
        trial.set_user_attr(metric_name, metric_value)

    return _extract_objective_metric(result.stats, objective_name)


def objective_multi(
    trial: Trial,
    study_cfg: StudyConfig,
    cfg: Any,
    df: pd.DataFrame,
    strategy_key: str,
    strategy_signal_fn: Callable[[pd.DataFrame, Dict[str, Any]], pd.Series],
    schema: List[Param],
    objective_names: List[str],
) -> tuple:
    """
    Optuna objective function for multi-objective optimization.

    Args:
        trial: Optuna Trial
        study_cfg: Study configuration
        cfg: Peak config
        df: Shared OHLCV DataFrame
        strategy_key: Strategy registry key
        strategy_signal_fn: Functional signal adapter
        schema: Strategy parameter_schema
        objective_names: List of metrics to optimize

    Returns:
        Tuple of objective values
    """
    trial_params = suggest_params_from_schema(trial, schema)

    for k, v in trial_params.items():
        trial.set_user_attr(f"param_{k}", v)

    result = run_backtest_trial(
        df=df,
        cfg=cfg,
        strategy_key=strategy_key,
        strategy_signal_fn=strategy_signal_fn,
        trial_params=trial_params,
        trial=trial,
    )

    for metric_name, metric_value in result.stats.items():
        trial.set_user_attr(metric_name, metric_value)

    return tuple(_extract_objective_metric(result.stats, obj_name) for obj_name in objective_names)


def run_study(study_cfg: StudyConfig) -> None:
    """
    Run Optuna Study.

    Args:
        study_cfg: Study configuration
    """
    check_optuna_available()

    # Load Peak config
    logger.info(f"Loading config from {study_cfg.config_path}")
    cfg = load_config(str(study_cfg.config_path))

    strategy_key = study_cfg.strategy_name
    logger.info(f"Loading strategy: {strategy_key}")
    strategy_spec = get_strategy_spec(strategy_key)
    schema = strategy_spec.cls.parameter_schema
    if not schema:
        logger.error(f"Strategy {strategy_key} has no parameter_schema. Cannot run optimization.")
        sys.exit(1)

    strategy_signal_fn = load_strategy(strategy_key)

    logger.info("Loading OHLCV data (once per study)")
    df = load_ohlcv_data(
        data_file=cfg.get("backtest.data_file"),
        start_date=cfg.get("backtest.start_date"),
        end_date=cfg.get("backtest.end_date"),
        n_bars=cfg.get("backtest.bars", 500),
    )
    logger.info(f"  {len(df)} bars loaded")

    logger.info(f"Parameter schema: {len(schema)} parameters")
    for param in schema:
        logger.info(f"  - {param.name} ({param.kind}): {param.low} - {param.high}")

    # Determine study name
    study_name = (
        study_cfg.study_name
        or f"{study_cfg.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    logger.info(f"Study name: {study_name}")

    # Create pruner and sampler
    pruner = create_pruner(study_cfg.pruner_type)
    grid_space: Optional[Dict[str, List[Any]]] = None
    if study_cfg.sampler_type == "grid":
        grid_space = _grid_search_space_from_schema(schema)
    sampler = create_sampler(study_cfg.sampler_type, seed=42, grid_search_space=grid_space)

    # Determine if single or multi-objective
    is_multi_objective = len(study_cfg.objectives) > 1

    if is_multi_objective:
        logger.info(f"Multi-objective optimization: {study_cfg.objectives}")
        # Multi-objective: always maximize all (we negate drawdown internally)
        directions = ["maximize"] * len(study_cfg.objectives)

        study = optuna.create_study(
            study_name=study_name,
            storage=study_cfg.storage,
            load_if_exists=study_cfg.load_if_exists,
            directions=directions,
            pruner=pruner,
            sampler=sampler,
        )

        # Run optimization
        study.optimize(
            lambda trial: objective_multi(
                trial,
                study_cfg,
                cfg,
                df,
                strategy_key,
                strategy_signal_fn,
                schema,
                study_cfg.objectives,
            ),
            n_trials=study_cfg.n_trials,
            timeout=study_cfg.timeout,
            n_jobs=study_cfg.n_jobs,
            show_progress_bar=True,
        )

        # Print best trials (Pareto front)
        logger.info("=" * 80)
        logger.info("Best Trials (Pareto Front):")
        logger.info("=" * 80)

        best_trials = study.best_trials
        for i, trial in enumerate(best_trials[:10], 1):  # Top 10
            logger.info(f"\nTrial #{trial.number} (Rank {i}):")
            logger.info(f"  Objectives: {trial.values}")
            logger.info("  Parameters:")
            for key, value in trial.params.items():
                logger.info(f"    {key}: {value}")

    else:
        # Single-objective
        objective_name = study_cfg.objectives[0]
        logger.info(f"Single-objective optimization: {objective_name}")

        # Determine direction
        direction = study_cfg.direction or "maximize"
        if objective_name == "max_drawdown":
            direction = "maximize"  # We maximize -drawdown (minimize drawdown)

        study = optuna.create_study(
            study_name=study_name,
            storage=study_cfg.storage,
            load_if_exists=study_cfg.load_if_exists,
            direction=direction,
            pruner=pruner,
            sampler=sampler,
        )

        # Run optimization
        study.optimize(
            lambda trial: objective_single(
                trial,
                study_cfg,
                cfg,
                df,
                strategy_key,
                strategy_signal_fn,
                schema,
                objective_name,
            ),
            n_trials=study_cfg.n_trials,
            timeout=study_cfg.timeout,
            n_jobs=study_cfg.n_jobs,
            show_progress_bar=True,
        )

        # Print best trial
        logger.info("=" * 80)
        logger.info("Best Trial:")
        logger.info("=" * 80)
        logger.info(f"  Trial number: {study.best_trial.number}")
        logger.info(f"  Objective value: {study.best_value:.4f}")
        logger.info("  Parameters:")
        for key, value in study.best_params.items():
            logger.info(f"    {key}: {value}")
        logger.info("  All metrics:")
        for key, value in study.best_trial.user_attrs.items():
            if not key.startswith("param_"):
                logger.info(f"    {key}: {value:.4f}")

    # Save study stats
    logger.info("=" * 80)
    logger.info("Study Statistics:")
    logger.info("=" * 80)
    logger.info(f"  Total trials: {len(study.trials)}")
    logger.info(f"  Completed: {len([t for t in study.trials if t.state == TrialState.COMPLETE])}")
    logger.info(f"  Pruned: {len([t for t in study.trials if t.state == TrialState.PRUNED])}")
    logger.info(f"  Failed: {len([t for t in study.trials if t.state == TrialState.FAIL])}")

    # Export results
    results_dir = Path("reports/optuna_studies")
    results_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / f"{study_name}.csv"
    df = study.trials_dataframe()
    df.to_csv(csv_path, index=False)
    logger.info(f"\n✅ Results exported to: {csv_path}")

    # Optionally: visualization (if optuna[visualization] installed)
    try:
        from optuna.visualization import plot_optimization_history, plot_param_importances

        viz_dir = results_dir / f"{study_name}_viz"
        viz_dir.mkdir(exist_ok=True)

        # Optimization history
        fig = plot_optimization_history(study)
        fig.write_html(str(viz_dir / "history.html"))

        # Parameter importances (only for single-objective)
        if not is_multi_objective:
            fig = plot_param_importances(study)
            fig.write_html(str(viz_dir / "param_importances.html"))

        logger.info(f"✅ Visualizations saved to: {viz_dir}")
    except ImportError:
        logger.info("ℹ️  Install optuna[visualization] for automatic plots")


def parse_args() -> StudyConfig:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Full Optuna study runner: strategy parameter_schema → search space, "
            "BacktestEngine-backed trials (config-driven).\n\n"
            "Not the J2 placeholder — for the minimal toy/demo CLI (dry-run default, "
            "no strategy backtests) use scripts/run_study_optuna_placeholder.py.\n\n"
            "NO-LIVE: trials evaluate via backtest/historical paths only; no live order execution."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scope:
  This entrypoint runs real optimization loops against the strategy registry and
  backtests. The J2 slice is intentionally separate:
    scripts/run_study_optuna_placeholder.py

Examples:
  # Basic single-objective (Sharpe)
  %(prog)s --strategy ma_crossover --n-trials 100

  # Multi-objective (Sharpe + Drawdown)
  %(prog)s --strategy ma_crossover --objectives sharpe,max_drawdown --n-trials 200

  # Persistent storage
  %(prog)s --strategy rsi_reversion --storage sqlite:///optuna.db --study-name rsi_v1 --n-trials 50

  # Parallel trials
  %(prog)s --strategy breakout_donchian --n-trials 100 --jobs 4

See: docs/STRATEGY_LAYER_VNEXT_PHASE2_REPORT.md
        """,
    )

    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        help="Strategy name (e.g., ma_crossover, rsi_reversion)",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Path to config.toml (default: config.toml)",
    )

    parser.add_argument(
        "--n-trials",
        type=int,
        default=100,
        help="Number of Optuna trials (default: 100)",
    )

    parser.add_argument(
        "--study-name",
        type=str,
        default=None,
        help="Study name (default: auto-generated)",
    )

    parser.add_argument(
        "--objectives",
        type=str,
        default="sharpe",
        help="Optimization objectives (comma-separated, e.g., 'sharpe,max_drawdown')",
    )

    parser.add_argument(
        "--storage",
        type=str,
        default=None,
        help="Storage URI (e.g., sqlite:///optuna.db, default: in-memory)",
    )

    parser.add_argument(
        "--pruner",
        type=str,
        default="median",
        choices=["median", "none", "hyperband"],
        help="Optuna pruner (default: median)",
    )

    parser.add_argument(
        "--sampler",
        type=str,
        default="tpe",
        choices=["tpe", "random", "grid"],
        help="Optuna sampler (default: tpe)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (default: no timeout)",
    )

    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Number of parallel jobs (default: 1)",
    )

    parser.add_argument(
        "--direction",
        type=str,
        default=None,
        choices=["maximize", "minimize"],
        help="Optimization direction (default: auto)",
    )

    parser.add_argument(
        "--no-load-if-exists",
        action="store_true",
        help="Don't load existing study, create new one",
    )

    args = parser.parse_args()

    # Parse objectives
    objectives = [obj.strip() for obj in args.objectives.split(",")]

    return StudyConfig(
        strategy_name=args.strategy,
        config_path=Path(args.config),
        n_trials=args.n_trials,
        study_name=args.study_name,
        objectives=objectives,
        storage=args.storage,
        pruner_type=args.pruner,
        sampler_type=args.sampler,
        timeout=args.timeout,
        n_jobs=args.jobs,
        load_if_exists=not args.no_load_if_exists,
        direction=args.direction,
    )


def main():
    """Entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Parse args
    study_cfg = parse_args()

    # Run study
    try:
        run_study(study_cfg)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Study interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Study failed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("\n✅ Study completed successfully")


if __name__ == "__main__":
    main()
