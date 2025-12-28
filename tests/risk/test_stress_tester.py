"""
Tests for Portfolio Stress Tester
==================================
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.risk.stress_tester import (
    StressTester,
    StressScenarioData,
    StressTestResult,
    ReverseStressResult,
)


class TestStressScenarioData:
    """Tests for StressScenarioData."""

    def test_from_json(self, tmp_path):
        """Load scenario from JSON."""
        scenario_file = tmp_path / "test_scenario.json"
        scenario_data = {
            "name": "Test Crash",
            "date": "2020-03-12",
            "description": "Test scenario",
            "asset_shocks": {
                "BTC-EUR": -0.50,
                "ETH-EUR": -0.60,
                "default": -0.40,
            },
            "probability": "rare",
            "historical_frequency": "once_per_decade",
        }

        with open(scenario_file, "w") as f:
            json.dump(scenario_data, f)

        scenario = StressScenarioData.from_json(scenario_file)

        assert scenario.name == "Test Crash"
        assert scenario.date == "2020-03-12"
        assert scenario.asset_shocks["BTC-EUR"] == -0.50
        assert scenario.default_shock == -0.40
        assert "default" not in scenario.asset_shocks  # Should be removed


class TestStressTesterInit:
    """Tests for StressTester initialization."""

    def test_init_with_scenarios_dir(self):
        """Initialize with existing scenarios directory."""
        tester = StressTester(scenarios_dir="data/scenarios")

        assert tester.scenarios_dir == Path("data/scenarios")
        assert len(tester.scenarios) > 0

    def test_init_loads_5_scenarios(self):
        """Should load 5 historical scenarios."""
        tester = StressTester(scenarios_dir="data/scenarios")

        assert len(tester.scenarios) == 5

    def test_init_scenario_names(self):
        """Check loaded scenario names."""
        tester = StressTester(scenarios_dir="data/scenarios")

        scenario_names = [s.name for s in tester.scenarios]

        # Should include all 5 historical scenarios
        assert any("COVID" in name for name in scenario_names)
        assert any("China" in name or "Mining" in name for name in scenario_names)
        assert any("LUNA" in name or "Terra" in name for name in scenario_names)
        assert any("FTX" in name for name in scenario_names)
        assert any("2018" in name or "Winter" in name for name in scenario_names)

    def test_init_nonexistent_dir(self, tmp_path):
        """Initialize with non-existent directory."""
        nonexistent = tmp_path / "nonexistent"
        tester = StressTester(scenarios_dir=str(nonexistent))

        # Should not raise, but have no scenarios
        assert len(tester.scenarios) == 0


class TestRunStress:
    """Tests for run_stress()."""

    def test_run_stress_basic(self):
        """Basic stress test should work."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
        result = tester.run_stress(weights, portfolio_value=100000)

        assert isinstance(result, StressTestResult)
        assert result.portfolio_value == 100000
        assert result.stressed_value < 100000  # Should have loss
        assert result.portfolio_loss_pct > 0  # Loss is positive
        assert result.portfolio_loss_abs > 0
        assert result.largest_contributor in ["BTC-EUR", "ETH-EUR"]

    def test_run_stress_covid_scenario(self):
        """COVID scenario should produce expected loss."""
        tester = StressTester(scenarios_dir="data/scenarios")

        # Find COVID scenario
        covid_scenario = None
        for s in tester.scenarios:
            if "COVID" in s.name:
                covid_scenario = s
                break

        assert covid_scenario is not None

        # Simple equal weights
        weights = {"BTC-EUR": 0.5, "ETH-EUR": 0.5}
        result = tester.run_stress(
            weights, portfolio_value=100000, scenario_name=covid_scenario.name
        )

        # COVID shocks: BTC -50%, ETH -60%
        # Expected loss: 0.5 * 0.50 + 0.5 * 0.60 = 0.55 (55%)
        expected_loss_pct = 0.5 * 0.50 + 0.5 * 0.60

        assert abs(result.portfolio_loss_pct - expected_loss_pct) < 0.01
        assert result.stressed_value == 100000 * (1 - expected_loss_pct)

    def test_run_stress_default_shock(self):
        """Default shock should be applied for missing assets."""
        tester = StressTester(scenarios_dir="data/scenarios")

        # Use asset not in scenario
        weights = {"XYZ-EUR": 1.0}
        result = tester.run_stress(weights, portfolio_value=100000)

        # Should use default shock
        assert result.portfolio_loss_pct > 0
        assert result.portfolio_loss_abs > 0

    def test_run_stress_asset_losses(self):
        """Asset losses should sum to total loss."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
        result = tester.run_stress(weights, portfolio_value=100000)

        # Sum of asset losses should equal total loss
        total_asset_losses = sum(result.asset_losses.values())

        assert abs(total_asset_losses - result.portfolio_loss_abs) < 0.01

    def test_run_stress_largest_contributor(self):
        """Largest contributor should be correct."""
        tester = StressTester(scenarios_dir="data/scenarios")

        # BTC has higher weight -> should be largest contributor
        weights = {"BTC-EUR": 0.9, "ETH-EUR": 0.1}
        result = tester.run_stress(weights, portfolio_value=100000)

        # BTC should be largest contributor
        assert result.largest_contributor == "BTC-EUR"

    def test_run_stress_weights_normalization(self):
        """Weights should be normalized if they don't sum to 1."""
        tester = StressTester(scenarios_dir="data/scenarios")

        # Weights don't sum to 1
        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.6}  # sum = 1.2

        result = tester.run_stress(weights, portfolio_value=100000)

        # Should not raise error
        assert result.portfolio_loss_pct > 0


