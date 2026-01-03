#!/usr/bin/env python3
"""
Peak_Trade Optuna Study Runner
===============================
Vollständige Optuna-Integration für hyperparameter optimization.

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
import sys
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Peak_Trade imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtest.engine import BacktestEngine
from src.core.peak_config import load_config
from src.core.tracking import build_tracker_from_config
from src.strategies import get_strategy

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


def create_sampler(sampler_type: str, seed: Optional[int] = None) -> Any:
    """Create Optuna Sampler."""
    if sampler_type == "tpe":
        return TPESampler(seed=seed)
    elif sampler_type == "random":
        return RandomSampler(seed=seed)
    elif sampler_type == "grid":
        return GridSampler(seed=seed)
    else:
        raise ValueError(f"Unknown sampler type: {sampler_type}")


def suggest_params_from_schema(trial: Trial, strategy: Any) -> Dict[str, Any]:
    """
    Extract parameter suggestions from strategy's parameter_schema.

    Args:
        trial: Optuna Trial
        strategy: Strategy instance with parameter_schema property

    Returns:
        Dict of suggested parameters
    """
    schema = strategy.parameter_schema
    if not schema:
        raise ValueError(
            f"Strategy {strategy.__class__.__name__} has no parameter_schema. "
            "Cannot optimize parameters."
        )

    params = {}
    for param in schema:
        # Use built-in to_optuna_suggest() method from Param class
        value = param.to_optuna_suggest(trial)
        params[param.name] = value

    return params


def run_backtest_trial(
    cfg: Any,
    strategy_cls: type,
    trial_params: Dict[str, Any],
    trial: Optional[Trial] = None,
) -> Dict[str, float]:
    """
    Run a single backtest trial with given parameters.

    Args:
        cfg: Peak config
        strategy_cls: Strategy class
        trial_params: Parameters for this trial
        trial: Optional Optuna Trial for intermediate reporting

    Returns:
        Dict of metrics (sharpe, total_return, max_drawdown, win_rate, etc.)
    """
    # Build strategy with trial params
    strategy = strategy_cls(**trial_params)

    # Build tracker (optional, for MLflow logging)
    tracker = build_tracker_from_config(cfg)

    # Build backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        config=cfg,
        tracker=tracker,
    )

    # Run backtest
    result = engine.run_realistic()

    # Extract metrics
    stats = result.get("stats", {})
    metrics = {
        "sharpe": stats.get("sharpe", 0.0),
        "total_return": stats.get("total_return", 0.0),
        "max_drawdown": abs(stats.get("max_drawdown", 0.0)),  # always positive
        "win_rate": stats.get("win_rate", 0.0),
        "num_trades": stats.get("num_trades", 0),
        "profit_factor": stats.get("profit_factor", 0.0),
    }

    # Report intermediate values for pruning (if supported)
    if trial is not None and hasattr(trial, "report"):
        # Report primary metric (sharpe) at the "end" of the trial
        trial.report(metrics["sharpe"], step=0)

        # Check if should prune
        if trial.should_prune():
            raise optuna.TrialPruned()

    return metrics


def objective_single(
    trial: Trial,
    study_cfg: StudyConfig,
    cfg: Any,
    strategy_cls: type,
    objective_name: str,
) -> float:
    """
    Optuna objective function for single-objective optimization.

    Args:
        trial: Optuna Trial
        study_cfg: Study configuration
        cfg: Peak config
        strategy_cls: Strategy class
        objective_name: Metric to optimize (e.g., "sharpe")

    Returns:
        Objective value (higher is better for maximize)
    """
    # Suggest parameters from schema
    trial_params = suggest_params_from_schema(trial, strategy_cls())

    # Log parameters to trial
    for k, v in trial_params.items():
        trial.set_user_attr(f"param_{k}", v)

    # Run backtest
    try:
        metrics = run_backtest_trial(cfg, strategy_cls, trial_params, trial)
    except Exception as e:
        logger.error(f"Trial {trial.number} failed: {e}")
        # Return worst possible value
        if study_cfg.direction == "maximize":
            return float("-inf")
        else:
            return float("inf")

    # Log all metrics as user attributes
    for metric_name, metric_value in metrics.items():
        trial.set_user_attr(metric_name, metric_value)

    # Return target objective
    objective_value = metrics.get(objective_name, 0.0)

    # For max_drawdown, we want to minimize (smaller drawdown = better)
    # But metrics stores it as positive value, so negate for maximization
    if objective_name == "max_drawdown":
        objective_value = -objective_value

    return objective_value


def objective_multi(
    trial: Trial,
    study_cfg: StudyConfig,
    cfg: Any,
    strategy_cls: type,
    objective_names: List[str],
) -> tuple:
    """
    Optuna objective function for multi-objective optimization.

    Args:
        trial: Optuna Trial
        study_cfg: Study configuration
        cfg: Peak config
        strategy_cls: Strategy class
        objective_names: List of metrics to optimize

    Returns:
        Tuple of objective values
    """
    # Suggest parameters from schema
    trial_params = suggest_params_from_schema(trial, strategy_cls())

    # Log parameters
    for k, v in trial_params.items():
        trial.set_user_attr(f"param_{k}", v)

    # Run backtest
    try:
        metrics = run_backtest_trial(cfg, strategy_cls, trial_params, trial)
    except Exception as e:
        logger.error(f"Trial {trial.number} failed: {e}")
        # Return worst possible values for all objectives
        return tuple([float("-inf")] * len(objective_names))

    # Log all metrics
    for metric_name, metric_value in metrics.items():
        trial.set_user_attr(metric_name, metric_value)

    # Return tuple of objectives
    values = []
    for obj_name in objective_names:
        value = metrics.get(obj_name, 0.0)

        # For max_drawdown, negate to maximize (minimize drawdown = maximize -drawdown)
        if obj_name == "max_drawdown":
            value = -value

        values.append(value)

    return tuple(values)


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

    # Get strategy class
    logger.info(f"Loading strategy: {study_cfg.strategy_name}")
    strategy_cls = get_strategy(study_cfg.strategy_name)

    # Verify strategy has parameter_schema
    dummy_strategy = strategy_cls()
    schema = dummy_strategy.parameter_schema
    if not schema:
        logger.error(
            f"Strategy {study_cfg.strategy_name} has no parameter_schema. Cannot run optimization."
        )
        sys.exit(1)

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
    sampler = create_sampler(study_cfg.sampler_type, seed=42)

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
                trial, study_cfg, cfg, strategy_cls, study_cfg.objectives
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
            lambda trial: objective_single(trial, study_cfg, cfg, strategy_cls, objective_name),
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
        description="Optuna-based Strategy Optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
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
