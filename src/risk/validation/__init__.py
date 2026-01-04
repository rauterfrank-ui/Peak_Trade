"""VaR Validation & Backtesting Module (Phase 2 + 8A/8B/8C).

This module provides VaR model validation tools including:
- Kupiec POF Test (Phase 8A: with pure Python chi-square, no scipy)
- Basel Traffic Light System (Phase 8A)
- Christoffersen Independence + Conditional Coverage Tests (Phase 8B)
- Suite Runner & Report Formatter (Phase 8C)
- Backtest Runner
- Breach Analysis

API Design:
-----------
All functions are deterministic and handle edge cases robustly.
No SciPy dependency - uses math.erfc for chi-square p-values.
Stdlib-only implementation.

Sign Convention:
---------------
VaR is positive loss magnitude.
Breach occurs when realized_loss = -return > var_value.

Example:
--------
>>> from src.risk.validation import kupiec_pof_test, run_var_backtest_suite
>>>
>>> # Kupiec test (Phase 8A)
>>> result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)
>>> print(result.is_valid)  # True or False
>>>
>>> # Full suite (Phase 8C)
>>> import pandas as pd
>>> returns = pd.Series([...])
>>> var_series = pd.Series([...])
>>> suite_result = run_var_backtest_suite(returns, var_series, confidence_level=0.99)
>>> print(suite_result.overall_result)  # PASS or FAIL
"""

from src.risk.validation.kupiec_pof import (
    KupiecResult,
    kupiec_pof_test,
    kupiec_lr_statistic,
    chi2_p_value,
)

from src.risk.validation.traffic_light import (
    TrafficLightResult,
    basel_traffic_light,
    get_traffic_light_thresholds,
)

from src.risk.validation.backtest_runner import (
    BacktestResult,
    run_var_backtest,
    detect_breaches,
)

from src.risk.validation.breach_analysis import (
    BreachAnalysis,
    analyze_breaches,
    compute_breach_statistics,
)

from src.risk.validation.christoffersen import (
    ChristoffersenIndependenceResult,
    ChristoffersenConditionalCoverageResult,
    independence_test,
    conditional_coverage_test,
)

from src.risk.validation.suite_runner import (
    VaRBacktestSuiteResult,
    run_var_backtest_suite,
)

from src.risk.validation.report_formatter import (
    format_suite_result_json,
    format_suite_result_markdown,
)

__all__ = [
    # Kupiec POF (Phase 8A)
    "KupiecResult",
    "kupiec_pof_test",
    "kupiec_lr_statistic",
    "chi2_p_value",
    # Traffic Light (Phase 8A)
    "TrafficLightResult",
    "basel_traffic_light",
    "get_traffic_light_thresholds",
    # Backtest Runner
    "BacktestResult",
    "run_var_backtest",
    "detect_breaches",
    # Breach Analysis
    "BreachAnalysis",
    "analyze_breaches",
    "compute_breach_statistics",
    # Christoffersen Tests (Phase 8B)
    "ChristoffersenIndependenceResult",
    "ChristoffersenConditionalCoverageResult",
    "independence_test",
    "conditional_coverage_test",
    # Suite Runner + Report Formatter (Phase 8C)
    "VaRBacktestSuiteResult",
    "run_var_backtest_suite",
    "format_suite_result_json",
    "format_suite_result_markdown",
]
