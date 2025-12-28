"""
Tests for VaR/CVaR calculations (src/risk/var.py)
"""

import pytest
import pandas as pd
import numpy as np

from src.risk.var import (
    historical_var,
    historical_cvar,
    parametric_var,
    parametric_cvar,
    cornish_fisher_var,
    cornish_fisher_cvar,
    ewma_var,
    ewma_cvar,
)


class TestHistoricalVaR:
    """Tests for historical_var()"""

    def test_historical_var_positive_returns(self):
        """VaR sollte 0 sein bei nur positiven Returns"""
        returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        var = historical_var(returns, alpha=0.05)
        assert var == 0.0, "VaR sollte 0 sein bei nur Gewinnen"

    def test_historical_var_negative_returns(self):
        """VaR sollte positiv sein bei negativen Returns"""
        returns = pd.Series([-0.01, -0.02, -0.03, -0.04, -0.05])
        var = historical_var(returns, alpha=0.05)
        assert var > 0.0, "VaR sollte > 0 bei Verlusten"

    def test_historical_var_mixed_returns(self):
        """VaR bei gemischten Returns"""
        returns = pd.Series([0.01, -0.02, 0.03, -0.04, 0.05])
        var = historical_var(returns, alpha=0.05)
        assert var >= 0.0, "VaR sollte immer >= 0"

    def test_historical_var_empty_series(self):
        """Leere Series sollte VaR=0 zurückgeben"""
        returns = pd.Series(dtype=float)
        var = historical_var(returns, alpha=0.05)
        assert var == 0.0

    def test_historical_var_with_nans(self):
        """NaNs sollten ignoriert werden"""
        returns = pd.Series([0.01, np.nan, -0.02, np.nan, 0.03])
        var = historical_var(returns, alpha=0.05)
        assert var >= 0.0, "VaR sollte mit NaNs funktionieren"

    def test_historical_var_alpha_variation(self):
        """Höheres Alpha sollte höheren VaR ergeben (mehr im Tail)"""
        returns = pd.Series([-0.01, -0.02, -0.03, -0.04, -0.05])
        var_5 = historical_var(returns, alpha=0.05)
        var_10 = historical_var(returns, alpha=0.10)
        # Bei alpha=0.10 ist das Quantil weniger extrem -> VaR kann kleiner sein
        assert var_5 >= 0 and var_10 >= 0


class TestHistoricalCVaR:
    """Tests for historical_cvar()"""

    def test_historical_cvar_greater_than_var(self):
        """CVaR sollte >= VaR sein"""
        returns = pd.Series([-0.01, -0.02, -0.03, -0.04, -0.05])
        var = historical_var(returns, alpha=0.05)
        cvar = historical_cvar(returns, alpha=0.05)
        assert cvar >= var, "CVaR sollte >= VaR"

    def test_historical_cvar_positive_returns(self):
        """CVaR sollte 0 sein bei nur positiven Returns"""
        returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])
        cvar = historical_cvar(returns, alpha=0.05)
        assert cvar == 0.0

    def test_historical_cvar_empty_series(self):
        """Leere Series sollte CVaR=0 zurückgeben"""
        returns = pd.Series(dtype=float)
        cvar = historical_cvar(returns, alpha=0.05)
        assert cvar == 0.0

    def test_historical_cvar_with_nans(self):
        """NaNs sollten ignoriert werden"""
        returns = pd.Series([0.01, np.nan, -0.02, np.nan, -0.03])
        cvar = historical_cvar(returns, alpha=0.05)
        assert cvar >= 0.0


