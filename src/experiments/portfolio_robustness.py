# src/experiments/portfolio_robustness.py
"""
Peak_Trade Portfolio-Level Robustness (Phase 47)
=================================================

Portfolio-Level Robustness-Analysen (Monte-Carlo & Stress-Tests) für Multi-Strategy-Portfolios.

Features:
- Portfolio-Return-Synthese aus mehreren Strategien
- Portfolio-Level Monte-Carlo
- Portfolio-Level Stress-Tests
- Integration mit Experiment-Registry & Top-N

Usage:
    from src.experiments.portfolio_robustness import (
        PortfolioComponent,
        PortfolioDefinition,
        PortfolioRobustnessConfig,
        PortfolioRobustnessResult,
        build_portfolio_returns,
        run_portfolio_robustness,
    )

    portfolio = PortfolioDefinition(
        name="rsi_portfolio_v1",
        components=[
            PortfolioComponent(strategy_name="rsi_reversion", config_id="config_1", weight=0.4),
            PortfolioComponent(strategy_name="ma_crossover", config_id="config_2", weight=0.3),
            PortfolioComponent(strategy_name="momentum", config_id="config_3", weight=0.3),
        ],
    )
    config = PortfolioRobustnessConfig(portfolio=portfolio, num_mc_runs=1000, run_stress_tests=True)
    result = run_portfolio_robustness(config, returns_loader)
"""
from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from ..backtest import stats as stats_mod
from .monte_carlo import MonteCarloConfig, run_monte_carlo_from_returns
from .stress_tests import (
    StressScenarioConfig,
    run_stress_test_suite,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DATAMODELS
# =============================================================================


@dataclass
class PortfolioComponent:
    """
    Eine Komponente (Strategie) im Portfolio.

    Attributes:
        strategy_name: Name der Strategie (z.B. "rsi_reversion")
        config_id: Identifier für die Konfiguration (z.B. "config_1" oder Registry-ID)
        weight: Gewicht im Portfolio (0.0-1.0, sollte zu 1.0 summieren)
    """

    strategy_name: str
    config_id: str
    weight: float

    def __post_init__(self) -> None:
        """Validiert Komponente."""
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"weight muss zwischen 0.0 und 1.0 sein, got {self.weight}")


@dataclass
class PortfolioDefinition:
    """
    Definition eines Portfolios aus mehreren Strategien.

    Attributes:
        name: Name des Portfolios
        components: Liste von Portfolio-Komponenten
        rebalancing: Rebalancing-Frequenz (aktuell nicht implementiert, für zukünftige Erweiterungen)
    """

    name: str
    components: list[PortfolioComponent]
    rebalancing: Literal["none", "daily", "weekly", "monthly"] = "none"

    def __post_init__(self) -> None:
        """Validiert Portfolio-Definition."""
        if not self.components:
            raise ValueError("Portfolio muss mindestens eine Komponente haben")

        total_weight = sum(c.weight for c in self.components)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(
                f"Portfolio-Gewichte summieren zu {total_weight:.4f} statt 1.0. "
                f"Normalisiere automatisch."
            )
            # Normalisiere Gewichte
            for component in self.components:
                component.weight = component.weight / total_weight


@dataclass
class PortfolioRobustnessConfig:
    """
    Konfiguration für Portfolio-Level Robustness-Analysen.

    Attributes:
        portfolio: Portfolio-Definition
        num_mc_runs: Anzahl Monte-Carlo-Runs (0 = kein Monte-Carlo)
        mc_method: Monte-Carlo-Methode ("simple" oder "block_bootstrap")
        mc_block_size: Block-Größe für Block-Bootstrap
        mc_seed: Random Seed für Monte-Carlo
        run_stress_tests: Ob Stress-Tests ausgeführt werden sollen
        stress_scenarios: Liste von Stress-Szenario-Typen
        stress_severity: Basis-Severity für Stress-Szenarien
        stress_window: Fenster-Größe für Stress-Szenarien
        stress_position: Position des Stress-Shocks
        stress_seed: Random Seed für Stress-Tests
    """

    portfolio: PortfolioDefinition
    num_mc_runs: int = 0
    mc_method: Literal["simple", "block_bootstrap"] = "simple"
    mc_block_size: int = 20
    mc_seed: int | None = 42
    run_stress_tests: bool = False
    stress_scenarios: list[str] | None = None
    stress_severity: float = 0.2
    stress_window: int = 5
    stress_position: Literal["start", "middle", "end"] = "middle"
    stress_seed: int | None = 42

    def __post_init__(self) -> None:
        """Validiert Konfiguration."""
        if self.num_mc_runs < 0:
            raise ValueError(f"num_mc_runs muss >= 0 sein, got {self.num_mc_runs}")
        if self.run_stress_tests and not self.stress_scenarios:
            self.stress_scenarios = ["single_crash_bar", "vol_spike"]


