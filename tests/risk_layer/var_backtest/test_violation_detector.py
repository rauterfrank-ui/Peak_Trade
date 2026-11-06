"""Unit Tests für VaR Violation Detector."""

import pandas as pd

from src.risk_layer.var_backtest.violation_detector import (
    detect_violations,
)


class TestViolationDetectorBasic:
    """Grundlegende Violation Detection Tests."""

    def test_simple_violation_detection(self):
        """Einfacher Fall: 1 Violation bei 3 Beobachtungen."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        returns = pd.Series([-0.01, -0.03, 0.02], index=dates)
        var_estimates = pd.Series([-0.02, -0.02, -0.02], index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_observations == 3
        assert result.n_violations == 1  # Zweiter Tag: -3% < -2%
        assert result.violations.iloc[1]
        assert not result.violations.iloc[0]
        assert not result.violations.iloc[2]

    def test_no_violations(self):
        """Keine Violations: alle Returns innerhalb VaR."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        returns = pd.Series([-0.01, -0.005, 0.01, -0.008, 0.005], index=dates)
        var_estimates = pd.Series([-0.02] * 5, index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_violations == 0
        assert all(~result.violations)

    def test_all_violations(self):
        """Alle Returns überschreiten VaR."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        returns = pd.Series([-0.05, -0.04, -0.03], index=dates)
        var_estimates = pd.Series([-0.02, -0.02, -0.02], index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_violations == 3
        assert all(result.violations)


class TestViolationDetectorAlignment:
    """Tests für Index-Alignment und NaN-Handling."""

    def test_alignment_different_indices(self):
        """Returns und VaR haben unterschiedliche Indices."""
        dates_returns = pd.date_range("2024-01-01", periods=5, freq="D")
        dates_var = pd.date_range("2024-01-02", periods=5, freq="D")

        returns = pd.Series([-0.01, -0.02, -0.03, -0.01, 0.01], index=dates_returns)
        var_estimates = pd.Series([-0.02] * 5, index=dates_var)

        result = detect_violations(returns, var_estimates)

        # Nur 4 überlappende Tage
        assert result.n_observations == 4
        # Überprüfe dass Alignment korrekt
        assert result.dates[0] == pd.Timestamp("2024-01-02")
        assert result.dates[-1] == pd.Timestamp("2024-01-05")

    def test_nan_handling_in_returns(self):
        """NaN-Werte in Returns werden entfernt."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        returns = pd.Series([-0.01, float("nan"), -0.03, -0.01, 0.01], index=dates)
        var_estimates = pd.Series([-0.02] * 5, index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_observations == 4  # NaN wurde entfernt
        assert not result.returns.isna().any()

    def test_nan_handling_in_var(self):
        """NaN-Werte in VaR estimates werden entfernt."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        returns = pd.Series([-0.01, -0.02, -0.03, -0.01, 0.01], index=dates)
        var_estimates = pd.Series([-0.02, float("nan"), -0.02, -0.02, -0.02], index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_observations == 4  # NaN wurde entfernt
        assert not result.var_estimates.isna().any()


class TestViolationDetectorSignConvention:
    """Tests für korrekte Sign Convention (beide negativ)."""

    def test_negative_return_exceeds_negative_var(self):
        """Return = -3%, VaR = -2% → Violation (korrekte Sign Convention)."""
        dates = pd.date_range("2024-01-01", periods=1, freq="D")
        returns = pd.Series([-0.03], index=dates)
        var_estimates = pd.Series([-0.02], index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_violations == 1

    def test_negative_return_within_var(self):
        """Return = -1%, VaR = -2% → keine Violation."""
        dates = pd.date_range("2024-01-01", periods=1, freq="D")
        returns = pd.Series([-0.01], index=dates)
        var_estimates = pd.Series([-0.02], index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_violations == 0

    def test_positive_return_no_violation(self):
        """Positive Returns → nie Violation."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        returns = pd.Series([0.01, 0.02, 0.03], index=dates)
        var_estimates = pd.Series([-0.02] * 3, index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_violations == 0

    def test_extreme_loss_violation(self):
        """Extremer Verlust → definitiv Violation."""
        dates = pd.date_range("2024-01-01", periods=1, freq="D")
        returns = pd.Series([-0.10], index=dates)  # -10% Verlust
        var_estimates = pd.Series([-0.02], index=dates)  # -2% VaR

        result = detect_violations(returns, var_estimates)

        assert result.n_violations == 1


class TestViolationSeriesProperties:
    """Tests für ViolationSeries Properties."""

    def test_violation_dates_property(self):
        """violation_dates gibt korrekte Daten zurück."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        returns = pd.Series([-0.01, -0.03, 0.01, -0.04, 0.01], index=dates)
        var_estimates = pd.Series([-0.02] * 5, index=dates)

        result = detect_violations(returns, var_estimates)

        expected_violation_dates = [dates[1], dates[3]]  # 2. und 4. Tag
        assert len(result.violation_dates) == 2
        assert result.violation_dates[0] == expected_violation_dates[0]
        assert result.violation_dates[1] == expected_violation_dates[1]

    def test_violation_rate_property(self):
        """violation_rate korrekt berechnet."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        # 5 Violations bei 100 Beobachtungen = 5%
        returns_list = [-0.01] * 95 + [-0.03] * 5
        returns = pd.Series(returns_list, index=dates)
        var_estimates = pd.Series([-0.02] * 100, index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.violation_rate == 0.05

    def test_empty_violations(self):
        """Leere Violation-Serie."""
        dates = pd.date_range("2024-01-01", periods=0, freq="D")
        returns = pd.Series([], index=dates, dtype=float)
        var_estimates = pd.Series([], index=dates, dtype=float)

        result = detect_violations(returns, var_estimates)

        assert result.n_observations == 0
        assert result.n_violations == 0
        assert result.violation_rate == 0.0


class TestViolationDetectorRealWorldScenarios:
    """Tests mit realistischen Szenarien."""

    def test_99_var_typical_scenario(self):
        """Typisches 99% VaR Szenario: ~1% Violations."""
        dates = pd.date_range("2024-01-01", periods=250, freq="D")

        # Simuliere: 247 OK Tage + 3 Violation Tage
        returns_list = [-0.01] * 247 + [-0.03] * 3
        returns = pd.Series(returns_list, index=dates)
        var_estimates = pd.Series([-0.02] * 250, index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_observations == 250
        assert result.n_violations == 3
        assert abs(result.violation_rate - 0.012) < 0.001  # ~1.2%

    def test_95_var_typical_scenario(self):
        """Typisches 95% VaR Szenario: ~5% Violations."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")

        # Simuliere: 95 OK Tage + 5 Violation Tage
        returns_list = [-0.01] * 95 + [-0.03] * 5
        returns = pd.Series(returns_list, index=dates)
        var_estimates = pd.Series([-0.02] * 100, index=dates)

        result = detect_violations(returns, var_estimates)

        assert result.n_observations == 100
        assert result.n_violations == 5
        assert result.violation_rate == 0.05  # Exakt 5%

    def test_varying_var_estimates(self):
        """VaR-Schätzungen variieren über Zeit (realistischer)."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        returns = pd.Series([-0.01, -0.025, -0.03, -0.015, -0.035], index=dates)
        var_estimates = pd.Series([-0.02, -0.03, -0.025, -0.01, -0.04], index=dates)

        result = detect_violations(returns, var_estimates)

        # Tag 1: -1% > -2% → OK
        # Tag 2: -2.5% > -3% → OK
        # Tag 3: -3% < -2.5% → Violation
        # Tag 4: -1.5% < -1% → Violation
        # Tag 5: -3.5% > -4% → OK
        assert result.n_violations == 2
        assert result.violations.iloc[2]
        assert result.violations.iloc[3]
