"""
Tests for Stress Testing (src/risk/stress.py)
"""

import pytest
import pandas as pd
import numpy as np

from src.risk.stress import (
    StressScenario,
    apply_scenario_to_returns,
    run_stress_suite,
)


class TestStressScenario:
    """Tests for StressScenario dataclass"""

    def test_valid_scenario_creation(self):
        """Valid scenario sollte korrekt erstellt werden"""
        scenario = StressScenario(name="crash", kind="shock", params={"shock_pct": -0.20})
        assert scenario.name == "crash"
        assert scenario.kind == "shock"
        assert scenario.params["shock_pct"] == -0.20

    def test_invalid_kind_raises(self):
        """Invalid kind sollte ValueError werfen"""
        with pytest.raises(ValueError, match="Invalid scenario kind"):
            StressScenario(name="invalid", kind="unknown_type", params={})


class TestApplyScenarioShock:
    """Tests for shock scenario"""

    def test_shock_reduces_returns(self):
        """Shock sollte Returns nach unten verschieben"""
        returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        scenario = StressScenario(
            name="crash", kind="shock", params={"shock_pct": -0.20, "days": 5}
        )

        stressed = apply_scenario_to_returns(returns, scenario)

        # Shock von -20% über 5 Tage verteilt = -4% pro Tag
        # Erste 5 Returns sollten um -0.04 reduziert sein
        expected_first = 0.01 - 0.04  # -0.03
        assert stressed.iloc[0] == pytest.approx(expected_first, abs=1e-6)

    def test_shock_single_day(self):
        """Shock an einem Tag"""
        returns = pd.Series([0.01, 0.02, 0.03])
        scenario = StressScenario(name="crash", kind="shock", params={"shock_pct": -0.10})

        stressed = apply_scenario_to_returns(returns, scenario)

        # Shock von -10% an Tag 0
        assert stressed.iloc[0] == pytest.approx(0.01 - 0.10, abs=1e-6)
        assert stressed.iloc[1] == pytest.approx(0.02, abs=1e-6)  # unverändert


class TestApplyScenarioVolSpike:
    """Tests for vol_spike scenario"""

    def test_vol_spike_increases_std(self):
        """Vol-Spike sollte Standardabweichung erhöhen"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.01, 100))
        original_std = returns.std()

        scenario = StressScenario(
            name="vol_spike", kind="vol_spike", params={"multiplier": 3.0}
        )

        stressed = apply_scenario_to_returns(returns, scenario)
        stressed_std = stressed.std()

        # Std sollte ~3x größer sein
        assert stressed_std > original_std * 2.5
        assert stressed_std < original_std * 3.5

    def test_vol_spike_preserves_mean(self):
        """Vol-Spike sollte Mean ungefähr erhalten"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.01, 0.02, 100))
        original_mean = returns.mean()

        scenario = StressScenario(name="vol", kind="vol_spike", params={"multiplier": 2.0})

        stressed = apply_scenario_to_returns(returns, scenario)
        stressed_mean = stressed.mean()

        # Mean sollte ungefähr gleich bleiben
        assert abs(stressed_mean - original_mean) < 0.005


class TestApplyScenarioFlashCrash:
    """Tests for flash_crash scenario"""

    def test_flash_crash_creates_large_drawdown(self):
        """Flash-Crash sollte extremen negativen Return erzeugen"""
        returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        scenario = StressScenario(
            name="crash", kind="flash_crash", params={"crash_pct": -0.30, "recovery_days": 10}
        )

        stressed = apply_scenario_to_returns(returns, scenario)

        # Erster Tag sollte Crash haben
        assert stressed.iloc[0] == pytest.approx(-0.30, abs=1e-6)

    def test_flash_crash_recovery(self):
        """Flash-Crash sollte Recovery-Phase haben"""
        returns = pd.Series([0.01] * 20)
        scenario = StressScenario(
            name="crash", kind="flash_crash", params={"crash_pct": -0.20, "recovery_days": 10}
        )

        stressed = apply_scenario_to_returns(returns, scenario)

        # Recovery-Returns sollten positiv sein (0.20 / 10 = 0.02 pro Tag)
        assert stressed.iloc[1] == pytest.approx(0.02, abs=1e-6)


class TestApplyScenarioRegimeBear:
    """Tests for regime_bear scenario"""

    def test_regime_bear_negative_drift(self):
        """Bear-Regime sollte negativen Drift hinzufügen"""
        returns = pd.Series([0.01] * 10)
        scenario = StressScenario(
            name="bear", kind="regime_bear", params={"drift_pct": -0.02, "duration_days": 10}
        )

        stressed = apply_scenario_to_returns(returns, scenario)

        # Alle Returns sollten um -0.02 reduziert sein
        expected = pd.Series([0.01 - 0.02] * 10)
        pd.testing.assert_series_equal(stressed, expected, check_names=False)


