"""Verify validation-layer Christoffersen wrappers match canonical engine."""

import pandas as pd
import pytest

from src.risk.validation.christoffersen import (
    conditional_coverage_test,
    independence_test,
)
from src.risk_layer.var_backtest.christoffersen_tests import (
    christoffersen_lr_cc,
    christoffersen_lr_ind,
)


class TestChristoffersenEquivalence:
    """Legacy wrappers vs canonical ``risk_layer`` implementation."""

    def test_independence_matches_canonical(self) -> None:
        exceed = [False] * 40 + [True, False, True, False] + [False] * 56
        s = pd.Series(exceed)

        leg = independence_test(s, significance=0.05)
        can = christoffersen_lr_ind(exceed, p_threshold=0.05)

        assert leg.is_valid == (can.verdict == "PASS")
        assert leg.p_value == pytest.approx(can.p_value, rel=0, abs=1e-12)
        assert leg.lr_statistic == pytest.approx(can.lr_ind, rel=0, abs=1e-12)

    def test_conditional_coverage_matches_canonical(self) -> None:
        exceed = [False] * 90 + [True] * 10
        s = pd.Series(exceed)
        conf = 0.95
        alpha = 1.0 - conf

        leg = conditional_coverage_test(
            breaches=10,
            observations=100,
            breaches_bool=s,
            confidence_level=conf,
            significance=0.05,
        )
        can = christoffersen_lr_cc(exceed, alpha, p_threshold=0.05)

        assert leg.is_valid == (can.verdict == "PASS")
        assert leg.p_value == pytest.approx(can.p_value, rel=0, abs=1e-12)
        assert leg.lr_cc_statistic == pytest.approx(can.lr_cc, rel=0, abs=1e-12)

    def test_inconsistent_breaches_raises(self) -> None:
        s = pd.Series([True, False, False])
        with pytest.raises(ValueError, match="must match breaches"):
            conditional_coverage_test(
                breaches=2,
                observations=3,
                breaches_bool=s,
                confidence_level=0.95,
            )
