"""Unit Tests für Kupiec POF Test."""

import math

import pytest

from src.risk_layer.var_backtest.kupiec_pof import (
    KupiecResult,
    chi2_df1_cdf,
    chi2_df1_ppf,
    chi2_df1_sf,
    kupiec_pof_test,
    quick_kupiec_check,
)


class TestKupiecPOFBasic:
    """Grundlegende Funktionalitätstests."""

    def test_perfect_calibration_99_var(self):
        """99% VaR mit exakt 1% Violations → sollte ACCEPT sein."""
        T = 1000
        N = 10  # Exakt 1% Violations
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.result == KupiecResult.ACCEPT
        assert result.n_observations == T
        assert result.n_violations == N
        assert abs(result.observed_violation_rate - 0.01) < 1e-10

    def test_too_many_violations_rejected(self):
        """Deutlich zu viele Violations → sollte REJECT sein."""
        T = 250
        N = 15  # 6% statt erwarteter 1% → klar zu viel
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.result == KupiecResult.REJECT
        assert result.violation_ratio > 5  # 6x mehr als erwartet

    def test_near_perfect_calibration_accepted(self):
        """Leicht abweichend aber noch im Akzeptanzbereich."""
        T = 250
        N = 3  # 1.2% statt 1% → sollte OK sein
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.result == KupiecResult.ACCEPT

    def test_insufficient_data_inconclusive(self):
        """Weniger als min_observations → INCONCLUSIVE."""
        violations = [False] * 100 + [True] * 1

        result = kupiec_pof_test(violations, min_observations=250)

        assert result.result == KupiecResult.INCONCLUSIVE
        assert math.isnan(result.lr_statistic)


class TestKupiecPOFEdgeCases:
    """Edge Cases und Grenzwerte."""

    def test_all_violations(self):
        """100% Violations → definitiv REJECT."""
        violations = [True] * 250

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.result == KupiecResult.REJECT
        assert result.observed_violation_rate == 1.0

    def test_no_violations_large_sample(self):
        """0 Violations bei großem Sample → sollte REJECT sein (zu konservativ)."""
        violations = [False] * 500

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.n_violations == 0
        assert result.observed_violation_rate == 0.0
        # Bei 500 Beobachtungen und 99% VaR erwarten wir ~5 Violations
        # 0 ist statistisch sehr unwahrscheinlich
        assert result.result == KupiecResult.REJECT

    def test_no_violations_small_sample(self):
        """0 Violations bei kleinem Sample → kann OK sein."""
        violations = [False] * 250

        result = kupiec_pof_test(violations, confidence_level=0.99)

        # Bei 250 Beobachtungen erwarten wir ~2.5 Violations
        # 0 ist weniger extrem als bei großem Sample
        assert result.n_violations == 0

    def test_confidence_95_var(self):
        """95% VaR (5% erwartete Violations)."""
        T = 500
        N = 25  # Exakt 5%
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.95)

        assert abs(result.expected_violation_rate - 0.05) < 1e-10
        assert result.result == KupiecResult.ACCEPT


class TestKupiecPOFValidation:
    """Input Validation Tests."""

    def test_invalid_confidence_level_high(self):
        """confidence_level >= 1 → ValueError."""
        with pytest.raises(ValueError, match="confidence_level"):
            kupiec_pof_test([False] * 250, confidence_level=1.0)

    def test_invalid_confidence_level_low(self):
        """confidence_level <= 0 → ValueError."""
        with pytest.raises(ValueError, match="confidence_level"):
            kupiec_pof_test([False] * 250, confidence_level=0.0)

    def test_invalid_significance_level(self):
        """significance_level außerhalb (0,1) → ValueError."""
        with pytest.raises(ValueError, match="significance_level"):
            kupiec_pof_test([False] * 250, significance_level=1.5)

    def test_empty_violations_sequence(self):
        """Leere Violations-Sequenz → INCONCLUSIVE."""
        result = kupiec_pof_test([], confidence_level=0.99)

        assert result.result == KupiecResult.INCONCLUSIVE
        assert result.n_observations == 0


class TestQuickKupiecCheck:
    """Tests für Convenience-Funktion."""

    def test_quick_check_valid(self):
        """Schneller Check mit validen Werten."""
        assert quick_kupiec_check(n_violations=3, n_observations=250) is True

    def test_quick_check_invalid(self):
        """Schneller Check mit zu vielen Violations."""
        assert quick_kupiec_check(n_violations=20, n_observations=250) is False