@dataclass
class PortfolioRobustnessResult:
    """
    Ergebnis einer Portfolio-Level Robustness-Analyse.

    Attributes:
        portfolio: Verwendete Portfolio-Definition
        portfolio_returns: Synthetisierte Portfolio-Returns
        baseline_metrics: Baseline-Metriken des Portfolios
        mc_results: Monte-Carlo-Ergebnisse (None wenn nicht ausgeführt)
        stress_results: Stress-Test-Ergebnisse (None wenn nicht ausgeführt)
    """

    portfolio: PortfolioDefinition
    portfolio_returns: pd.Series
    baseline_metrics: dict[str, float]
    mc_results: dict | None = None
    stress_results: dict | None = None


# =============================================================================
# PORTFOLIO RETURN SYNTHESIS
# =============================================================================


def build_portfolio_returns(
    components: Iterable[PortfolioComponent],
    returns_loader: Callable[[str, str], pd.Series | None],
) -> pd.Series:
    """
    Baut eine Portfolio-Return-Serie aus mehreren Komponenten, gewichtet nach `weight`.

    Args:
        components: Iterable von Portfolio-Komponenten
        returns_loader: Funktion, die für (strategy_name, config_id) eine Returns-Serie liefert
                       oder None, falls nicht verfügbar

    Returns:
        Portfolio-Returns (gleicher Index wie die Einzel-Strategien, aligned via inner join)

    Raises:
        ValueError: Wenn keine gültigen Returns geladen werden konnten

    Example:
        >>> def loader(strategy_name: str, config_id: str) -> pd.Series:
        ...     # Lade Returns aus Registry/Sweep-Ergebnissen
        ...     return pd.Series([0.01, -0.02, 0.015, ...])
        >>>
        >>> components = [
        ...     PortfolioComponent("rsi_reversion", "config_1", 0.4),
        ...     PortfolioComponent("ma_crossover", "config_2", 0.6),
        ... ]
        >>> portfolio_returns = build_portfolio_returns(components, loader)
    """
    component_returns: list[pd.Series] = []
    component_weights: list[float] = []

    for component in components:
        returns = returns_loader(component.strategy_name, component.config_id)

        if returns is None:
            logger.warning(
                f"Konnte Returns nicht laden für {component.strategy_name}/{component.config_id}, "
                f"überspringe Komponente"
            )
            continue

        if len(returns) == 0:
            logger.warning(
                f"Leere Returns-Serie für {component.strategy_name}/{component.config_id}, "
                f"überspringe Komponente"
            )
            continue

        component_returns.append(returns)
        component_weights.append(component.weight)

    if not component_returns:
        raise ValueError("Keine gültigen Returns für Portfolio-Komponenten gefunden")

    # Normalisiere Gewichte (falls einige Komponenten übersprungen wurden)
    total_weight = sum(component_weights)
    if total_weight > 0:
        component_weights = [w / total_weight for w in component_weights]

    # Aligne Returns (inner join, nur gemeinsame Zeitpunkte)
    if len(component_returns) == 1:
        portfolio_returns = component_returns[0] * component_weights[0]
    else:
        # Kombiniere alle Returns in DataFrame
        df = pd.DataFrame({i: ret for i, ret in enumerate(component_returns)})
        df = df.dropna()  # Entferne Zeilen mit fehlenden Werten

        if len(df) == 0:
            raise ValueError("Keine überlappenden Zeitpunkte zwischen Portfolio-Komponenten")

        # Gewichtete Summe
        portfolio_returns = pd.Series(0.0, index=df.index)
        for i, weight in enumerate(component_weights):
            portfolio_returns += df[i] * weight

    logger.info(
        f"Portfolio-Returns synthetisiert: {len(portfolio_returns)} Bars, "
        f"{len(component_returns)} Komponenten"
    )

    return portfolio_returns