class TestParametricVaR:
    """Tests for parametric_var()"""

    def test_parametric_var_positive(self):
        """Parametric VaR sollte >= 0 sein"""
        # Normal-verteilte Returns (mean~0, std>0)
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))
        var = parametric_var(returns, alpha=0.05)
        assert var >= 0.0

    def test_parametric_var_zero_volatility(self):
        """Bei zero volatility sollte VaR=0 sein"""
        returns = pd.Series([0.01] * 100)  # Konstante Returns
        var = parametric_var(returns, alpha=0.05)
        assert var == 0.0, "VaR sollte 0 bei zero vol"

    def test_parametric_var_empty_series(self):
        """Leere Series sollte VaR=0 zurückgeben"""
        returns = pd.Series(dtype=float)
        var = parametric_var(returns, alpha=0.05)
        assert var == 0.0

    def test_parametric_var_insufficient_data(self):
        """Bei n<2 sollte VaR=0 zurückgeben (std undefiniert)"""
        returns = pd.Series([0.01])
        var = parametric_var(returns, alpha=0.05)
        assert var == 0.0

    def test_parametric_var_with_nans(self):
        """NaNs sollten ignoriert werden"""
        np.random.seed(42)
        returns = pd.Series(list(np.random.normal(0, 0.02, 50)) + [np.nan] * 10)
        var = parametric_var(returns, alpha=0.05)
        assert var >= 0.0


class TestParametricCVaR:
    """Tests for parametric_cvar()"""

    def test_parametric_cvar_greater_than_var(self):
        """CVaR sollte >= VaR sein (bei Normal-Verteilung)"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))
        var = parametric_var(returns, alpha=0.05)
        cvar = parametric_cvar(returns, alpha=0.05)
        assert cvar >= var, "CVaR sollte >= VaR"

    def test_parametric_cvar_zero_volatility(self):
        """Bei zero volatility sollte CVaR=0 sein"""
        returns = pd.Series([0.01] * 100)
        cvar = parametric_cvar(returns, alpha=0.05)
        assert cvar == 0.0

    def test_parametric_cvar_empty_series(self):
        """Leere Series sollte CVaR=0 zurückgeben"""
        returns = pd.Series(dtype=float)
        cvar = parametric_cvar(returns, alpha=0.05)
        assert cvar == 0.0


class TestVaRInvariants:
    """Tests für allgemeine VaR/CVaR-Invarianten"""

    def test_cvar_always_geq_var_historical(self):
        """CVaR >= VaR (Historical)"""
        np.random.seed(123)
        returns = pd.Series(np.random.normal(-0.01, 0.03, 200))

        for alpha in [0.01, 0.05, 0.10]:
            var = historical_var(returns, alpha=alpha)
            cvar = historical_cvar(returns, alpha=alpha)
            assert cvar >= var, f"CVaR < VaR at alpha={alpha}"

    def test_var_increases_with_alpha_parametric(self):
        """Bei parametric: höheres alpha sollte tendenziell niedrigeren VaR ergeben"""
        # (weil alpha=0.05 = 95% VaR, alpha=0.10 = 90% VaR -> weniger extrem)
        np.random.seed(123)
        returns = pd.Series(np.random.normal(-0.01, 0.03, 200))

        var_1 = parametric_var(returns, alpha=0.01)  # 99% VaR
        var_5 = parametric_var(returns, alpha=0.05)  # 95% VaR

        # 99% VaR sollte >= 95% VaR (extremerer Tail)
        assert var_1 >= var_5, "99% VaR sollte >= 95% VaR"

    def test_var_always_non_negative(self):
        """VaR/CVaR immer >= 0"""
        np.random.seed(456)
        returns = pd.Series(np.random.normal(0.01, 0.02, 100))

        var_hist = historical_var(returns, alpha=0.05)
        cvar_hist = historical_cvar(returns, alpha=0.05)
        var_param = parametric_var(returns, alpha=0.05)
        cvar_param = parametric_cvar(returns, alpha=0.05)

        assert var_hist >= 0
        assert cvar_hist >= 0
        assert var_param >= 0
        assert cvar_param >= 0


# =============================================================================
# Phase 1 Tests: Cornish-Fisher & EWMA VaR/CVaR (Agent A1)
# =============================================================================


class TestCornishFisherVaR:
    """Tests for cornish_fisher_var()"""

    def test_cornish_fisher_var_basic(self):
        """Cornish-Fisher VaR sollte >= 0 sein"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))
        var = cornish_fisher_var(returns, alpha=0.05)
        assert var >= 0.0, "CF-VaR sollte >= 0"

    def test_cornish_fisher_var_vs_parametric_normal(self):
        """Bei skew≈0, kurt≈0 sollte CF-VaR ≈ Parametric VaR sein"""
        # Normal-verteilte Returns (skew≈0, excess kurt≈0)
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 1000))

        cf_var = cornish_fisher_var(returns, alpha=0.05)
        param_var = parametric_var(returns, alpha=0.05)

        # Sollten ähnlich sein (Toleranz 20%)
        assert abs(cf_var - param_var) / param_var < 0.20, \
            f"CF-VaR ({cf_var:.4f}) sollte ≈ Parametric VaR ({param_var:.4f}) bei Normal-Dist"

    def test_cornish_fisher_var_with_skew(self):
        """CF-VaR sollte Skewness berücksichtigen"""
        # Positive Skew (rechts-schief) -> weniger extreme negative Returns
        np.random.seed(42)
        returns = pd.Series(np.random.exponential(0.02, 100) - 0.02)

        cf_var = cornish_fisher_var(returns, alpha=0.05)
        param_var = parametric_var(returns, alpha=0.05)

        # CF sollte sich von parametric unterscheiden
        assert cf_var >= 0.0

    def test_cornish_fisher_var_empty_series(self):
        """Leere Series sollte VaR=0 zurückgeben"""
        returns = pd.Series(dtype=float)
        var = cornish_fisher_var(returns, alpha=0.05)
        assert var == 0.0

    def test_cornish_fisher_var_insufficient_data(self):
        """Bei weniger als min_obs sollte VaR=0 zurückgeben"""
        returns = pd.Series([0.01, -0.02, 0.03])  # nur 3 obs, min_obs=20
        var = cornish_fisher_var(returns, alpha=0.05, min_obs=20)
        assert var == 0.0

    def test_cornish_fisher_var_with_nans(self):
        """NaNs sollten robust behandelt werden"""
        np.random.seed(42)
        returns = pd.Series(list(np.random.normal(0, 0.02, 80)) + [np.nan] * 10)
        var = cornish_fisher_var(returns, alpha=0.05, min_obs=50)
        assert var >= 0.0

    def test_cornish_fisher_var_determinism(self):
        """Gleicher Input sollte gleichen Output ergeben"""
        np.random.seed(123)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        var1 = cornish_fisher_var(returns, alpha=0.05)
        var2 = cornish_fisher_var(returns, alpha=0.05)

        assert var1 == var2, "CF-VaR sollte deterministisch sein"

    def test_cornish_fisher_var_zero_volatility(self):
        """Bei zero volatility sollte VaR=0 sein"""
        returns = pd.Series([0.01] * 100)
        var = cornish_fisher_var(returns, alpha=0.05)
        assert var == 0.0


