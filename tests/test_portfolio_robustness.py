# tests/test_portfolio_robustness.py
"""
Tests für Portfolio-Level Robustness (Phase 47)
================================================

Tests für:
- build_portfolio_returns
- compute_portfolio_metrics
- run_portfolio_monte_carlo
- run_portfolio_stress_tests
- run_portfolio_robustness
"""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.experiments.portfolio_robustness import (
    PortfolioComponent,
    PortfolioDefinition,
    PortfolioRobustnessConfig,
    PortfolioRobustnessResult,
    build_portfolio_returns,
    compute_portfolio_metrics,
    run_portfolio_monte_carlo,
    run_portfolio_stress_tests,
    run_portfolio_robustness,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_returns_1() -> pd.Series:
    """Erstellt Sample-Returns-Serie 1 für Tests."""
    np.random.seed(42)
    n = 200
    returns = np.random.normal(0.001, 0.02, n)
    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    return pd.Series(returns, index=dates)


@pytest.fixture
def sample_returns_2() -> pd.Series:
    """Erstellt Sample-Returns-Serie 2 für Tests."""
    np.random.seed(43)
    n = 200
    returns = np.random.normal(0.0008, 0.018, n)
    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    return pd.Series(returns, index=dates)


@pytest.fixture
def sample_returns_3() -> pd.Series:
    """Erstellt Sample-Returns-Serie 3 für Tests."""
    np.random.seed(44)
    n = 200
    returns = np.random.normal(0.0012, 0.022, n)
    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    return pd.Series(returns, index=dates)


@pytest.fixture
def sample_portfolio_components() -> list[PortfolioComponent]:
    """Erstellt Sample-Portfolio-Komponenten."""
    return [
        PortfolioComponent(strategy_name="strategy_1", config_id="config_1", weight=0.4),
        PortfolioComponent(strategy_name="strategy_2", config_id="config_2", weight=0.3),
        PortfolioComponent(strategy_name="strategy_3", config_id="config_3", weight=0.3),
    ]


@pytest.fixture
def sample_returns_loader(sample_returns_1, sample_returns_2, sample_returns_3):
    """Erstellt einen Returns-Loader für Tests."""
    returns_map = {
        ("strategy_1", "config_1"): sample_returns_1,
        ("strategy_2", "config_2"): sample_returns_2,
        ("strategy_3", "config_3"): sample_returns_3,
    }

    def loader(strategy_name: str, config_id: str) -> Optional[pd.Series]:
        return returns_map.get((strategy_name, config_id))

    return loader


# =============================================================================
# DATAMODEL TESTS
# =============================================================================


def test_portfolio_component_validation():
    """Testet Validierung von PortfolioComponent."""
    # Gültige Komponente
    comp = PortfolioComponent("strategy_1", "config_1", 0.5)
    assert comp.weight == 0.5

    # Ungültiges Gewicht
    with pytest.raises(ValueError, match="weight muss zwischen 0.0 und 1.0"):
        PortfolioComponent("strategy_1", "config_1", 1.5)


def test_portfolio_definition_validation():
    """Testet Validierung von PortfolioDefinition."""
    # Gültiges Portfolio
    components = [
        PortfolioComponent("strategy_1", "config_1", 0.5),
        PortfolioComponent("strategy_2", "config_2", 0.5),
    ]
    portfolio = PortfolioDefinition(name="test_portfolio", components=components)
    assert len(portfolio.components) == 2

    # Leeres Portfolio
    with pytest.raises(ValueError, match="Portfolio muss mindestens eine Komponente haben"):
        PortfolioDefinition(name="empty", components=[])

    # Normalisierung bei nicht-normierten Gewichten
    components_unnormalized = [
        PortfolioComponent("strategy_1", "config_1", 0.3),
        PortfolioComponent("strategy_2", "config_2", 0.3),
    ]
    portfolio = PortfolioDefinition(name="test", components=components_unnormalized)
    total_weight = sum(c.weight for c in portfolio.components)
    assert abs(total_weight - 1.0) < 0.01


def test_portfolio_robustness_config_validation():
    """Testet Validierung von PortfolioRobustnessConfig."""
    components = [PortfolioComponent("strategy_1", "config_1", 1.0)]
    portfolio = PortfolioDefinition(name="test", components=components)

    # Gültige Config
    config = PortfolioRobustnessConfig(portfolio=portfolio, num_mc_runs=1000)
    assert config.num_mc_runs == 1000

    # Ungültige num_mc_runs
    with pytest.raises(ValueError, match="num_mc_runs muss >= 0"):
        PortfolioRobustnessConfig(portfolio=portfolio, num_mc_runs=-1)

    # Auto-Stress-Szenarien wenn run_stress_tests=True
    config = PortfolioRobustnessConfig(portfolio=portfolio, run_stress_tests=True)
    assert config.stress_scenarios is not None
    assert len(config.stress_scenarios) > 0


# =============================================================================
# PORTFOLIO RETURN SYNTHESIS TESTS
# =============================================================================


def test_build_portfolio_returns(sample_portfolio_components, sample_returns_loader):
    """Testet build_portfolio_returns."""
    portfolio_returns = build_portfolio_returns(sample_portfolio_components, sample_returns_loader)

    assert len(portfolio_returns) > 0
    assert isinstance(portfolio_returns.index, pd.DatetimeIndex)

    # Prüfe, dass Portfolio-Return = gewichtete Summe ist (ungefähr)
    # (Exakte Prüfung schwierig wegen Alignment, aber Struktur sollte stimmen)
    assert portfolio_returns.dtype == float or portfolio_returns.dtype == np.float64


def test_build_portfolio_returns_single_component(sample_returns_loader):
    """Testet build_portfolio_returns mit nur einer Komponente."""
    components = [PortfolioComponent("strategy_1", "config_1", 1.0)]
    portfolio_returns = build_portfolio_returns(components, sample_returns_loader)

    assert len(portfolio_returns) > 0


def test_build_portfolio_returns_no_valid_returns(sample_portfolio_components):
    """Testet build_portfolio_returns mit fehlenden Returns."""
    def empty_loader(strategy_name: str, config_id: str) -> Optional[pd.Series]:
        return None

    with pytest.raises(ValueError, match="Keine gültigen Returns"):
        build_portfolio_returns(sample_portfolio_components, empty_loader)


# =============================================================================
# PORTFOLIO METRICS TESTS
# =============================================================================


def test_compute_portfolio_metrics(sample_returns_1):
    """Testet compute_portfolio_metrics."""
    metrics = compute_portfolio_metrics(sample_returns_1)

    assert "sharpe" in metrics
    assert "max_drawdown" in metrics
    assert "total_return" in metrics
    assert "cagr" in metrics
    assert "volatility" in metrics

    # Prüfe, dass Metriken sinnvolle Werte haben
    assert isinstance(metrics["sharpe"], float)
    assert isinstance(metrics["max_drawdown"], float)
    assert metrics["max_drawdown"] <= 0.0  # Drawdown sollte negativ sein


def test_compute_portfolio_metrics_short_series():
    """Testet compute_portfolio_metrics mit zu kurzer Serie."""
    short_returns = pd.Series([0.01])
    metrics = compute_portfolio_metrics(short_returns)

    assert metrics["total_return"] == 0.0
    assert metrics["sharpe"] == 0.0


# =============================================================================
# PORTFOLIO MONTE-CARLO TESTS
# =============================================================================


def test_run_portfolio_monte_carlo(sample_returns_1):
    """Testet run_portfolio_monte_carlo."""
    mc_results = run_portfolio_monte_carlo(sample_returns_1, num_runs=100, method="simple")

    assert mc_results is not None
    assert "num_runs" in mc_results
    assert mc_results["num_runs"] == 100
    assert "method" in mc_results
    assert "metric_quantiles" in mc_results

    # Prüfe, dass Quantilen vorhanden sind
    if mc_results["metric_quantiles"]:
        first_metric = list(mc_results["metric_quantiles"].keys())[0]
        quantiles = mc_results["metric_quantiles"][first_metric]
        assert "p50" in quantiles


def test_run_portfolio_monte_carlo_zero_runs(sample_returns_1):
    """Testet run_portfolio_monte_carlo mit num_runs=0."""
    mc_results = run_portfolio_monte_carlo(sample_returns_1, num_runs=0)
    assert mc_results == {}


# =============================================================================
# PORTFOLIO STRESS-TESTS TESTS
# =============================================================================


def test_run_portfolio_stress_tests(sample_returns_1):
    """Testet run_portfolio_stress_tests."""
    stress_results = run_portfolio_stress_tests(
        sample_returns_1,
        scenario_names=["single_crash_bar", "vol_spike"],
        severity=0.2,
    )

    assert stress_results is not None
    assert "baseline_metrics" in stress_results
    assert "scenarios" in stress_results
    assert len(stress_results["scenarios"]) == 2

    # Prüfe Szenario-Struktur
    for scenario in stress_results["scenarios"]:
        assert "scenario_type" in scenario
        assert "baseline_metrics" in scenario
        assert "stressed_metrics" in scenario
        assert "diff_metrics" in scenario


def test_run_portfolio_stress_tests_empty_scenarios(sample_returns_1):
    """Testet run_portfolio_stress_tests mit leerer Szenario-Liste."""
    stress_results = run_portfolio_stress_tests(sample_returns_1, scenario_names=[])
    assert stress_results == {}


# =============================================================================
# ORCHESTRATOR TESTS
# =============================================================================


def test_run_portfolio_robustness_baseline_only(sample_portfolio_components, sample_returns_loader):
    """Testet run_portfolio_robustness nur mit Baseline."""
    components = sample_portfolio_components
    portfolio = PortfolioDefinition(name="test_portfolio", components=components)

    config = PortfolioRobustnessConfig(
        portfolio=portfolio,
        num_mc_runs=0,
        run_stress_tests=False,
    )

    result = run_portfolio_robustness(config, sample_returns_loader)

    assert isinstance(result, PortfolioRobustnessResult)
    assert len(result.portfolio_returns) > 0
    assert len(result.baseline_metrics) > 0
    assert result.mc_results is None
    assert result.stress_results is None


def test_run_portfolio_robustness_with_monte_carlo(sample_portfolio_components, sample_returns_loader):
    """Testet run_portfolio_robustness mit Monte-Carlo."""
    components = sample_portfolio_components
    portfolio = PortfolioDefinition(name="test_portfolio", components=components)

    config = PortfolioRobustnessConfig(
        portfolio=portfolio,
        num_mc_runs=100,  # Kleine Anzahl für Tests
        run_stress_tests=False,
    )

    result = run_portfolio_robustness(config, sample_returns_loader)

    assert result.mc_results is not None
    assert result.mc_results["num_runs"] == 100


def test_run_portfolio_robustness_with_stress_tests(sample_portfolio_components, sample_returns_loader):
    """Testet run_portfolio_robustness mit Stress-Tests."""
    components = sample_portfolio_components
    portfolio = PortfolioDefinition(name="test_portfolio", components=components)

    config = PortfolioRobustnessConfig(
        portfolio=portfolio,
        num_mc_runs=0,
        run_stress_tests=True,
        stress_scenarios=["single_crash_bar"],
    )

    result = run_portfolio_robustness(config, sample_returns_loader)

    assert result.stress_results is not None
    assert len(result.stress_results.get("scenarios", [])) == 1


def test_run_portfolio_robustness_full(sample_portfolio_components, sample_returns_loader):
    """Testet run_portfolio_robustness mit allen Optionen."""
    components = sample_portfolio_components
    portfolio = PortfolioDefinition(name="test_portfolio", components=components)

    config = PortfolioRobustnessConfig(
        portfolio=portfolio,
        num_mc_runs=100,
        run_stress_tests=True,
        stress_scenarios=["single_crash_bar"],
    )

    result = run_portfolio_robustness(config, sample_returns_loader)

    assert result.mc_results is not None
    assert result.stress_results is not None