# =============================================================================
# PORTFOLIO METRICS
# =============================================================================


def compute_portfolio_metrics(returns: pd.Series) -> dict[str, float]:
    """
    Berechnet Portfolio-Level-Metriken aus Returns.

    Args:
        returns: Portfolio-Returns-Serie

    Returns:
        Dict mit Metriken (Sharpe, CAGR, Max-Drawdown, etc.)

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.015, ...])
        >>> metrics = compute_portfolio_metrics(returns)
        >>> print(f"Sharpe: {metrics['sharpe']:.2f}")
    """
    if len(returns) < 2:
        return {
            "total_return": 0.0,
            "cagr": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "volatility": 0.0,
        }

    # Konvertiere Returns zu Equity-Curve
    equity = (1 + returns).cumprod() * 10000  # Startkapital = 10000

    # Basis-Metriken
    stats = stats_mod.compute_basic_stats(equity)

    # Zusätzliche Metriken
    stats["volatility"] = float(returns.std() * np.sqrt(252))  # Annualisiert
    stats["mean_return"] = float(returns.mean() * 252)  # Annualisiert

    return stats


# =============================================================================
# PORTFOLIO MONTE-CARLO
# =============================================================================


def run_portfolio_monte_carlo(
    returns: pd.Series,
    num_runs: int,
    method: str = "simple",
    block_size: int = 20,
    seed: int | None = 42,
) -> dict:
    """
    Führt Monte-Carlo-Simulationen auf Portfolio-Returns durch.

    Args:
        returns: Portfolio-Returns-Serie
        num_runs: Anzahl Monte-Carlo-Runs
        method: Monte-Carlo-Methode ("simple" oder "block_bootstrap")
        block_size: Block-Größe für Block-Bootstrap
        seed: Random Seed

    Returns:
        Dict mit kompakter Summary-Struktur für Reporting

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.015, ...])
        >>> mc_results = run_portfolio_monte_carlo(returns, num_runs=1000)
        >>> print(f"Sharpe p50: {mc_results['metric_quantiles']['sharpe']['p50']:.2f}")
    """
    if num_runs <= 0:
        return {}

    config = MonteCarloConfig(
        num_runs=num_runs,
        method=method,  # type: ignore
        block_size=block_size,
        seed=seed,
    )

    def stats_fn(returns_series: pd.Series) -> dict[str, float]:
        return compute_portfolio_metrics(returns_series)

    summary = run_monte_carlo_from_returns(returns, config, stats_fn=stats_fn)

    # Konvertiere zu kompakter Dict-Struktur
    return {
        "num_runs": summary.num_runs,
        "method": summary.config.method,
        "metric_quantiles": summary.metric_quantiles,
        "metric_distributions": {
            k: v.tolist() for k, v in summary.metric_distributions.items()
        },
    }


# =============================================================================
# PORTFOLIO STRESS-TESTS
# =============================================================================