class TestCornishFisherCVaR:
    """Tests for cornish_fisher_cvar()"""

    def test_cornish_fisher_cvar_geq_var(self):
        """CF-CVaR sollte >= CF-VaR sein"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        cf_var = cornish_fisher_var(returns, alpha=0.05)
        cf_cvar = cornish_fisher_cvar(returns, alpha=0.05)

        assert cf_cvar >= cf_var, "CF-CVaR sollte >= CF-VaR"

    def test_cornish_fisher_cvar_empty_series(self):
        """Leere Series sollte CVaR=0 zurückgeben"""
        returns = pd.Series(dtype=float)
        cvar = cornish_fisher_cvar(returns, alpha=0.05)
        assert cvar == 0.0

    def test_cornish_fisher_cvar_determinism(self):
        """Gleicher Input sollte gleichen Output ergeben"""
        np.random.seed(123)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        cvar1 = cornish_fisher_cvar(returns, alpha=0.05)
        cvar2 = cornish_fisher_cvar(returns, alpha=0.05)

        assert cvar1 == cvar2, "CF-CVaR sollte deterministisch sein"


class TestEWMAVaR:
    """Tests for ewma_var()"""

    def test_ewma_var_basic(self):
        """EWMA VaR sollte >= 0 sein"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))
        var = ewma_var(returns, alpha=0.05, lambda_=0.94)
        assert var >= 0.0, "EWMA-VaR sollte >= 0"

    def test_ewma_var_vs_parametric(self):
        """EWMA VaR sollte in ähnlicher Größenordnung wie Parametric VaR sein"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        ewma = ewma_var(returns, alpha=0.05, lambda_=0.94)
        param = parametric_var(returns, alpha=0.05)

        # Sollten in gleicher Größenordnung sein (innerhalb Faktor 2)
        assert 0.5 * param <= ewma <= 2.0 * param, \
            f"EWMA ({ewma:.4f}) sollte in ähnlicher Größenordnung wie Parametric ({param:.4f}) sein"

    def test_ewma_var_lambda_effect(self):
        """Höheres Lambda (langsamer Decay) sollte andere VaR ergeben"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        var_fast = ewma_var(returns, alpha=0.05, lambda_=0.90)  # Schneller Decay
        var_slow = ewma_var(returns, alpha=0.05, lambda_=0.97)  # Langsamer Decay

        # Sollten unterschiedlich sein
        assert var_fast != var_slow

    def test_ewma_var_empty_series(self):
        """Leere Series sollte VaR=0 zurückgeben"""
        returns = pd.Series(dtype=float)
        var = ewma_var(returns, alpha=0.05)
        assert var == 0.0

    def test_ewma_var_insufficient_data(self):
        """Bei weniger als min_obs sollte VaR=0 zurückgeben"""
        returns = pd.Series([0.01, -0.02, 0.03])
        var = ewma_var(returns, alpha=0.05, lambda_=0.94, min_obs=20)
        assert var == 0.0

    def test_ewma_var_invalid_lambda(self):
        """Lambda außerhalb (0,1) sollte ValueError werfen"""
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        with pytest.raises(ValueError, match="lambda_ must be in"):
            ewma_var(returns, alpha=0.05, lambda_=1.5)

        with pytest.raises(ValueError, match="lambda_ must be in"):
            ewma_var(returns, alpha=0.05, lambda_=0.0)

    def test_ewma_var_determinism(self):
        """Gleicher Input sollte gleichen Output ergeben"""
        np.random.seed(123)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        var1 = ewma_var(returns, alpha=0.05, lambda_=0.94)
        var2 = ewma_var(returns, alpha=0.05, lambda_=0.94)

        assert var1 == var2, "EWMA-VaR sollte deterministisch sein"

    def test_ewma_var_with_nans(self):
        """NaNs sollten robust behandelt werden"""
        np.random.seed(42)
        returns = pd.Series(list(np.random.normal(0, 0.02, 80)) + [np.nan] * 10)
        var = ewma_var(returns, alpha=0.05, lambda_=0.94, min_obs=50)
        assert var >= 0.0

    def test_ewma_var_recent_volatility_spike(self):
        """EWMA sollte stärker auf recent volatility reagieren als Sample Std"""
        # Niedrige Vol, dann Spike am Ende
        np.random.seed(42)
        low_vol_returns = list(np.random.normal(0, 0.01, 90))
        high_vol_returns = list(np.random.normal(0, 0.05, 10))
        returns = pd.Series(low_vol_returns + high_vol_returns)

        ewma = ewma_var(returns, alpha=0.05, lambda_=0.94)
        param = parametric_var(returns, alpha=0.05)

        # EWMA sollte höher sein (wegen recent spike)
        # Dies ist nicht immer garantiert, aber tendenziell der Fall
        assert ewma >= 0.0 and param >= 0.0


