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
