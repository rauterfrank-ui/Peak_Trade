"""
VaR Backtest Suite Runner.

Aggregates all VaR backtests (Kupiec POF, Basel Traffic Light, Christoffersen IND/CC)
into a single suite run with deterministic output.

Phase 8C: Suite Report & Regression Guard
"""

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

from .christoffersen import (
    conditional_coverage_test,
    independence_test,
)
from .kupiec_pof import kupiec_pof_test
from .traffic_light import basel_traffic_light


@dataclass
class VaRBacktestSuiteResult:
    """
    Aggregated result of all VaR backtest suite tests.

    Attributes:
        observations: Number of observations (days)
        breaches: Number of VaR breaches
        confidence_level: VaR confidence level (e.g. 0.95, 0.99)
        kupiec_pof_result: Kupiec POF test result ("PASS" or "FAIL")
        kupiec_pof_pvalue: Kupiec POF test p-value (rounded to 6 decimals)
        basel_traffic_light: Basel Traffic Light color ("GREEN", "YELLOW", "RED")
        christoffersen_ind_result: Christoffersen IND test result ("PASS" or "FAIL")
        christoffersen_ind_pvalue: Christoffersen IND test p-value (rounded to 6 decimals)
        christoffersen_cc_result: Christoffersen CC test result ("PASS" or "FAIL")
        christoffersen_cc_pvalue: Christoffersen CC test p-value (rounded to 6 decimals)
        overall_result: Overall suite result ("PASS" if all tests pass, else "FAIL")
    """

    observations: int
    breaches: int
    confidence_level: float
    kupiec_pof_result: str
    kupiec_pof_pvalue: float
    basel_traffic_light: str
    christoffersen_ind_result: str
    christoffersen_ind_pvalue: float
    christoffersen_cc_result: str
    christoffersen_cc_pvalue: float
    overall_result: str = field(init=False)

    def __post_init__(self):
        """Compute overall result."""
        all_pass = (
            self.kupiec_pof_result == "PASS"
            and self.basel_traffic_light == "GREEN"
            and self.christoffersen_ind_result == "PASS"
            and self.christoffersen_cc_result == "PASS"
        )
        self.overall_result = "PASS" if all_pass else "FAIL"


def run_var_backtest_suite(
    returns: pd.Series,
    var_series: pd.Series,
    confidence_level: float = 0.95,
    significance: float = 0.05,
) -> VaRBacktestSuiteResult:
    """
    Run full VaR backtest suite (Kupiec POF, Basel Traffic Light, Christoffersen IND/CC).

    Args:
        returns: Time series of returns (aligned with var_series index)
        var_series: Time series of VaR forecasts (positive values)
        confidence_level: VaR confidence level (e.g. 0.95 for 95% VaR)
        significance: Significance level for statistical tests (default: 0.05)

    Returns:
        VaRBacktestSuiteResult with all test outcomes

    Raises:
        ValueError: If returns and var_series have different lengths or indices

    Example:
        >>> import pandas as pd
        >>> returns = pd.Series([0.01, -0.02, 0.015, -0.03, 0.005])
        >>> var_series = pd.Series([0.02, 0.02, 0.02, 0.02, 0.02])
        >>> result = run_var_backtest_suite(returns, var_series, confidence_level=0.95)
        >>> print(result.overall_result)
        PASS
    """
    # Validate inputs
    if len(returns) != len(var_series):
        raise ValueError(
            f"returns and var_series must have same length "
            f"(got {len(returns)} vs {len(var_series)})"
        )

    if not returns.index.equals(var_series.index):
        raise ValueError("returns and var_series must have identical indices")

    # Compute breaches (loss exceeds VaR)
    # VaR is positive, losses are negative
    breaches_bool = returns < -var_series
    breaches = breaches_bool.sum()
    observations = len(returns)

    # 1) Kupiec POF Test
    kupiec_result = kupiec_pof_test(
        breaches=breaches,
        observations=observations,
        confidence_level=confidence_level,
        alpha=significance,
    )
    kupiec_pof_result = "PASS" if kupiec_result.is_valid else "FAIL"
    kupiec_pof_pvalue = round(kupiec_result.p_value, 6)

    # 2) Basel Traffic Light
    traffic_light_result = basel_traffic_light(
        breaches=breaches,
        observations=observations,
        confidence_level=confidence_level,
    )
    basel_traffic_light_color = traffic_light_result.color.upper()

    # 3) Christoffersen Independence Test
    ind_result = independence_test(
        breaches_bool=breaches_bool,
        significance=significance,
    )
    christoffersen_ind_result = "PASS" if ind_result.is_valid else "FAIL"
    christoffersen_ind_pvalue = round(ind_result.p_value, 6)

    # 4) Christoffersen Conditional Coverage Test
    cc_result = conditional_coverage_test(
        breaches=breaches,
        observations=observations,
        breaches_bool=breaches_bool,
        confidence_level=confidence_level,
        significance=significance,
    )
    christoffersen_cc_result = "PASS" if cc_result.is_valid else "FAIL"
    christoffersen_cc_pvalue = round(cc_result.p_value, 6)

    return VaRBacktestSuiteResult(
        observations=observations,
        breaches=breaches,
        confidence_level=confidence_level,
        kupiec_pof_result=kupiec_pof_result,
        kupiec_pof_pvalue=kupiec_pof_pvalue,
        basel_traffic_light=basel_traffic_light_color,
        christoffersen_ind_result=christoffersen_ind_result,
        christoffersen_ind_pvalue=christoffersen_ind_pvalue,
        christoffersen_cc_result=christoffersen_cc_result,
        christoffersen_cc_pvalue=christoffersen_cc_pvalue,
    )
