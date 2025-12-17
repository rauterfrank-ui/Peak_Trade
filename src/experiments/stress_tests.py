# src/experiments/stress_tests.py
"""
Peak_Trade Stress-Tests & Crash-Szenarien (Phase 46)
====================================================

Stress-Tests für Strategien durch deterministische Transformationen von Returns/Equity.

Features:
- Szenario-Typen: single_crash_bar, vol_spike, drawdown_extension, gap_down_open
- Baseline vs. Szenario-Vergleiche
- Integration mit Experiment-Registry

Usage:
    from src.experiments.stress_tests import (
        StressScenarioConfig,
        StressScenarioResult,
        StressTestSuiteResult,
        apply_stress_scenario_to_returns,
        run_stress_test_suite,
    )

    returns = pd.Series([0.01, -0.02, 0.015, ...])
    scenario = StressScenarioConfig(
        scenario_type="single_crash_bar",
        severity=0.2,
        position="middle",
    )
    stressed_returns = apply_stress_scenario_to_returns(returns, scenario)
    suite = run_stress_test_suite(returns, [scenario], stats_fn)
"""
from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

StressScenarioType = Literal[
    "single_crash_bar",      # ein starker negativer Return an einem Tag
    "vol_spike",             # Volatilität sprunghaft erhöht
    "drawdown_extension",    # vorhandene Drawdowns werden verlängert/vertieft
    "gap_down_open",         # großer einmaliger Gap nach unten
]


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class StressScenarioConfig:
    """
    Konfiguration für ein Stress-Szenario.

    Attributes:
        scenario_type: Typ des Szenarios
        severity: Schweregrad (z.B. 0.2 = 20% Crash)
        window: Fenster-Größe für vol_spike / drawdown_extension
        position: Position des Shocks ("start", "middle", "end")
        seed: Random Seed für deterministische Positionierung (falls zufällig)
    """

    scenario_type: StressScenarioType
    severity: float = 0.2
    window: int = 5
    position: Literal["start", "middle", "end"] = "middle"
    seed: int | None = 42

    def __post_init__(self) -> None:
        """Validiert Konfiguration."""
        if self.severity <= 0:
            raise ValueError(f"severity muss > 0 sein, got {self.severity}")
        if self.window < 1:
            raise ValueError(f"window muss >= 1 sein, got {self.window}")


# =============================================================================
# RESULT OBJECTS
# =============================================================================


@dataclass
class StressScenarioResult:
    """
    Ergebnis eines einzelnen Stress-Szenarios.

    Attributes:
        scenario: Verwendete StressScenarioConfig
        baseline_metrics: Metriken der Baseline-Returns
        stressed_metrics: Metriken der gestressten Returns
        diff_metrics: Differenz (stressed - baseline)
    """

    scenario: StressScenarioConfig
    baseline_metrics: dict[str, float]
    stressed_metrics: dict[str, float]
    diff_metrics: dict[str, float]


@dataclass
class StressTestSuiteResult:
    """
    Ergebnis einer kompletten Stress-Test-Suite.

    Attributes:
        returns: Original-Returns-Serie
        baseline_metrics: Metriken der Baseline
        scenario_results: Liste von StressScenarioResult
    """

    returns: pd.Series
    baseline_metrics: dict[str, float]
    scenario_results: list[StressScenarioResult]


# =============================================================================
# SCENARIO TRANSFORM FUNCTIONS
# =============================================================================


def _get_position_index(
    length: int,
    position: Literal["start", "middle", "end"],
    seed: int | None = None,
) -> int:
    """
    Bestimmt den Index für eine Position.

    Args:
        length: Länge der Serie
        position: Position ("start", "middle", "end")
        seed: Optionaler Seed für deterministische Zufälligkeit

    Returns:
        Index (0-basiert)
    """
    if length == 0:
        return 0

    if position == "start":
        return 0
    elif position == "end":
        return length - 1
    elif position == "middle":
        return length // 2
    else:
        raise ValueError(f"Unbekannte Position: {position}")


