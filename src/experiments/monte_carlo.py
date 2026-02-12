# src/experiments/monte_carlo.py
"""
Peak_Trade Monte-Carlo Robustness (Phase 45)
============================================

Monte-Carlo-Simulationen auf Basis vorhandener Backtest-Ergebnisse.

Features:
- Simple Bootstrap (i.i.d. Resampling)
- Block-Bootstrap (erhält Autokorrelation)
- Konfidenzintervalle für Kennzahlen (Sharpe, CAGR, Max-Drawdown, etc.)
- Integration mit Experiment-Registry

Usage:
    from src.experiments.monte_carlo import (
        MonteCarloConfig,
        run_monte_carlo_from_returns,
        run_monte_carlo_for_experiment,
    )

    config = MonteCarloConfig(num_runs=1000, method="simple")
    summary = run_monte_carlo_from_returns(returns, config)
    print(f"Sharpe p50: {summary.metric_quantiles['sharpe']['p50']:.2f}")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Literal, Optional

import numpy as np
import pandas as pd

from ..backtest import stats as stats_mod
from .equity_loader import equity_to_returns, load_equity_curves_from_run_dir

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class MonteCarloConfig:
    """
    Konfiguration für Monte-Carlo-Simulationen.

    Attributes:
        num_runs: Anzahl der Monte-Carlo-Runs (default: 1000)
        method: Bootstrap-Methode ("simple" oder "block_bootstrap")
        block_size: Blockgröße für Block-Bootstrap (nur relevant für block_bootstrap)
        seed: Random Seed für Reproduzierbarkeit (default: 42)
    """

    num_runs: int = 1000
    method: Literal["simple", "block_bootstrap"] = "simple"
    block_size: int = 20
    seed: Optional[int] = 42

    def __post_init__(self) -> None:
        """Validiert Konfiguration."""
        if self.num_runs < 1:
            raise ValueError(f"num_runs muss >= 1 sein, got {self.num_runs}")
        if self.method == "block_bootstrap" and self.block_size < 1:
            raise ValueError(f"block_size muss >= 1 sein, got {self.block_size}")


# =============================================================================
# RESULT OBJECTS
# =============================================================================


@dataclass
class MonteCarloRunResult:
    """
    Ergebnis eines einzelnen Monte-Carlo-Runs.

    Attributes:
        run_index: Index des Runs (0-basiert)
        metrics: Dict mit Metriken (z.B. {"cagr": 0.15, "sharpe": 1.5, ...})
    """

    run_index: int
    metrics: Dict[str, float]


@dataclass
class MonteCarloSummaryResult:
    """
    Zusammenfassung aller Monte-Carlo-Runs.

    Attributes:
        config: Verwendete MonteCarloConfig
        metric_distributions: Dict mit Metrik-Namen -> pd.Series der Werte über alle Runs
        metric_quantiles: Dict mit Metrik-Namen -> Dict mit Quantilen (p5, p50, p95)
        num_runs: Anzahl durchgeführter Runs
    """

    config: MonteCarloConfig
    metric_distributions: Dict[str, pd.Series]
    metric_quantiles: Dict[str, Dict[str, float]]
    num_runs: int


# =============================================================================
# BOOTSTRAP FUNCTIONS
# =============================================================================


def _simple_bootstrap(returns: pd.Series, n_samples: int, rng: np.random.Generator) -> pd.Series:
    """
    Einfacher i.i.d. Bootstrap (Resampling mit Replacement).

    Args:
        returns: Original-Returns
        n_samples: Anzahl zu generierender Samples
        rng: NumPy Random Generator

    Returns:
        Resampled Returns-Serie
    """
    indices = rng.integers(0, len(returns), size=n_samples)
    return returns.iloc[indices].reset_index(drop=True)


def _block_bootstrap(
    returns: pd.Series, n_samples: int, block_size: int, rng: np.random.Generator
) -> pd.Series:
    """
    Block-Bootstrap (erhält Autokorrelation).

    Args:
        returns: Original-Returns
        n_samples: Anzahl zu generierender Samples
        block_size: Größe der Blöcke
        rng: NumPy Random Generator

    Returns:
        Resampled Returns-Serie
    """
    n_blocks = (n_samples + block_size - 1) // block_size  # Aufrunden
    max_start_idx = len(returns) - block_size + 1

    if max_start_idx <= 0:
        # Fallback zu simple bootstrap wenn Block zu groß
        return _simple_bootstrap(returns, n_samples, rng)

    blocks: List[pd.Series] = []
    for _ in range(n_blocks):
        start_idx = rng.integers(0, max_start_idx)
        block = returns.iloc[start_idx : start_idx + block_size]
        blocks.append(block)

    # Kombiniere Blöcke und schneide auf n_samples
    combined = pd.concat(blocks, ignore_index=True)
    return combined.iloc[:n_samples].reset_index(drop=True)


# =============================================================================
# CORE MONTE-CARLO FUNCTION
# =============================================================================


def run_monte_carlo_from_returns(
    returns: pd.Series,
    config: MonteCarloConfig,
    *,
    stats_fn: Optional[Callable[[pd.Series], Dict[str, float]]] = None,
) -> MonteCarloSummaryResult:
    """
    Führt Monte-Carlo-Simulationen auf einer Serie von Returns durch.

    Args:
        returns: Serie von Perioden-Returns (z.B. tägliche log-Returns oder einfache Returns)
        config: Monte-Carlo-Konfiguration
        stats_fn: Funktion, die aus einer simulierten Return-Serie Kennzahlen berechnet.
                  Default: Wrapper um compute_basic_stats aus src.backtest.stats

    Returns:
        MonteCarloSummaryResult mit Verteilungen + Quantilen der Metriken

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.015, ...])
        >>> config = MonteCarloConfig(num_runs=100, method="simple")
        >>> summary = run_monte_carlo_from_returns(returns, config)
        >>> print(summary.metric_quantiles["sharpe"]["p50"])
    """
    if len(returns) < 2:
        raise ValueError(f"Returns-Serie muss mindestens 2 Werte haben, got {len(returns)}")

    # Default stats_fn: Wrapper um compute_basic_stats
    if stats_fn is None:

        def stats_fn(returns_series: pd.Series) -> Dict[str, float]:
            # Konvertiere Returns zu Equity-Curve für compute_basic_stats
            equity = (1 + returns_series).cumprod() * 10000  # Startkapital = 10000
            stats = stats_mod.compute_basic_stats(equity)
            # Füge zusätzliche Metriken hinzu
            if len(returns_series) > 0:
                stats["volatility"] = float(returns_series.std() * np.sqrt(252))  # Annualisiert
                stats["mean_return"] = float(returns_series.mean() * 252)  # Annualisiert
            return stats

    # Initialisiere Random Generator
    rng = np.random.default_rng(config.seed)

    # Führe Monte-Carlo-Runs durch
    all_metrics: Dict[str, List[float]] = {}
    run_results: List[MonteCarloRunResult] = []

    logger.info(f"Starte {config.num_runs} Monte-Carlo-Runs (Methode: {config.method})")

    for run_idx in range(config.num_runs):
        # Bootstrap Returns
        if config.method == "simple":
            simulated_returns = _simple_bootstrap(returns, len(returns), rng)
        elif config.method == "block_bootstrap":
            simulated_returns = _block_bootstrap(returns, len(returns), config.block_size, rng)
        else:
            raise ValueError(f"Unbekannte Methode: {config.method}")

        # Berechne Metriken
        try:
            metrics = stats_fn(simulated_returns)
        except Exception as e:
            logger.warning(f"Fehler bei Run {run_idx}: {e}, überspringe Run")
            continue

        # Sammle Metriken
        for metric_name, metric_value in metrics.items():
            if metric_name not in all_metrics:
                all_metrics[metric_name] = []
            all_metrics[metric_name].append(metric_value)

        run_results.append(MonteCarloRunResult(run_index=run_idx, metrics=metrics))

        # Progress-Logging
        if (run_idx + 1) % 100 == 0:
            logger.info(f"Fortschritt: {run_idx + 1}/{config.num_runs} Runs abgeschlossen")

    if not all_metrics:
        raise ValueError("Keine gültigen Runs durchgeführt - alle Runs fehlgeschlagen")

    # Erstelle Verteilungen und Quantilen
    metric_distributions: Dict[str, pd.Series] = {}
    metric_quantiles: Dict[str, Dict[str, float]] = {}

    for metric_name, values in all_metrics.items():
        series = pd.Series(values)
        metric_distributions[metric_name] = series

        # Berechne Quantilen
        metric_quantiles[metric_name] = {
            "p5": float(series.quantile(0.05)),
            "p25": float(series.quantile(0.25)),
            "p50": float(series.quantile(0.50)),
            "p75": float(series.quantile(0.75)),
            "p95": float(series.quantile(0.95)),
            "mean": float(series.mean()),
            "std": float(series.std()),
        }

    logger.info(f"Monte-Carlo abgeschlossen: {len(run_results)} gültige Runs")

    return MonteCarloSummaryResult(
        config=config,
        metric_distributions=metric_distributions,
        metric_quantiles=metric_quantiles,
        num_runs=len(run_results),
    )


# =============================================================================
# INTEGRATION WITH EXPERIMENTS
# =============================================================================


def load_returns_for_experiment_run(
    experiment_id: str,
    experiments_dir: Path,
) -> pd.Series:
    """
    Lädt Returns für einen Experiment-Run.

    Diese Funktion sucht nach gespeicherten Equity-Curves oder Returns
    in den Experiment-Ergebnissen.

    Args:
        experiment_id: Eindeutige Experiment-ID
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen

    Returns:
        Returns-Serie oder None, falls nicht gefunden

    Note:
        Aktuell ist dies eine vereinfachte Implementierung. In einer vollständigen
        Implementierung würde man die Equity-Curves aus den Backtest-Result-Objekten
        laden. Für Phase 45 verwenden wir eine pragmatische Lösung, die aus den
        Metriken approximiert oder Dummy-Daten verwendet.
    """
    run_dir = Path(experiments_dir) / experiment_id
    curves = load_equity_curves_from_run_dir(run_dir, max_curves=1)
    return equity_to_returns(curves[0])


def run_monte_carlo_for_experiment(
    experiment_id: str,
    config: MonteCarloConfig,
    experiments_dir: Path,
) -> MonteCarloSummaryResult:
    """
    Führt Monte-Carlo-Analyse für einen Experiment-Run durch.

    Args:
        experiment_id: Eindeutige Experiment-ID
        config: Monte-Carlo-Konfiguration
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen

    Returns:
        MonteCarloSummaryResult
    """
    returns = load_returns_for_experiment_run(experiment_id, experiments_dir)
    return run_monte_carlo_from_returns(returns, config)


def run_monte_carlo_from_equity(
    equity: pd.Series,
    config: MonteCarloConfig,
    *,
    stats_fn: Optional[Callable[[pd.Series], Dict[str, float]]] = None,
) -> MonteCarloSummaryResult:
    """
    Führt Monte-Carlo-Analyse auf Basis einer Equity-Curve durch.

    Konvertiert die Equity-Curve zu Returns und führt dann Monte-Carlo durch.

    Args:
        equity: Equity-Curve (Series mit DatetimeIndex)
        config: Monte-Carlo-Konfiguration
        stats_fn: Optionale Stats-Funktion (default: compute_basic_stats)

    Returns:
        MonteCarloSummaryResult
    """
    # Konvertiere Equity zu Returns
    returns = equity.pct_change().dropna()

    if len(returns) < 2:
        raise ValueError(f"Equity-Curve muss mindestens 2 Werte haben, got {len(equity)}")

    # Wrapper für stats_fn, der Equity erwartet
    if stats_fn is None:

        def stats_fn_equity(returns_series: pd.Series) -> Dict[str, float]:
            equity_sim = (1 + returns_series).cumprod() * equity.iloc[0]
            return stats_mod.compute_basic_stats(equity_sim)

        return run_monte_carlo_from_returns(returns, config, stats_fn=stats_fn_equity)
    else:
        return run_monte_carlo_from_returns(returns, config, stats_fn=stats_fn)
