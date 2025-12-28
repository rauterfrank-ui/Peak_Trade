"""VaR Validation & Backtesting Module (Phase 2).

This module provides VaR model validation tools including:
- Kupiec POF Test (with pure Python chi-square, no scipy)
- Basel Traffic Light System
- Backtest Runner
- Breach Analysis

API Design:
-----------
All functions are deterministic and handle edge cases robustly.
No SciPy dependency - uses math.erfc for chi-square p-values.

Sign Convention:
---------------
VaR is positive loss magnitude.
Breach occurs when realized_loss = -return > var_value.

Example:
--------
>>> from src.risk.validation import kupiec_pof_test, run_var_backtest
>>>
>>> # Kupiec test
>>> result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)
>>> print(result.is_valid)  # True or False
>>>
>>> # Full backtest
>>> backtest_result = run_var_backtest(returns, var_series, confidence_level=0.99)
>>> print(backtest_result.kupiec.is_valid)
>>> print(backtest_result.traffic_light.color)
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

__all__ = [
    # Kupiec POF
    "KupiecResult",
    "kupiec_pof_test",
    "kupiec_lr_statistic",
    "chi2_p_value",
    # Traffic Light
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
]