def apply_stress_scenario_to_returns(
    returns: pd.Series,
    scenario: StressScenarioConfig,
) -> pd.Series:
    """
    Wendet ein Stress-Szenario auf eine Serie von Returns an.

    Args:
        returns: Original-Returns-Serie
        scenario: Stress-Szenario-Konfiguration

    Returns:
        Neue Serie mit gestressten Returns

    Example:
        >>> returns = pd.Series([0.01, 0.02, -0.01, 0.015])
        >>> scenario = StressScenarioConfig(
        ...     scenario_type="single_crash_bar",
        ...     severity=0.2,
        ...     position="middle",
        ... )
        >>> stressed = apply_stress_scenario_to_returns(returns, scenario)
        >>> assert stressed.iloc[1] < -0.15  # Crash-Bar sollte sehr negativ sein
    """
    if len(returns) == 0:
        return returns.copy()

    stressed = returns.copy()

    if scenario.scenario_type == "single_crash_bar":
        # Einzelner starker negativer Return
        idx = _get_position_index(len(returns), scenario.position, scenario.seed)
        stressed.iloc[idx] = -scenario.severity

    elif scenario.scenario_type == "vol_spike":
        # Erhöhe Volatilität in einem Fenster
        idx = _get_position_index(len(returns), scenario.position, scenario.seed)
        start_idx = max(0, idx - scenario.window // 2)
        end_idx = min(len(returns), idx + scenario.window // 2 + 1)

        # Multipliziere Returns im Fenster mit (1 + severity_factor)
        # severity_factor bestimmt, wie stark die Volatilität steigt
        severity_factor = scenario.severity
        stressed.iloc[start_idx:end_idx] = stressed.iloc[start_idx:end_idx] * (1 + severity_factor)

    elif scenario.scenario_type == "drawdown_extension":
        # Identifiziere stärkste Drawdown-Phase und verstärke sie
        equity = (1 + returns).cumprod()
        running_max = equity.cummax()
        drawdown = (equity - running_max) / running_max.replace(0.0, np.nan)

        # Finde längste/größte Drawdown-Phase
        in_drawdown = drawdown < -0.01  # Mindestens 1% Drawdown

        if in_drawdown.any():
            # Finde Start und Ende der größten Drawdown-Phase
            drawdown_periods = []
            start = None
            for i, is_dd in enumerate(in_drawdown):
                if is_dd and start is None:
                    start = i
                elif not is_dd and start is not None:
                    drawdown_periods.append((start, i))
                    start = None
            if start is not None:
                drawdown_periods.append((start, len(in_drawdown)))

            if drawdown_periods:
                # Wähle längste Drawdown-Phase
                longest = max(drawdown_periods, key=lambda x: x[1] - x[0])
                start_idx, end_idx = longest

                # Verstärke negative Returns in dieser Phase
                window_returns = stressed.iloc[start_idx:end_idx]
                negative_mask = window_returns < 0
                if negative_mask.any():
                    # Multipliziere negative Returns mit (1 + severity)
                    stressed.iloc[start_idx:end_idx] = window_returns.where(
                        ~negative_mask,
                        window_returns * (1 + scenario.severity),
                    )
        else:
            # Keine Drawdown-Phase gefunden, wende auf Mitte an
            idx = _get_position_index(len(returns), scenario.position, scenario.seed)
            start_idx = max(0, idx - scenario.window // 2)
            end_idx = min(len(returns), idx + scenario.window // 2 + 1)
            window_returns = stressed.iloc[start_idx:end_idx]
            negative_mask = window_returns < 0
            if negative_mask.any():
                stressed.iloc[start_idx:end_idx] = window_returns.where(
                    ~negative_mask,
                    window_returns * (1 + scenario.severity),
                )

    elif scenario.scenario_type == "gap_down_open":
        # Großer einmaliger Gap nach unten (additiver negativer Return)
        idx = _get_position_index(len(returns), scenario.position, scenario.seed)
        stressed.iloc[idx] = stressed.iloc[idx] - scenario.severity

    else:
        raise ValueError(f"Unbekannter Szenario-Typ: {scenario.scenario_type}")

    return stressed


# =============================================================================
# STRESS TEST SUITE
# =============================================================================


def run_stress_test_suite(
    returns: pd.Series,
    scenarios: Iterable[StressScenarioConfig],
    stats_fn: Callable[[pd.Series], dict[str, float]],
) -> StressTestSuiteResult:
    """
    Führt eine Suite von Stress-Szenarien auf einer Baseline-Return-Serie aus.

    Args:
        returns: Baseline-Returns-Serie
        scenarios: Iterable von StressScenarioConfig
        stats_fn: Funktion, die aus Returns Kennzahlen berechnet
                  (z.B. Wrapper um compute_basic_stats)

    Returns:
        StressTestSuiteResult mit allen Ergebnissen

    Example:
        >>> from src.backtest.stats import compute_basic_stats
        >>> def stats_fn(returns_series: pd.Series) -> Dict[str, float]:
        ...     equity = (1 + returns_series).cumprod() * 10000
        ...     return compute_basic_stats(equity)
        >>>
        >>> returns = pd.Series([0.01, -0.02, 0.015, ...])
        >>> scenarios = [
        ...     StressScenarioConfig("single_crash_bar", severity=0.2),
        ...     StressScenarioConfig("vol_spike", severity=0.5),
        ... ]
        >>> suite = run_stress_test_suite(returns, scenarios, stats_fn)
        >>> print(f"Baseline Sharpe: {suite.baseline_metrics['sharpe']:.2f}")
    """
    if len(returns) < 2:
        raise ValueError(f"Returns-Serie muss mindestens 2 Werte haben, got {len(returns)}")

    # Berechne Baseline-Metriken
    logger.info("Berechne Baseline-Metriken...")
    baseline_metrics = stats_fn(returns)

    # Führe Szenarien durch
    scenario_results: list[StressScenarioResult] = []

    for scenario in scenarios:
        logger.info(f"Führe Szenario aus: {scenario.scenario_type} (severity={scenario.severity})")

        # Wende Szenario an
        stressed_returns = apply_stress_scenario_to_returns(returns, scenario)

        # Berechne gestresste Metriken
        try:
            stressed_metrics = stats_fn(stressed_returns)
        except Exception as e:
            logger.warning(f"Fehler bei Berechnung der gestressten Metriken: {e}, überspringe Szenario")
            continue

        # Berechne Differenzen
        diff_metrics: dict[str, float] = {}
        for key in set(baseline_metrics.keys()) | set(stressed_metrics.keys()):
            baseline_val = baseline_metrics.get(key, 0.0)
            stressed_val = stressed_metrics.get(key, 0.0)
            diff_metrics[key] = stressed_val - baseline_val

        scenario_results.append(
            StressScenarioResult(
                scenario=scenario,
                baseline_metrics=baseline_metrics.copy(),
                stressed_metrics=stressed_metrics,
                diff_metrics=diff_metrics,
            )
        )

    logger.info(f"Stress-Test-Suite abgeschlossen: {len(scenario_results)} Szenarien durchgeführt")

    return StressTestSuiteResult(
        returns=returns,
        baseline_metrics=baseline_metrics,
        scenario_results=scenario_results,
    )


# =============================================================================
# INTEGRATION WITH REGISTRY / TOP-N
# =============================================================================


def load_returns_for_top_config(
    sweep_name: str,
    config_rank: int,
    experiments_dir: Path,
    *,
    use_dummy_data: bool = False,
    dummy_bars: int = 500,
) -> pd.Series | None:
    """
    Lädt Returns für eine Top-N-Konfiguration aus einem Sweep.

    Args:
        sweep_name: Name des Sweeps
        config_rank: Rank der Konfiguration (1 = best, 2 = second-best, ...)
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen
        use_dummy_data: Wenn True, werden Dummy-Daten verwendet
        dummy_bars: Anzahl Bars für Dummy-Daten

    Returns:
        Returns-Serie oder None

    Note:
        Aktuell ist dies eine vereinfachte Implementierung. In einer vollständigen
        Implementierung würde man die Equity-Curves aus den Backtest-Result-Objekten
        laden. Für Phase 46 verwenden wir Dummy-Daten oder Approximationen.
    """
    if use_dummy_data:
        logger.info(f"Verwende Dummy-Daten für Config Rank {config_rank}")
        np.random.seed(42 + config_rank)
        n = dummy_bars
        returns = np.random.normal(0.0005, 0.02, n)
        dates = pd.date_range("2024-01-01", periods=n, freq="1h")
        return pd.Series(returns, index=dates)

    # NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (Eintrag "Vollständige Stress-Test-Implementierung")
    logger.warning(
        f"load_returns_for_top_config ist noch nicht vollständig implementiert "
        f"für sweep_name={sweep_name}, config_rank={config_rank}. "
        f"Verwende Dummy-Daten als Fallback."
    )
    np.random.seed(42 + config_rank)
    n = dummy_bars
    returns = np.random.normal(0.0005, 0.02, n)
    dates = pd.date_range("2024-01-01", periods=n, freq="1h")
    return pd.Series(returns, index=dates)
