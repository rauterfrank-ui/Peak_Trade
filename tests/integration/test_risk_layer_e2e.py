"""
End-to-End Integration Tests for Risk Layer v1.0
=================================================

Agent A6 Implementation: Full risk assessment smoke tests.
"""

import numpy as np
import pandas as pd
import pytest

from src.risk import RiskLayerManager, RiskAssessmentResult


@pytest.fixture
def synthetic_returns():
    """Generate synthetic returns for testing."""
    np.random.seed(42)
    n_days = 500

    returns = pd.DataFrame(
        {
            "BTC-EUR": np.random.randn(n_days) * 0.03 + 0.0005,
            "ETH-EUR": np.random.randn(n_days) * 0.04 + 0.0003,
            "SOL-EUR": np.random.randn(n_days) * 0.05 + 0.0002,
        }
    )

    return returns


@pytest.fixture
def portfolio_weights():
    """Standard portfolio weights."""
    return {"BTC-EUR": 0.5, "ETH-EUR": 0.3, "SOL-EUR": 0.2}


@pytest.fixture
def config_all_enabled():
    """Config with all features enabled."""
    return {
        "risk_layer_v1": {
            "enabled": True,
            "var": {
                "enabled": True,
                "methods": ["historical", "parametric", "ewma"],
                "confidence_level": 0.95,
                "window": 252,
            },
            "component_var": {"enabled": True},
            "monte_carlo": {
                "enabled": True,
                "n_simulations": 1000,  # Small for testing
                "method": "normal",
                "seed": 42,
            },
            "stress_test": {
                "enabled": True,
                "scenarios_dir": "data/scenarios",
            },
            "backtest": {"enabled": False},  # Skip for E2E
        }
    }


@pytest.fixture
def config_disabled():
    """Config with Risk Layer disabled."""
    return {
        "risk_layer_v1": {
            "enabled": False,
        }
    }


class TestRiskLayerManagerInit:
    """Tests for RiskLayerManager initialization."""

    def test_init_all_enabled(self, config_all_enabled):
        """Initialize with all features enabled."""
        manager = RiskLayerManager(config_all_enabled)

        assert manager.enabled is True
        assert manager.var_enabled is True
        assert manager.component_var_enabled is True
        assert manager.monte_carlo_enabled is True
        assert manager.stress_test_enabled is True

        assert "var" in manager.enabled_features
        assert "component_var" in manager.enabled_features
        assert "monte_carlo" in manager.enabled_features
        assert "stress_test" in manager.enabled_features

    def test_init_disabled(self, config_disabled):
        """Initialize with Risk Layer disabled."""
        manager = RiskLayerManager(config_disabled)

        assert manager.enabled is False
        assert len(manager.enabled_features) == 0


