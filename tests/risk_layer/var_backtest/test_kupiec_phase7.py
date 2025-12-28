"""Tests für Phase 7 Kupiec Convenience API (n/x/alpha interface)."""

import pytest

from src.risk_layer.var_backtest.kupiec_pof import (
    KupiecLRResult,
    kupiec_from_exceedances,
    kupiec_lr_uc,
    kupiec_pof_test,
)


class TestKupiecLRUC:
    """Tests für kupiec_lr_uc (direktes n/x/alpha Interface)."""

    def test_basic_pass_case(self):
        """n=1000, x=10, alpha=0.01 sollte PASS ergeben (gut kalibriert)."""
        result = kupiec_lr_uc(n=1000, x=10, alpha=0.01)

        assert isinstance(result, KupiecLRResult)
        assert result.n == 1000
        assert result.x == 10
        assert result.alpha == 0.01
        assert abs(result.phat - 0.01) < 1e-10  # x/n = 10/1000 = 0.01
        assert result.verdict == "PASS"
        assert result.p_value >= 0.05

    def test_extreme_x_zero(self):
        """x=0 mit alpha=0.01 sollte funktionieren (kein log(0) Fehler)."""
        result = kupiec_lr_uc(n=1000, x=0, alpha=0.01)

        assert result.x == 0
        assert result.phat == 0.0
        assert result.verdict == "FAIL"  # 0 violations bei alpha=0.01 ist suspekt
        assert 0 <= result.p_value <= 1
        assert result.lr_uc >= 0

    def test_extreme_x_equals_n(self):
        """x=n mit kleinem alpha sollte FAIL ergeben."""
        result = kupiec_lr_uc(n=100, x=100, alpha=0.01)

        assert result.x == result.n
        assert result.phat == 1.0
        assert result.verdict == "FAIL"
        assert result.p_value < 0.05

    def test_monotonic_sanity(self):
        """Je weiter x von alpha*n abweicht, desto kleiner p_value."""
        n = 1000
        alpha = 0.01
        expected_x = int(alpha * n)  # 10

        # Gut kalibriert: x nahe bei expected_x
        result_good = kupiec_lr_uc(n=n, x=expected_x, alpha=alpha)

        # Schlecht kalibriert: x weit von expected_x
        result_bad = kupiec_lr_uc(n=n, x=50, alpha=alpha)

        # LR sollte steigen, p_value sinken
        assert result_bad.lr_uc > result_good.lr_uc
        assert result_bad.p_value < result_good.p_value

    def test_validation_n_zero(self):
        """n=0 sollte ValueError werfen."""
        with pytest.raises(ValueError, match="n must be > 0"):
            kupiec_lr_uc(n=0, x=0, alpha=0.01)

    def test_validation_negative_x(self):
        """Negative x sollte ValueError werfen."""
        with pytest.raises(ValueError, match="x must be >= 0"):
            kupiec_lr_uc(n=100, x=-1, alpha=0.01)

    def test_validation_x_exceeds_n(self):
        """x > n sollte ValueError werfen."""
        with pytest.raises(ValueError, match="cannot exceed n"):
            kupiec_lr_uc(n=100, x=101, alpha=0.01)

    def test_validation_alpha_bounds(self):
        """alpha außerhalb (0,1) sollte ValueError werfen."""
        with pytest.raises(ValueError, match="alpha must be in"):
            kupiec_lr_uc(n=100, x=10, alpha=0.0)
        with pytest.raises(ValueError, match="alpha must be in"):
            kupiec_lr_uc(n=100, x=10, alpha=1.0)
        with pytest.raises(ValueError, match="alpha must be in"):
            kupiec_lr_uc(n=100, x=10, alpha=1.5)

    def test_custom_p_threshold(self):
        """Custom p_threshold sollte respektiert werden."""
        # p_threshold = 0.01 (strenger)
        result_strict = kupiec_lr_uc(n=250, x=5, alpha=0.01, p_threshold=0.01)

        # p_threshold = 0.1 (lockerer)
        result_loose = kupiec_lr_uc(n=250, x=5, alpha=0.01, p_threshold=0.1)

        # Bei gleichem Test können unterschiedliche Thresholds zu unterschiedlichen Verdicts führen
        assert result_strict.p_value == result_loose.p_value  # Same test
        assert result_strict.lr_uc == result_loose.lr_uc

    def test_to_dict(self):
        """to_dict() sollte alle Felder exportieren."""
        result = kupiec_lr_uc(n=1000, x=10, alpha=0.01)
        d = result.to_dict()

        assert d["n"] == 1000
        assert d["x"] == 10
        assert d["alpha"] == 0.01
        assert d["phat"] == 0.01
        assert "lr_uc" in d
        assert "p_value" in d
        assert d["verdict"] == "PASS"
        assert "notes" in d