class TestApplyScenarioRegimeSideways:
    """Tests for regime_sideways scenario"""

    def test_regime_sideways_increases_volatility(self):
        """Sideways-Regime sollte Volatilität erhöhen"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.01, 0.01, 50))
        original_std = returns.std()

        scenario = StressScenario(
            name="sideways",
            kind="regime_sideways",
            params={"chop_factor": 2.0, "duration_days": 50},
        )

        stressed = apply_scenario_to_returns(returns, scenario)
        stressed_std = stressed.std()

        # Std sollte größer sein
        assert stressed_std > original_std

    def test_regime_sideways_removes_trend(self):
        """Sideways-Regime sollte Trend entfernen"""
        # Trend-Returns (steigend)
        returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        original_mean = returns.mean()

        scenario = StressScenario(
            name="sideways",
            kind="regime_sideways",
            params={"chop_factor": 1.0, "duration_days": 5},
        )

        stressed = apply_scenario_to_returns(returns, scenario)

        # Mean sollte ~0 sein (Trend entfernt)
        assert abs(stressed.mean()) < abs(original_mean)


class TestRunStressSuite:
    """Tests for run_stress_suite()"""

    def test_stress_suite_returns_dataframe(self):
        """Stress-Suite sollte DataFrame zurückgeben"""
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        scenarios = [
            StressScenario("baseline", "shock", {"shock_pct": 0.0}),
            StressScenario("crash", "shock", {"shock_pct": -0.20}),
        ]

        results = run_stress_suite(returns, scenarios, alpha=0.05)

        assert isinstance(results, pd.DataFrame)
        assert len(results) == 2

    def test_stress_suite_columns(self):
        """Stress-Suite sollte erwartete Spalten haben"""
        returns = pd.Series([0.01, -0.02, 0.03])
        scenarios = [StressScenario("test", "shock", {"shock_pct": -0.10})]

        results = run_stress_suite(returns, scenarios, alpha=0.05)

        expected_cols = [
            "scenario",
            "kind",
            "var",
            "cvar",
            "mean",
            "std",
            "min",
            "max",
            "total_return",
        ]
        for col in expected_cols:
            assert col in results.columns

    def test_stress_suite_baseline_vs_crash(self):
        """Crash-Szenario sollte höheren VaR haben als Baseline"""
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        scenarios = [
            StressScenario("baseline", "shock", {"shock_pct": 0.0}),
            StressScenario("crash", "shock", {"shock_pct": -0.20}),
        ]

        results = run_stress_suite(returns, scenarios, alpha=0.05)

        baseline_var = results[results["scenario"] == "baseline"]["var"].iloc[0]
        crash_var = results[results["scenario"] == "crash"]["var"].iloc[0]

        assert crash_var > baseline_var, "Crash sollte höheren VaR haben"

    def test_stress_suite_cvar_geq_var(self):
        """CVaR sollte >= VaR für alle Szenarien"""
        returns = pd.Series([-0.01, -0.02, -0.03, -0.04, -0.05])
        scenarios = [
            StressScenario("s1", "shock", {"shock_pct": -0.10}),
            StressScenario("s2", "vol_spike", {"multiplier": 2.0}),
        ]

        results = run_stress_suite(returns, scenarios, alpha=0.05)

        for _, row in results.iterrows():
            assert row["cvar"] >= row["var"], f"CVaR < VaR for {row['scenario']}"

    def test_stress_suite_empty_returns(self):
        """Leere Returns sollten leeres DataFrame zurückgeben"""
        returns = pd.Series(dtype=float)
        scenarios = [StressScenario("test", "shock", {"shock_pct": -0.10})]

        results = run_stress_suite(returns, scenarios, alpha=0.05)

        assert results.empty


class TestScenarioEdgeCases:
    """Edge Cases für Szenarien"""

    def test_empty_returns_series(self):
        """Leere Returns sollten unverändert zurückgegeben werden"""
        returns = pd.Series(dtype=float)
        scenario = StressScenario("test", "shock", {"shock_pct": -0.10})

        stressed = apply_scenario_to_returns(returns, scenario)

        assert stressed.empty

    def test_single_return_value(self):
        """Single Return sollte korrekt verarbeitet werden"""
        returns = pd.Series([0.01])
        scenario = StressScenario("test", "shock", {"shock_pct": -0.05})

        stressed = apply_scenario_to_returns(returns, scenario)

        assert stressed.iloc[0] == pytest.approx(0.01 - 0.05, abs=1e-6)

    def test_unknown_scenario_kind(self):
        """Unknown scenario kind sollte unveränderte Returns zurückgeben"""
        returns = pd.Series([0.01, 0.02])

        # Erstelle Szenario durch direkten Zugriff (umgeht Validation)
        scenario = StressScenario.__new__(StressScenario)
        scenario.name = "unknown"
        scenario.kind = "unknown_type_bypass"
        scenario.params = {}
        scenario.description = ""

        stressed = apply_scenario_to_returns(returns, scenario)

        # Sollte unverändert bleiben
        pd.testing.assert_series_equal(stressed, returns, check_names=False)