class TestFullRiskAssessment:
    """Tests for full_risk_assessment()."""

    def test_full_assessment_all_enabled(
        self, config_all_enabled, synthetic_returns, portfolio_weights
    ):
        """Full assessment with all features enabled."""
        manager = RiskLayerManager(config_all_enabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
            alpha=0.05,
        )

        assert isinstance(assessment, RiskAssessmentResult)

        # VaR should be calculated
        assert len(assessment.var) > 0
        assert "historical" in assessment.var
        assert "parametric" in assessment.var
        assert "ewma" in assessment.var

        # CVaR should be calculated
        assert len(assessment.cvar) > 0
        assert "historical" in assessment.cvar

        # All values should be positive (losses)
        for method, value in assessment.var.items():
            assert value > 0, f"VaR ({method}) should be positive"

        for method, value in assessment.cvar.items():
            assert value > 0, f"CVaR ({method}) should be positive"

        # Component VaR should be present
        assert assessment.component_var is not None

        # Monte Carlo should be present
        assert assessment.monte_carlo is not None
        assert assessment.monte_carlo.var > 0
        assert assessment.monte_carlo.cvar > 0

        # Stress test should be present
        assert assessment.stress_test is not None
        assert len(assessment.stress_test) == 5  # 5 historical scenarios

    def test_full_assessment_disabled(self, config_disabled, synthetic_returns, portfolio_weights):
        """Full assessment when Risk Layer is disabled."""
        manager = RiskLayerManager(config_disabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        # Should return empty result with warning
        assert len(assessment.var) == 0
        assert assessment.component_var is None
        assert assessment.monte_carlo is None
        assert assessment.stress_test is None
        assert len(assessment.warnings) > 0

    def test_full_assessment_var_only(self, synthetic_returns, portfolio_weights):
        """Full assessment with only VaR enabled."""
        config = {
            "risk_layer_v1": {
                "enabled": True,
                "var": {
                    "enabled": True,
                    "methods": ["historical"],
                },
                "component_var": {"enabled": False},
                "monte_carlo": {"enabled": False},
                "stress_test": {"enabled": False},
                "backtest": {"enabled": False},
            }
        }

        manager = RiskLayerManager(config)
        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        # Only VaR should be present
        assert len(assessment.var) > 0
        assert assessment.component_var is None
        assert assessment.monte_carlo is None
        assert assessment.stress_test is None


class TestCVaRInvariant:
    """Test CVaR >= VaR invariant."""

    def test_cvar_gte_var_all_methods(
        self, config_all_enabled, synthetic_returns, portfolio_weights
    ):
        """CVaR should be >= VaR for all methods."""
        manager = RiskLayerManager(config_all_enabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        for method in assessment.var.keys():
            var = assessment.var[method]
            cvar = assessment.cvar.get(method)

            if cvar is not None:
                assert cvar >= var, f"CVaR ({method}) should be >= VaR"


class TestStressTestIntegration:
    """Test stress testing integration."""

    def test_stress_test_scenarios(self, config_all_enabled, synthetic_returns, portfolio_weights):
        """Stress test should run all scenarios."""
        manager = RiskLayerManager(config_all_enabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        assert assessment.stress_test is not None
        assert len(assessment.stress_test) == 5

        # All scenarios should have losses
        for result in assessment.stress_test:
            assert result.portfolio_loss_pct > 0
            assert result.stressed_value < 100000

    def test_stress_test_covid_scenario(
        self, config_all_enabled, synthetic_returns, portfolio_weights
    ):
        """COVID scenario should be present."""
        manager = RiskLayerManager(config_all_enabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        scenario_names = [s.scenario_name for s in assessment.stress_test]
        assert any("COVID" in name for name in scenario_names)


class TestMonteCarloIntegration:
    """Test Monte Carlo integration."""

    def test_monte_carlo_determinism(self, synthetic_returns, portfolio_weights):
        """Same seed should give same results."""
        config = {
            "risk_layer_v1": {
                "enabled": True,
                "var": {"enabled": False},
                "component_var": {"enabled": False},
                "monte_carlo": {
                    "enabled": True,
                    "n_simulations": 1000,
                    "method": "normal",
                    "seed": 123,
                },
                "stress_test": {"enabled": False},
            }
        }

        manager1 = RiskLayerManager(config)
        assessment1 = manager1.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        manager2 = RiskLayerManager(config)
        assessment2 = manager2.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        assert assessment1.monte_carlo.var == assessment2.monte_carlo.var
        assert assessment1.monte_carlo.cvar == assessment2.monte_carlo.cvar


class TestReportGeneration:
    """Test report generation."""

    def test_generate_markdown_report(
        self, config_all_enabled, synthetic_returns, portfolio_weights
    ):
        """Markdown report should be generated."""
        manager = RiskLayerManager(config_all_enabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        report = manager.generate_report(assessment, format="markdown")

        assert "# Risk Assessment Report" in report
        assert "Value at Risk" in report
        assert "$" in report

    def test_generate_html_report(self, config_all_enabled, synthetic_returns, portfolio_weights):
        """HTML report should be generated."""
        manager = RiskLayerManager(config_all_enabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        report = manager.generate_report(assessment, format="html")

        assert "<!DOCTYPE html>" in report
        assert "<h1>Risk Assessment Report</h1>" in report

    def test_generate_json_report(self, config_all_enabled, synthetic_returns, portfolio_weights):
        """JSON report should be generated."""
        manager = RiskLayerManager(config_all_enabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        report = manager.generate_report(assessment, format="json")

        import json

        parsed = json.loads(report)
        assert "enabled_features" in parsed
        assert "var" in parsed


class TestAssessmentSummary:
    """Test RiskAssessmentResult.summary()."""

    def test_summary_format(self, config_all_enabled, synthetic_returns, portfolio_weights):
        """Summary should return formatted dict."""
        manager = RiskLayerManager(config_all_enabled)

        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        summary = assessment.summary()

        assert "var" in summary
        assert "cvar" in summary
        assert "enabled_features" in summary
        assert "has_component_var" in summary
        assert "has_monte_carlo" in summary
        assert "has_stress_test" in summary


class TestGracefulDegradation:
    """Test graceful degradation when components fail."""

    def test_invalid_scenarios_dir(self, synthetic_returns, portfolio_weights):
        """Should handle invalid scenarios directory gracefully."""
        config = {
            "risk_layer_v1": {
                "enabled": True,
                "var": {"enabled": False},
                "component_var": {"enabled": False},
                "monte_carlo": {"enabled": False},
                "stress_test": {
                    "enabled": True,
                    "scenarios_dir": "/nonexistent/path",
                },
            }
        }

        # Should not raise error
        manager = RiskLayerManager(config)

        # Stress test should be disabled due to initialization failure
        assert "stress_test" not in manager.enabled_features

        # Assessment should still work
        assessment = manager.full_risk_assessment(
            returns_df=synthetic_returns,
            weights=portfolio_weights,
            portfolio_value=100000,
        )

        assert assessment.stress_test is None