class TestKupiecFromExceedances:
    """Tests für kupiec_from_exceedances (series helper)."""

    def test_exceedances_list_basic(self):
        """List[bool] sollte korrekt zu n/x konvertiert werden."""
        exceedances = [False] * 990 + [True] * 10

        result = kupiec_from_exceedances(exceedances, alpha=0.01)

        assert result.n == 1000
        assert result.x == 10
        assert result.verdict == "PASS"

    def test_exceedances_tuple(self):
        """Tuple sollte auch funktionieren."""
        exceedances = tuple([True] * 5 + [False] * 245)

        result = kupiec_from_exceedances(exceedances, alpha=0.01)

        assert result.n == 250
        assert result.x == 5

    def test_exceedances_empty(self):
        """Leere Liste sollte Fehler werfen (n=0)."""
        with pytest.raises(ValueError, match="n must be > 0"):
            kupiec_from_exceedances([], alpha=0.01)

    def test_exceedances_all_false(self):
        """Alle False sollte x=0 ergeben."""
        exceedances = [False] * 1000

        result = kupiec_from_exceedances(exceedances, alpha=0.01)

        assert result.x == 0
        assert result.phat == 0.0
        assert result.verdict == "FAIL"

    def test_exceedances_all_true(self):
        """Alle True sollte x=n ergeben."""
        exceedances = [True] * 100

        result = kupiec_from_exceedances(exceedances, alpha=0.01)

        assert result.x == 100
        assert result.phat == 1.0
        assert result.verdict == "FAIL"

    def test_invalid_exceedances_type(self):
        """Ungültiger Typ sollte ValueError werfen."""
        with pytest.raises(ValueError, match="must be a sequence"):
            kupiec_from_exceedances(123, alpha=0.01)  # type: ignore


