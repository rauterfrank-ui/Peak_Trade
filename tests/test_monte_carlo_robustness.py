# tests/test_monte_carlo_robustness.py
"""
Tests für Monte-Carlo-Robustness (Phase 45)
===========================================

Tests für:
- run_monte_carlo_from_returns (simple & block_bootstrap)
- MonteCarloConfig Validierung
- Integration mit Stats-Funktionen
"""

from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.experiments.monte_carlo import (
    MonteCarloConfig,
    MonteCarloRunResult,
    MonteCarloSummaryResult,
    run_monte_carlo_from_returns,
    run_monte_carlo_from_equity,
    _simple_bootstrap,
    _block_bootstrap,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_returns() -> pd.Series:
    """Erstellt eine Sample-Returns-Serie für Tests."""
    np.random.seed(42)
    n = 200
    returns = np.random.normal(0.001, 0.02, n)  # ~0.1% pro Periode, 2% Vol
    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    return pd.Series(returns, index=dates)


@pytest.fixture
def sample_equity() -> pd.Series:
    """Erstellt eine Sample-Equity-Curve für Tests."""
    np.random.seed(42)
    n = 200
    returns = np.random.normal(0.001, 0.02, n)  # ~0.1% pro Periode, 2% Vol
    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    returns_series = pd.Series(returns, index=dates)
    equity = (1 + returns_series).cumprod() * 10000
    return equity


# =============================================================================
# CONFIG TESTS
# =============================================================================


def test_monte_carlo_config_defaults():
    """Testet Standard-Konfiguration."""
    config = MonteCarloConfig()
    assert config.num_runs == 1000
    assert config.method == "simple"
    assert config.block_size == 20
    assert config.seed == 42


def test_monte_carlo_config_custom():
    """Testet benutzerdefinierte Konfiguration."""
    config = MonteCarloConfig(
        num_runs=500,
        method="block_bootstrap",
        block_size=10,
        seed=123,
    )
    assert config.num_runs == 500
    assert config.method == "block_bootstrap"
    assert config.block_size == 10
    assert config.seed == 123


def test_monte_carlo_config_validation():
    """Testet Validierung der Konfiguration."""
    # num_runs < 1
    with pytest.raises(ValueError, match="num_runs muss >= 1"):
        MonteCarloConfig(num_runs=0)

    # block_size < 1
    with pytest.raises(ValueError, match="block_size muss >= 1"):
        MonteCarloConfig(method="block_bootstrap", block_size=0)


# =============================================================================
# BOOTSTRAP TESTS
# =============================================================================


def test_simple_bootstrap(sample_returns):
    """Testet einfachen Bootstrap."""
    rng = np.random.default_rng(42)
    n_samples = len(sample_returns)

    bootstrapped = _simple_bootstrap(sample_returns, n_samples, rng)

    assert len(bootstrapped) == n_samples
    assert isinstance(bootstrapped, pd.Series)
    # Alle Werte sollten aus der Original-Serie stammen
    assert all(val in sample_returns.values for val in bootstrapped.values)


def test_block_bootstrap(sample_returns):
    """Testet Block-Bootstrap."""
    rng = np.random.default_rng(42)
    n_samples = len(sample_returns)
    block_size = 20

    bootstrapped = _block_bootstrap(sample_returns, n_samples, block_size, rng)

    assert len(bootstrapped) == n_samples
    assert isinstance(bootstrapped, pd.Series)
    # Alle Werte sollten aus der Original-Serie stammen
    assert all(val in sample_returns.values for val in bootstrapped.values)


def test_block_bootstrap_too_large_block(sample_returns):
    """Testet Block-Bootstrap mit zu großem Block (Fallback zu simple)."""
    rng = np.random.default_rng(42)
    n_samples = len(sample_returns)
    block_size = len(sample_returns) + 10  # Größer als Serie

    bootstrapped = _block_bootstrap(sample_returns, n_samples, block_size, rng)

    # Sollte zu simple bootstrap fallen
    assert len(bootstrapped) == n_samples


# =============================================================================
# MONTE-CARLO TESTS
# =============================================================================


def test_run_monte_carlo_from_returns_simple(sample_returns):
    """Testet Monte-Carlo mit simple Bootstrap."""
    config = MonteCarloConfig(num_runs=50, method="simple", seed=42)

    summary = run_monte_carlo_from_returns(sample_returns, config)

    assert summary.num_runs == 50
    assert summary.config == config
    assert len(summary.metric_distributions) > 0
    assert len(summary.metric_quantiles) > 0

    # Prüfe, dass wichtige Metriken vorhanden sind
    assert "sharpe" in summary.metric_distributions
    assert "cagr" in summary.metric_distributions
    assert "max_drawdown" in summary.metric_distributions

    # Prüfe Quantilen-Struktur
    sharpe_quantiles = summary.metric_quantiles["sharpe"]
    assert "p5" in sharpe_quantiles
    assert "p50" in sharpe_quantiles
    assert "p95" in sharpe_quantiles
    assert "mean" in sharpe_quantiles
    assert "std" in sharpe_quantiles

    # Prüfe, dass p5 <= p50 <= p95
    assert sharpe_quantiles["p5"] <= sharpe_quantiles["p50"] <= sharpe_quantiles["p95"]


def test_run_monte_carlo_from_returns_block_bootstrap(sample_returns):
    """Testet Monte-Carlo mit Block-Bootstrap."""
    config = MonteCarloConfig(
        num_runs=50,
        method="block_bootstrap",
        block_size=10,
        seed=42,
    )

    summary = run_monte_carlo_from_returns(sample_returns, config)

    assert summary.num_runs == 50
    assert summary.config.method == "block_bootstrap"
    assert len(summary.metric_distributions) > 0


def test_run_monte_carlo_from_equity(sample_equity):
    """Testet Monte-Carlo mit Equity-Curve."""
    config = MonteCarloConfig(num_runs=50, method="simple", seed=42)

    summary = run_monte_carlo_from_equity(sample_equity, config)

    assert summary.num_runs == 50
    assert len(summary.metric_distributions) > 0


def test_run_monte_carlo_insufficient_data():
    """Testet Fehlerbehandlung bei unzureichenden Daten."""
    config = MonteCarloConfig(num_runs=10, method="simple")

    # Zu kurze Serie
    short_returns = pd.Series([0.01])
    with pytest.raises(ValueError, match="muss mindestens 2 Werte haben"):
        run_monte_carlo_from_returns(short_returns, config)


def test_run_monte_carlo_custom_stats_fn(sample_returns):
    """Testet Monte-Carlo mit benutzerdefinierter Stats-Funktion."""
    config = MonteCarloConfig(num_runs=20, method="simple", seed=42)

    def custom_stats_fn(returns: pd.Series) -> dict[str, float]:
        return {
            "mean": float(returns.mean()),
            "std": float(returns.std()),
            "min": float(returns.min()),
            "max": float(returns.max()),
        }

    summary = run_monte_carlo_from_returns(sample_returns, config, stats_fn=custom_stats_fn)

    assert summary.num_runs == 20
    assert "mean" in summary.metric_distributions
    assert "std" in summary.metric_distributions
    assert "min" in summary.metric_distributions
    assert "max" in summary.metric_distributions


def test_run_monte_carlo_reproducibility(sample_returns):
    """Testet Reproduzierbarkeit mit gleichem Seed."""
    config1 = MonteCarloConfig(num_runs=10, method="simple", seed=42)
    config2 = MonteCarloConfig(num_runs=10, method="simple", seed=42)

    summary1 = run_monte_carlo_from_returns(sample_returns, config1)
    summary2 = run_monte_carlo_from_returns(sample_returns, config2)

    # Mit gleichem Seed sollten die Ergebnisse identisch sein
    for metric_name in summary1.metric_distributions:
        dist1 = summary1.metric_distributions[metric_name]
        dist2 = summary2.metric_distributions[metric_name]
        pd.testing.assert_series_equal(dist1, dist2)


def test_run_monte_carlo_different_seeds(sample_returns):
    """Testet, dass verschiedene Seeds unterschiedliche Ergebnisse liefern."""
    config1 = MonteCarloConfig(num_runs=10, method="simple", seed=42)
    config2 = MonteCarloConfig(num_runs=10, method="simple", seed=123)

    summary1 = run_monte_carlo_from_returns(sample_returns, config1)
    summary2 = run_monte_carlo_from_returns(sample_returns, config2)

    # Mit verschiedenen Seeds sollten die Ergebnisse unterschiedlich sein
    # (mit sehr hoher Wahrscheinlichkeit)
    # Nutze total_return statt sharpe, da sharpe bei kurzen Serien konstant sein kann
    tr1 = summary1.metric_distributions["total_return"]
    tr2 = summary2.metric_distributions["total_return"]
    assert not tr1.equals(tr2)