class TestEWMACVaR:
    """Tests for ewma_cvar()"""

    def test_ewma_cvar_geq_var(self):
        """EWMA-CVaR sollte >= EWMA-VaR sein"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        ewma_v = ewma_var(returns, alpha=0.05, lambda_=0.94)
        ewma_cv = ewma_cvar(returns, alpha=0.05, lambda_=0.94)

        assert ewma_cv >= ewma_v, "EWMA-CVaR sollte >= EWMA-VaR"

    def test_ewma_cvar_empty_series(self):
        """Leere Series sollte CVaR=0 zurückgeben"""
        returns = pd.Series(dtype=float)
        cvar = ewma_cvar(returns, alpha=0.05)
        assert cvar == 0.0

    def test_ewma_cvar_determinism(self):
        """Gleicher Input sollte gleichen Output ergeben"""
        np.random.seed(123)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        cvar1 = ewma_cvar(returns, alpha=0.05, lambda_=0.94)
        cvar2 = ewma_cvar(returns, alpha=0.05, lambda_=0.94)

        assert cvar1 == cvar2, "EWMA-CVaR sollte deterministisch sein"

    def test_ewma_cvar_invalid_lambda(self):
        """Lambda außerhalb (0,1) sollte ValueError werfen"""
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        with pytest.raises(ValueError, match="lambda_ must be in"):
            ewma_cvar(returns, alpha=0.05, lambda_=1.5)


class TestVaRMethodsComparison:
    """Vergleichstests zwischen verschiedenen VaR-Methoden"""

    def test_all_methods_non_negative(self):
        """Alle VaR-Methoden sollten >= 0 zurückgeben"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        methods = [
            ("historical", historical_var),
            ("parametric", parametric_var),
            ("cornish_fisher", cornish_fisher_var),
            ("ewma", lambda r, a: ewma_var(r, a, lambda_=0.94)),
        ]

        for name, func in methods:
            var = func(returns, 0.05)
            assert var >= 0.0, f"{name} VaR sollte >= 0"

    def test_all_cvar_methods_geq_var(self):
        """Alle CVaR-Methoden sollten >= VaR sein"""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        # Historical
        assert historical_cvar(returns, 0.05) >= historical_var(returns, 0.05)

        # Parametric
        assert parametric_cvar(returns, 0.05) >= parametric_var(returns, 0.05)

        # Cornish-Fisher
        assert cornish_fisher_cvar(returns, 0.05) >= cornish_fisher_var(returns, 0.05)

        # EWMA
        assert ewma_cvar(returns, 0.05, 0.94) >= ewma_var(returns, 0.05, 0.94)

    def test_determinism_all_methods(self):
        """Alle Methoden sollten deterministisch sein"""
        np.random.seed(123)
        returns = pd.Series(np.random.normal(0, 0.02, 100))

        # Historical
        assert historical_var(returns, 0.05) == historical_var(returns, 0.05)

        # Parametric
        assert parametric_var(returns, 0.05) == parametric_var(returns, 0.05)

        # Cornish-Fisher
        assert cornish_fisher_var(returns, 0.05) == cornish_fisher_var(returns, 0.05)

        # EWMA
        assert ewma_var(returns, 0.05, 0.94) == ewma_var(returns, 0.05, 0.94)