def run_portfolio_stress_tests(
    returns: pd.Series,
    scenario_names: list[str],
    severity: float = 0.2,
    window: int = 5,
    position: Literal["start", "middle", "end"] = "middle",
    seed: int | None = 42,
) -> dict:
    """
    Führt Portfolio-Level-Stress-Szenarien aus.

    Args:
        returns: Portfolio-Returns-Serie
        scenario_names: Liste von Stress-Szenario-Typen
        severity: Basis-Severity für Szenarien
        window: Fenster-Größe für vol_spike / drawdown_extension
        position: Position des Stress-Shocks
        seed: Random Seed

    Returns:
        Dict mit kompakter Summary-Struktur für Reporting

    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.015, ...])
        >>> stress_results = run_portfolio_stress_tests(
        ...     returns,
        ...     scenario_names=["single_crash_bar", "vol_spike"],
        ...     severity=0.2,
        ... )
    """
    if not scenario_names:
        return {}

    # Erstelle Stress-Szenario-Configs
    scenarios = []
    for scenario_type in scenario_names:
        scenarios.append(
            StressScenarioConfig(
                scenario_type=scenario_type,  # type: ignore
                severity=severity,
                window=window,
                position=position,
                seed=seed,
            )
        )

    def stats_fn(returns_series: pd.Series) -> dict[str, float]:
        return compute_portfolio_metrics(returns_series)

    suite = run_stress_test_suite(returns, scenarios, stats_fn)

    # Konvertiere zu kompakter Dict-Struktur
    scenario_summaries = []
    for result in suite.scenario_results:
        scenario_summaries.append({
            "scenario_type": result.scenario.scenario_type,
            "severity": result.scenario.severity,
            "baseline_metrics": result.baseline_metrics,
            "stressed_metrics": result.stressed_metrics,
            "diff_metrics": result.diff_metrics,
        })

    return {
        "baseline_metrics": suite.baseline_metrics,
        "scenarios": scenario_summaries,
    }


# =============================================================================
# ORCHESTRATOR
# =============================================================================


def run_portfolio_robustness(
    robustness_config: PortfolioRobustnessConfig,
    returns_loader: Callable[[str, str], pd.Series | None],
) -> PortfolioRobustnessResult:
    """
    Führt Baseline-Analyse, optional Monte-Carlo und optional Stress-Tests auf Portfolio-Ebene durch.

    Args:
        robustness_config: Portfolio-Robustness-Konfiguration
        returns_loader: Funktion, die für (strategy_name, config_id) eine Returns-Serie liefert

    Returns:
        PortfolioRobustnessResult mit allen Ergebnissen

    Example:
        >>> config = PortfolioRobustnessConfig(
        ...     portfolio=portfolio,
        ...     num_mc_runs=1000,
        ...     run_stress_tests=True,
        ... )
        >>> result = run_portfolio_robustness(config, returns_loader)
    """
    portfolio = robustness_config.portfolio

    logger.info(f"Starte Portfolio-Robustness-Analyse für Portfolio '{portfolio.name}'")
    logger.info(f"Komponenten: {len(portfolio.components)}")

    # 1. Synthetisiere Portfolio-Returns
    logger.info("Synthetisiere Portfolio-Returns...")
    portfolio_returns = build_portfolio_returns(portfolio.components, returns_loader)

    # 2. Berechne Baseline-Metriken
    logger.info("Berechne Baseline-Metriken...")
    baseline_metrics = compute_portfolio_metrics(portfolio_returns)

    # 3. Monte-Carlo (optional)
    mc_results = None
    if robustness_config.num_mc_runs > 0:
        logger.info(f"Führe Monte-Carlo aus ({robustness_config.num_mc_runs} Runs)...")
        mc_results = run_portfolio_monte_carlo(
            portfolio_returns,
            num_runs=robustness_config.num_mc_runs,
            method=robustness_config.mc_method,
            block_size=robustness_config.mc_block_size,
            seed=robustness_config.mc_seed,
        )

    # 4. Stress-Tests (optional)
    stress_results = None
    if robustness_config.run_stress_tests and robustness_config.stress_scenarios:
        logger.info(
            f"Führe Stress-Tests aus ({len(robustness_config.stress_scenarios)} Szenarien)..."
        )
        stress_results = run_portfolio_stress_tests(
            portfolio_returns,
            scenario_names=robustness_config.stress_scenarios,
            severity=robustness_config.stress_severity,
            window=robustness_config.stress_window,
            position=robustness_config.stress_position,
            seed=robustness_config.stress_seed,
        )

    logger.info("Portfolio-Robustness-Analyse abgeschlossen")

    return PortfolioRobustnessResult(
        portfolio=portfolio,
        portfolio_returns=portfolio_returns,
        baseline_metrics=baseline_metrics,
        mc_results=mc_results,
        stress_results=stress_results,
    )








