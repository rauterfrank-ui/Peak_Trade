# tests/test_stress_tests.py
"""
Tests für Stress-Tests (Phase 46)
==================================

Tests für:
- apply_stress_scenario_to_returns (alle Szenario-Typen)
- run_stress_test_suite
- StressScenarioConfig Validierung
"""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.experiments.stress_tests import (
    StressScenarioConfig,
    StressScenarioResult,
    StressTestSuiteResult,
    apply_stress_scenario_to_returns,
    run_stress_test_suite,
    load_returns_for_top_config,
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
def sample_stats_fn():
    """Erstellt eine einfache Stats-Funktion für Tests."""
    from src.backtest import stats as stats_mod

    def stats_fn(returns_series: pd.Series) -> dict[str, float]:
        equity = (1 + returns_series).cumprod() * 10000
        stats = stats_mod.compute_basic_stats(equity)
        if len(returns_series) > 0:
            stats["volatility"] = float(returns_series.std() * np.sqrt(252))
            stats["mean_return"] = float(returns_series.mean() * 252)
        return stats

    return stats_fn


# =============================================================================
# CONFIG TESTS
# =============================================================================


def test_stress_scenario_config_defaults():
    """Testet Standard-Konfiguration."""
    config = StressScenarioConfig(scenario_type="single_crash_bar")
    assert config.scenario_type == "single_crash_bar"
    assert config.severity == 0.2
    assert config.window == 5
    assert config.position == "middle"
    assert config.seed == 42


def test_stress_scenario_config_custom():
    """Testet benutzerdefinierte Konfiguration."""
    config = StressScenarioConfig(
        scenario_type="vol_spike",
        severity=0.3,
        window=10,
        position="end",
        seed=123,
    )
    assert config.scenario_type == "vol_spike"
    assert config.severity == 0.3
    assert config.window == 10
    assert config.position == "end"
    assert config.seed == 123


def test_stress_scenario_config_validation():
    """Testet Validierung der Konfiguration."""
    # severity <= 0
    with pytest.raises(ValueError, match="severity muss > 0"):
        StressScenarioConfig(scenario_type="single_crash_bar", severity=0)

    # window < 1
    with pytest.raises(ValueError, match="window muss >= 1"):
        StressScenarioConfig(scenario_type="vol_spike", window=0)


# =============================================================================
# SCENARIO TRANSFORM TESTS
# =============================================================================


def test_single_crash_bar(sample_returns):
    """Testet single_crash_bar Szenario."""
    scenario = StressScenarioConfig(
        scenario_type="single_crash_bar",
        severity=0.2,
        position="middle",
    )

    stressed = apply_stress_scenario_to_returns(sample_returns, scenario)

    # Prüfe, dass genau eine Bar deutlich negativer geworden ist
    middle_idx = len(sample_returns) // 2
    assert stressed.iloc[middle_idx] == -0.2

    # Andere Bars sollten unverändert sein
    for i in range(len(sample_returns)):
        if i != middle_idx:
            assert stressed.iloc[i] == pytest.approx(sample_returns.iloc[i])


def test_single_crash_bar_start(sample_returns):
    """Testet single_crash_bar an Start-Position."""
    scenario = StressScenarioConfig(
        scenario_type="single_crash_bar",
        severity=0.15,
        position="start",
    )

    stressed = apply_stress_scenario_to_returns(sample_returns, scenario)
    assert stressed.iloc[0] == -0.15


def test_single_crash_bar_end(sample_returns):
    """Testet single_crash_bar an End-Position."""
    scenario = StressScenarioConfig(
        scenario_type="single_crash_bar",
        severity=0.25,
        position="end",
    )

    stressed = apply_stress_scenario_to_returns(sample_returns, scenario)
    assert stressed.iloc[-1] == -0.25


def test_vol_spike(sample_returns):
    """Testet vol_spike Szenario."""
    scenario = StressScenarioConfig(
        scenario_type="vol_spike",
        severity=0.5,  # 50% Erhöhung
        window=5,
        position="middle",
    )

    stressed = apply_stress_scenario_to_returns(sample_returns, scenario)

    # Prüfe, dass die Standardabweichung im betroffenen Fenster steigt
    middle_idx = len(sample_returns) // 2
    start_idx = max(0, middle_idx - 2)
    end_idx = min(len(sample_returns), middle_idx + 3)

    original_window = sample_returns.iloc[start_idx:end_idx]
    stressed_window = stressed.iloc[start_idx:end_idx]

    # Volatilität sollte gestiegen sein
    assert stressed_window.std() > original_window.std()


def test_drawdown_extension(sample_returns):
    """Testet drawdown_extension Szenario."""
    scenario = StressScenarioConfig(
        scenario_type="drawdown_extension",
        severity=0.3,
        window=10,
        position="middle",
    )

    stressed = apply_stress_scenario_to_returns(sample_returns, scenario)

    # Prüfe, dass negative Returns verstärkt wurden
    # (genaue Prüfung hängt von der Drawdown-Phase ab)
    assert len(stressed) == len(sample_returns)


def test_gap_down_open(sample_returns):
    """Testet gap_down_open Szenario."""
    scenario = StressScenarioConfig(
        scenario_type="gap_down_open",
        severity=0.1,
        position="middle",
    )

    original_middle = sample_returns.iloc[len(sample_returns) // 2]
    stressed = apply_stress_scenario_to_returns(sample_returns, scenario)

    # Gap sollte additiv sein
    middle_idx = len(sample_returns) // 2
    expected = original_middle - 0.1
    assert stressed.iloc[middle_idx] == pytest.approx(expected)


def test_empty_returns():
    """Testet Edge-Case: leere Returns-Serie."""
    empty_returns = pd.Series([], dtype=float)
    scenario = StressScenarioConfig(scenario_type="single_crash_bar")

    stressed = apply_stress_scenario_to_returns(empty_returns, scenario)
    assert len(stressed) == 0


def test_single_return():
    """Testet Edge-Case: nur ein Return."""
    single_return = pd.Series([0.01])
    scenario = StressScenarioConfig(
        scenario_type="single_crash_bar",
        severity=0.2,
        position="middle",
    )

    stressed = apply_stress_scenario_to_returns(single_return, scenario)
    assert len(stressed) == 1
    assert stressed.iloc[0] == -0.2


# =============================================================================
# STRESS TEST SUITE TESTS
# =============================================================================


def test_run_stress_test_suite(sample_returns, sample_stats_fn):
    """Testet run_stress_test_suite."""
    scenarios = [
        StressScenarioConfig(scenario_type="single_crash_bar", severity=0.2),
        StressScenarioConfig(scenario_type="vol_spike", severity=0.5),
    ]

    suite = run_stress_test_suite(sample_returns, scenarios, sample_stats_fn)

    # Prüfe Struktur
    assert isinstance(suite, StressTestSuiteResult)
    assert len(suite.returns) == len(sample_returns)
    assert len(suite.baseline_metrics) > 0
    assert len(suite.scenario_results) == 2

    # Prüfe Baseline-Metriken
    assert "sharpe" in suite.baseline_metrics or "total_return" in suite.baseline_metrics

    # Prüfe Szenario-Ergebnisse
    for result in suite.scenario_results:
        assert isinstance(result, StressScenarioResult)
        assert len(result.baseline_metrics) > 0
        assert len(result.stressed_metrics) > 0
        assert len(result.diff_metrics) > 0

        # Prüfe, dass diff_metrics = stressed - baseline
        for key in result.diff_metrics:
            baseline_val = result.baseline_metrics.get(key, 0.0)
            stressed_val = result.stressed_metrics.get(key, 0.0)
            expected_diff = stressed_val - baseline_val
            assert result.diff_metrics[key] == pytest.approx(expected_diff)


def test_run_stress_test_suite_empty_scenarios(sample_returns, sample_stats_fn):
    """Testet run_stress_test_suite mit leerer Szenario-Liste."""
    suite = run_stress_test_suite(sample_returns, [], sample_stats_fn)

    assert len(suite.scenario_results) == 0
    assert len(suite.baseline_metrics) > 0


def test_run_stress_test_suite_too_short():
    """Testet run_stress_test_suite mit zu kurzer Returns-Serie."""
    short_returns = pd.Series([0.01])
    scenarios = [StressScenarioConfig(scenario_type="single_crash_bar")]

    from src.backtest import stats as stats_mod

    def stats_fn(returns_series: pd.Series) -> dict[str, float]:
        equity = (1 + returns_series).cumprod() * 10000
        return stats_mod.compute_basic_stats(equity)

    with pytest.raises(ValueError, match="muss mindestens 2 Werte haben"):
        run_stress_test_suite(short_returns, scenarios, stats_fn)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


def test_load_returns_for_top_config_dummy():
    """Testet load_returns_for_top_config mit Dummy-Daten."""
    returns = load_returns_for_top_config(
        sweep_name="test_sweep",
        config_rank=1,
        experiments_dir=Path("reports/experiments"),
        use_dummy_data=True,
        dummy_bars=100,
    )

    assert returns is not None
    assert len(returns) == 100
    assert isinstance(returns.index, pd.DatetimeIndex)