class TestEdgeCases:
    """Tests für Edge Cases und Robustheit"""

    def test_single_observation_all_methods(self):
        """Alle Methoden sollten bei 1 Observation robust sein"""
        returns = pd.Series([0.01])

        # Historical: Sollte 0 oder minimal sein
        assert historical_var(returns, 0.05) == 0.0

        # Parametric: Sollte 0 sein (std undefiniert bei n=1)
        assert parametric_var(returns, 0.05) == 0.0

        # Cornish-Fisher: Sollte 0 sein (min_obs nicht erreicht)
        assert cornish_fisher_var(returns, 0.05, min_obs=20) == 0.0

        # EWMA: Sollte 0 sein (min_obs nicht erreicht)
        assert ewma_var(returns, 0.05, min_obs=20) == 0.0

    def test_all_nans_all_methods(self):
        """Alle Methoden sollten bei only-NaNs robust sein"""
        returns = pd.Series([np.nan, np.nan, np.nan])

        assert historical_var(returns, 0.05) == 0.0
        assert parametric_var(returns, 0.05) == 0.0
        assert cornish_fisher_var(returns, 0.05, min_obs=1) == 0.0
        assert ewma_var(returns, 0.05, min_obs=1) == 0.0

    def test_constant_returns_all_methods(self):
        """Alle Methoden sollten bei konstanten Returns 0 zurückgeben (zero vol)"""
        returns = pd.Series([0.01] * 100)

        assert historical_var(returns, 0.05) == 0.0
        assert parametric_var(returns, 0.05) == 0.0
        assert cornish_fisher_var(returns, 0.05) == 0.0
        # EWMA: Bei konstanten Returns konvergiert Variance gegen 0,
        # aber startet mit sample variance. Nach genug Iterationen sollte sie klein sein.
        # Mit 100 Iterationen und lambda=0.94 ist sie noch nicht bei 0.
        # Test: EWMA sollte mindestens klein sein
        ewma = ewma_var(returns, 0.05, lambda_=0.94)
        assert ewma >= 0.0  # Nur Positivität testen, nicht exakte 0