class TestKupiecPOFOutput:
    """Tests für Output-Struktur."""

    def test_output_immutable(self):
        """Output sollte frozen dataclass sein."""
        violations = [False] * 250 + [True] * 3
        result = kupiec_pof_test(violations)

        with pytest.raises(AttributeError):
            result.n_violations = 999  # type: ignore

    def test_violation_ratio_calculation(self):
        """violation_ratio korrekt berechnet."""
        T = 500
        N = 10  # 2% statt erwarteter 1%
        violations = [True] * N + [False] * (T - N)

        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert abs(result.violation_ratio - 2.0) < 0.01  # ~2x mehr

    def test_is_valid_property(self):
        """is_valid Property funktioniert korrekt."""
        violations_ok = [False] * 247 + [True] * 3
        result_ok = kupiec_pof_test(violations_ok, confidence_level=0.99)
        assert result_ok.is_valid is True

        violations_bad = [False] * 235 + [True] * 15
        result_bad = kupiec_pof_test(violations_bad, confidence_level=0.99)
        assert result_bad.is_valid is False


class TestChi2StdlibImplementation:
    """Tests für stdlib-only chi2 Implementierung."""

    def test_chi2_cdf_basic(self):
        """Chi2 CDF Basiswerte."""
        # chi2(1).cdf(0) = 0
        assert abs(chi2_df1_cdf(0.0) - 0.0) < 1e-6

        # chi2(1).cdf(1) ≈ 0.6827 (innerhalb 1 std dev für normal)
        assert abs(chi2_df1_cdf(1.0) - 0.6827) < 0.01

        # chi2(1).cdf(3.84) ≈ 0.95 (95th percentile)
        assert abs(chi2_df1_cdf(3.84) - 0.95) < 0.01

    def test_chi2_sf_basic(self):
        """Chi2 survival function Basiswerte."""
        # chi2(1).sf(0) = 1
        assert abs(chi2_df1_sf(0.0) - 1.0) < 1e-6

        # chi2(1).sf(3.84) ≈ 0.05 (p-value for 95th percentile)
        assert abs(chi2_df1_sf(3.84) - 0.05) < 0.01

    def test_chi2_ppf_basic(self):
        """Chi2 PPF (inverse CDF) Basiswerte."""
        # chi2(1).ppf(0.95) ≈ 3.84
        assert abs(chi2_df1_ppf(0.95) - 3.84) < 0.01

        # chi2(1).ppf(0.99) ≈ 6.63
        assert abs(chi2_df1_ppf(0.99) - 6.63) < 0.01

    def test_chi2_ppf_edge_cases(self):
        """Chi2 PPF Edge Cases."""
        # Sehr kleine p-Werte
        result_small = chi2_df1_ppf(1e-9)
        assert result_small >= 0
        assert result_small < 1

        # Sehr große p-Werte
        result_large = chi2_df1_ppf(0.9999)
        assert result_large > 10

    def test_chi2_cdf_sf_complementary(self):
        """CDF und SF sollten komplementär sein."""
        test_values = [0.5, 1.0, 3.84, 10.0]

        for x in test_values:
            cdf_val = chi2_df1_cdf(x)
            sf_val = chi2_df1_sf(x)
            # CDF + SF sollte ≈ 1 sein
            assert abs((cdf_val + sf_val) - 1.0) < 0.01


class TestKupiecStatistics:
    """Tests für statistische Korrektheit."""

    def test_lr_statistic_positive(self):
        """LR Statistik sollte nicht-negativ sein."""
        violations = [False] * 240 + [True] * 10
        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert result.lr_statistic >= 0

    def test_p_value_range(self):
        """p-value sollte in [0,1] liegen."""
        violations = [False] * 245 + [True] * 5
        result = kupiec_pof_test(violations, confidence_level=0.99)

        assert 0 <= result.p_value <= 1

    def test_critical_value_consistent(self):
        """Kritischer Wert sollte konsistent mit significance_level sein."""
        violations = [False] * 250
        result = kupiec_pof_test(
            violations, confidence_level=0.99, significance_level=0.05
        )

        # Für df=1, alpha=0.05: critical value ≈ 3.84
        assert abs(result.critical_value - 3.84) < 0.05