class TestRunAllScenarios:
    """Tests for run_all_scenarios()."""

    def test_run_all_scenarios(self):
        """Run all scenarios should return 5 results."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
        results = tester.run_all_scenarios(weights, portfolio_value=100000)

        assert len(results) == 5
        assert all(isinstance(r, StressTestResult) for r in results)

    def test_run_all_scenarios_different_losses(self):
        """Different scenarios should produce different losses."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
        results = tester.run_all_scenarios(weights, portfolio_value=100000)

        losses = [r.portfolio_loss_pct for r in results]

        # All losses should be positive
        assert all(loss > 0 for loss in losses)

        # Not all losses should be identical
        assert len(set(losses)) > 1


class TestReverseStress:
    """Tests for reverse_stress()."""

    def test_reverse_stress_uniform_shock(self):
        """Uniform shock should match target loss."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.5, "ETH-EUR": 0.5}
        target_loss = 0.20  # 20% loss

        result = tester.reverse_stress(weights, target_loss_pct=target_loss)

        assert isinstance(result, ReverseStressResult)
        assert result.target_loss_pct == target_loss

        # Uniform shock: s = target_loss / sum(weights) = target_loss / 1.0
        expected_uniform_shock = -target_loss
        assert abs(result.uniform_shock - expected_uniform_shock) < 0.01

    def test_reverse_stress_btc_shock(self):
        """BTC-specific shock should match target loss."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.5, "ETH-EUR": 0.5}
        target_loss = 0.30  # 30% loss

        result = tester.reverse_stress(weights, target_loss_pct=target_loss)

        # BTC shock: s_btc = target_loss / w_btc = 0.30 / 0.5 = 0.60
        expected_btc_shock = -target_loss / weights["BTC-EUR"]

        assert result.btc_shock is not None
        assert abs(result.btc_shock - expected_btc_shock) < 0.01

    def test_reverse_stress_no_btc(self):
        """Should handle portfolios without BTC."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"ETH-EUR": 0.6, "XRP-EUR": 0.4}
        target_loss = 0.15

        result = tester.reverse_stress(weights, target_loss_pct=target_loss)

        # No BTC in portfolio -> btc_shock should be None
        assert result.btc_shock is None

    def test_reverse_stress_probability_assessment(self):
        """Probability assessment should be qualitative."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.5, "ETH-EUR": 0.5}

        # Small loss -> Common
        result_small = tester.reverse_stress(weights, target_loss_pct=0.05)
        assert "Common" in result_small.probability_assessment

        # Large loss -> Extreme
        result_large = tester.reverse_stress(weights, target_loss_pct=0.60)
        assert "Extreme" in result_large.probability_assessment

    def test_reverse_stress_comparable_scenarios(self):
        """Should find comparable historical scenarios."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.5, "ETH-EUR": 0.5}
        target_loss = 0.55  # ~55% loss (close to COVID scenario)

        result = tester.reverse_stress(weights, target_loss_pct=target_loss)

        # Should have some comparable scenarios
        assert isinstance(result.comparable_scenarios, list)


class TestReportGeneration:
    """Tests for report generation."""

    def test_generate_markdown_report(self):
        """Markdown report should be generated."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
        results = tester.run_all_scenarios(weights, portfolio_value=100000)

        report = tester.generate_report(results, format="markdown")

        assert "# Portfolio Stress Test Report" in report
        assert "Total Scenarios" in report
        assert "$" in report  # Should have dollar amounts

    def test_generate_html_report(self):
        """HTML report should be generated."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
        results = tester.run_all_scenarios(weights, portfolio_value=100000)

        report = tester.generate_report(results, format="html")

        assert "<!DOCTYPE html>" in report
        assert "<table>" in report
        assert "<th>" in report

    def test_generate_json_report(self):
        """JSON report should be generated."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
        results = tester.run_all_scenarios(weights, portfolio_value=100000)

        report = tester.generate_report(results, format="json")

        # Should be valid JSON
        import json

        parsed = json.loads(report)
        assert "total_scenarios" in parsed
        assert "results" in parsed
        assert len(parsed["results"]) == 5


class TestStressTestResultSummary:
    """Tests for StressTestResult.summary()."""

    def test_summary_format(self):
        """Summary should return formatted dict."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}
        result = tester.run_stress(weights, portfolio_value=100000)

        summary = result.summary()

        assert "scenario" in summary
        assert "portfolio_value" in summary
        assert "loss_pct" in summary
        assert "$" in summary["portfolio_value"]
        assert "%" in summary["loss_pct"]


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_run_stress_determinism(self):
        """Same inputs should give same outputs."""
        tester1 = StressTester(scenarios_dir="data/scenarios")
        tester2 = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.6, "ETH-EUR": 0.4}

        result1 = tester1.run_stress(weights, portfolio_value=100000)
        result2 = tester2.run_stress(weights, portfolio_value=100000)

        assert result1.portfolio_loss_pct == result2.portfolio_loss_pct
        assert result1.stressed_value == result2.stressed_value

    def test_reverse_stress_determinism(self):
        """Same inputs should give same outputs."""
        tester = StressTester(scenarios_dir="data/scenarios")

        weights = {"BTC-EUR": 0.5, "ETH-EUR": 0.5}

        result1 = tester.reverse_stress(weights, target_loss_pct=0.20)
        result2 = tester.reverse_stress(weights, target_loss_pct=0.20)

        assert result1.uniform_shock == result2.uniform_shock
        assert result1.btc_shock == result2.btc_shock