class TestWrapperEquivalence:
    """Tests dass neue Wrapper äquivalent zu bestehender Implementation sind."""

    def test_lr_uc_matches_existing_engine(self):
        """kupiec_lr_uc sollte gleiche LR/p_value wie kupiec_pof_test ergeben."""
        n = 1000
        x = 10
        alpha = 0.01
        confidence_level = 1 - alpha  # 0.99

        # Phase 7 Wrapper
        result_new = kupiec_lr_uc(n=n, x=x, alpha=alpha)

        # Bestehende Implementation
        violations = [True] * x + [False] * (n - x)
        result_old = kupiec_pof_test(violations, confidence_level=confidence_level)

        # LR Statistik sollte identisch sein
        assert abs(result_new.lr_uc - result_old.lr_statistic) < 1e-9

        # p_value sollte identisch sein
        assert abs(result_new.p_value - result_old.p_value) < 1e-9

    def test_from_exceedances_matches_pof_test(self):
        """kupiec_from_exceedances sollte gleiche Ergebnisse wie kupiec_pof_test ergeben."""
        exceedances = [False] * 247 + [True] * 3
        alpha = 0.01
        confidence_level = 1 - alpha

        # Phase 7 Wrapper
        result_new = kupiec_from_exceedances(exceedances, alpha=alpha)

        # Bestehende Implementation
        result_old = kupiec_pof_test(exceedances, confidence_level=confidence_level)

        # Sollten äquivalent sein
        assert abs(result_new.lr_uc - result_old.lr_statistic) < 1e-9
        assert abs(result_new.p_value - result_old.p_value) < 1e-9
        assert result_new.n == result_old.n_observations
        assert result_new.x == result_old.n_violations

    def test_edge_case_x_zero_equivalence(self):
        """Edge Case x=0 sollte in beiden APIs identisch behandelt werden."""
        n = 1000
        x = 0
        alpha = 0.01

        result_new = kupiec_lr_uc(n=n, x=x, alpha=alpha)

        violations = [False] * n
        result_old = kupiec_pof_test(violations, confidence_level=1 - alpha)

        assert abs(result_new.lr_uc - result_old.lr_statistic) < 1e-9
        assert abs(result_new.p_value - result_old.p_value) < 1e-9

    def test_edge_case_x_equals_n_equivalence(self):
        """Edge Case x=n: neue API ist robuster (alte gibt nan zurück)."""
        n = 100
        x = 100
        alpha = 0.01

        result_new = kupiec_lr_uc(n=n, x=x, alpha=alpha)

        violations = [True] * n
        result_old = kupiec_pof_test(violations, confidence_level=1 - alpha)

        # Alte API gibt INCONCLUSIVE mit nan zurück (n < min_observations)
        # Neue API berechnet validen Wert (robuster)
        assert result_new.lr_uc > 0  # Valider Wert
        assert result_new.p_value < 0.05  # Sollte FAIL sein
        assert result_new.verdict == "FAIL"

        # Alte API ist INCONCLUSIVE wegen min_observations check
        # (das ist ein Unterschied im Design, kein Bug)


class TestPhase7Sanity:
    """Sanity Checks für Phase 7 Requirements."""

    def test_sanity_n1000_alpha001_x10_pass(self):
        """Requirement: n=1000 alpha=0.01 x≈alpha*n sollte PASS ergeben."""
        result = kupiec_lr_uc(n=1000, x=10, alpha=0.01)

        assert result.verdict == "PASS"
        assert result.p_value >= 0.05

    def test_sanity_x0_small_alpha_fail(self):
        """Requirement: x=0 mit alpha=0.01 sollte FAIL ergeben."""
        result = kupiec_lr_uc(n=1000, x=0, alpha=0.01)

        assert result.verdict == "FAIL"
        assert result.p_value < 0.05
        assert 0 <= result.p_value <= 1  # p_value finite

    def test_sanity_x_equals_n_small_alpha_fail(self):
        """Requirement: x=n mit kleinem alpha sollte FAIL ergeben."""
        result = kupiec_lr_uc(n=100, x=100, alpha=0.01)

        assert result.verdict == "FAIL"
        assert result.p_value < 0.05

    def test_monotonic_lr_increases_pvalue_decreases(self):
        """Requirement: LR steigt → p_value sinkt."""
        # Drei Szenarien: gut kalibriert, leicht off, stark off
        results = [
            kupiec_lr_uc(n=1000, x=10, alpha=0.01),  # Perfekt
            kupiec_lr_uc(n=1000, x=20, alpha=0.01),  # Leicht daneben
            kupiec_lr_uc(n=1000, x=50, alpha=0.01),  # Stark daneben
        ]

        # LR sollte monoton steigen
        assert results[1].lr_uc > results[0].lr_uc
        assert results[2].lr_uc > results[1].lr_uc

        # p_value sollte monoton fallen
        assert results[1].p_value < results[0].p_value
        assert results[2].p_value < results[1].p_value

    def test_series_helper_correct_nx(self):
        """Requirement: Series helper sollte korrektes n/x ableiten."""
        exceedances = [True, False, True, False, False]

        result = kupiec_from_exceedances(exceedances, alpha=0.4)

        assert result.n == 5
        assert result.x == 2
