"""Smoke Tests für VaRBacktestRunner (End-to-End)."""

import pandas as pd

from src.risk_layer.var_backtest import (
    KupiecResult,
    VaRBacktestRunner,
)


class TestVaRBacktestRunnerSmoke:
    """Smoke Tests für vollständigen Backtest-Flow."""

    def test_runner_basic_workflow(self):
        """Grundlegender Workflow: Returns → Violations → Kupiec Test."""
        # Setup
        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        returns = pd.Series([-0.01] * 247 + [-0.03] * 3, index=dates)
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.99, min_observations=250)

        # Run
        result = runner.run(returns, var_estimates, symbol="TEST/EUR")

        # Assertions
        assert result.symbol == "TEST/EUR"
        assert result.kupiec.n_observations == 250
        assert result.kupiec.n_violations == 3
        assert result.kupiec.result == KupiecResult.ACCEPT
        assert result.is_valid is True

    def test_runner_with_reject_scenario(self):
        """Zu viele Violations → REJECT."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        returns = pd.Series([-0.01] * 235 + [-0.03] * 15, index=dates)
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.99)

        result = runner.run(returns, var_estimates, symbol="BAD/EUR")

        assert result.kupiec.result == KupiecResult.REJECT
        assert result.is_valid is False
        assert result.kupiec.n_violations == 15  # 6% statt 1%

    def test_runner_with_inconclusive_scenario(self):
        """Zu wenige Daten → INCONCLUSIVE."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        returns = pd.Series([-0.01] * 99 + [-0.03] * 1, index=dates)
        var_estimates = pd.Series([-0.02] * 100, index=dates)

        runner = VaRBacktestRunner(
            confidence_level=0.99, min_observations=250
        )

        result = runner.run(returns, var_estimates, symbol="SHORT/EUR")

        assert result.kupiec.result == KupiecResult.INCONCLUSIVE
        assert result.kupiec.n_observations == 100

    def test_runner_summary_output(self):
        """Summary-Methode liefert erwartete Keys."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        returns = pd.Series([-0.01] * 247 + [-0.03] * 3, index=dates)
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.99)
        result = runner.run(returns, var_estimates, symbol="BTC/EUR")

        summary = result.summary()

        # Prüfe erwartete Keys
        expected_keys = [
            "symbol",
            "period",
            "n_observations",
            "n_violations",
            "expected_rate",
            "observed_rate",
            "violation_ratio",
            "kupiec_lr",
            "p_value",
            "result",
            "is_valid",
        ]

        for key in expected_keys:
            assert key in summary

        assert summary["symbol"] == "BTC/EUR"
        assert summary["is_valid"] is True


class TestVaRBacktestRunnerConfiguration:
    """Tests für verschiedene Konfigurationen."""

    def test_different_confidence_levels(self):
        """Test mit unterschiedlichen Confidence Levels."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        returns = pd.Series([-0.01] * 238 + [-0.03] * 12, index=dates)
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        # 99% VaR: 12 Violations → zu viele (expected ~2.5)
        runner_99 = VaRBacktestRunner(confidence_level=0.99)
        result_99 = runner_99.run(returns, var_estimates)
        assert result_99.kupiec.result == KupiecResult.REJECT

        # 95% VaR: 12 Violations → OK (expected ~12.5)
        runner_95 = VaRBacktestRunner(confidence_level=0.95)
        result_95 = runner_95.run(returns, var_estimates)
        assert result_95.kupiec.result == KupiecResult.ACCEPT

    def test_custom_min_observations(self):
        """Custom min_observations Schwellwert."""
        dates = pd.date_range("2024-01-01", periods=150, freq="D")
        returns = pd.Series([-0.01] * 149 + [-0.03] * 1, index=dates)
        var_estimates = pd.Series([-0.02] * 150, index=dates)

        # Default min_observations=250 → INCONCLUSIVE
        runner_strict = VaRBacktestRunner(min_observations=250)
        result_strict = runner_strict.run(returns, var_estimates)
        assert result_strict.kupiec.result == KupiecResult.INCONCLUSIVE

        # Niedrigerer Schwellwert=100 → Test wird durchgeführt
        runner_lenient = VaRBacktestRunner(min_observations=100)
        result_lenient = runner_lenient.run(returns, var_estimates)
        assert result_lenient.kupiec.result in [
            KupiecResult.ACCEPT,
            KupiecResult.REJECT,
        ]

    def test_var_method_metadata(self):
        """VaR-Methode wird korrekt im Ergebnis gespeichert."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        returns = pd.Series([-0.01] * 247 + [-0.03] * 3, index=dates)
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        runner = VaRBacktestRunner(
            confidence_level=0.99, var_method="parametric"
        )
        result = runner.run(returns, var_estimates)

        assert result.var_method == "parametric"


class TestVaRBacktestRunnerEdgeCases:
    """Edge Cases für Runner."""

    def test_runner_with_nan_values(self):
        """Runner handled NaN-Werte korrekt."""
        dates = pd.date_range("2024-01-01", periods=260, freq="D")
        returns_list = [-0.01] * 250 + [float("nan")] * 10
        returns = pd.Series(returns_list, index=dates)
        var_estimates = pd.Series([-0.02] * 260, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.99)
        result = runner.run(returns, var_estimates)

        # NaNs werden entfernt → 250 Beobachtungen bleiben
        assert result.kupiec.n_observations == 250

    def test_runner_with_misaligned_indices(self):
        """Runner handled misaligned Indices."""
        dates_returns = pd.date_range("2024-01-01", periods=255, freq="D")
        dates_var = pd.date_range("2024-01-03", periods=255, freq="D")

        returns = pd.Series([-0.01] * 255, index=dates_returns)
        var_estimates = pd.Series([-0.02] * 255, index=dates_var)

        runner = VaRBacktestRunner(confidence_level=0.99, min_observations=250)
        result = runner.run(returns, var_estimates)

        # Nur überlappende Daten
        assert result.kupiec.n_observations == 253  # 255 - 2 Tage Differenz

    def test_runner_with_no_violations(self):
        """Keine Violations szenario."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        returns = pd.Series([0.01] * 250, index=dates)  # Nur positive Returns
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.99)
        result = runner.run(returns, var_estimates)

        assert result.kupiec.n_violations == 0
        # Bei 250 Beobachtungen und 99% VaR erwarten wir ~2.5 Violations
        # 0 ist sehr unwahrscheinlich → sollte REJECT sein
        assert result.kupiec.result == KupiecResult.REJECT

    def test_runner_with_all_violations(self):
        """Alle Violations szenario."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        returns = pd.Series([-0.05] * 250, index=dates)  # Alle sehr negativ
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.99)
        result = runner.run(returns, var_estimates)

        assert result.kupiec.n_violations == 250
        assert result.kupiec.result == KupiecResult.REJECT


class TestVaRBacktestRunnerMetadata:
    """Tests für Metadaten im Ergebnis."""

    def test_result_contains_correct_dates(self):
        """start_date und end_date korrekt gesetzt."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        returns = pd.Series([-0.01] * 100, index=dates)
        var_estimates = pd.Series([-0.02] * 100, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.99, min_observations=50)
        result = runner.run(returns, var_estimates)

        assert result.start_date == dates[0]
        assert result.end_date == dates[-1]

    def test_result_contains_confidence_level(self):
        """var_confidence korrekt gesetzt."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")
        returns = pd.Series([-0.01] * 250, index=dates)
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.95)
        result = runner.run(returns, var_estimates)

        assert result.var_confidence == 0.95


class TestVaRBacktestRunnerRealisticScenarios:
    """Tests mit realistischen Marktszenarien."""

    def test_bitcoin_like_volatility(self):
        """Hohe Volatilität wie bei Bitcoin."""
        dates = pd.date_range("2024-01-01", periods=365, freq="D")

        # Simuliere hohe Volatilität: viele kleine Bewegungen + wenige Extremereignisse
        returns_list = [-0.01] * 360 + [-0.05] * 5
        returns = pd.Series(returns_list, index=dates)
        var_estimates = pd.Series([-0.03] * 365, index=dates)  # 3% VaR

        runner = VaRBacktestRunner(confidence_level=0.99)
        result = runner.run(returns, var_estimates, symbol="BTC/EUR")

        assert result.kupiec.n_observations == 365
        assert result.kupiec.n_violations == 5  # ~1.4%

    def test_low_volatility_stablecoin(self):
        """Niedrige Volatilität wie bei Stablecoins."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")

        # Sehr geringe Schwankungen
        returns_list = [-0.0001] * 250
        returns = pd.Series(returns_list, index=dates)
        var_estimates = pd.Series([-0.002] * 250, index=dates)

        runner = VaRBacktestRunner(confidence_level=0.99)
        result = runner.run(returns, var_estimates)

        assert result.kupiec.n_violations == 0  # Keine Violations bei Stablecoin
