"""
VaR Backtesting Module
======================

Provides statistical backtesting capabilities for VaR models,
including the Kupiec Proportion of Failures (POF) test.

This module is designed for research and backtesting only.
It is NOT intended for real-time/live trading validation.
"""

from src.risk_layer.var_backtest.kupiec_pof import (
    KupiecPOFOutput,
    KupiecResult,
    kupiec_pof_test,
    quick_kupiec_check,
)
from src.risk_layer.var_backtest.var_backtest_runner import (
    VaRBacktestResult,
    VaRBacktestRunner,
)
from src.risk_layer.var_backtest.violation_detector import (
    ViolationSeries,
    detect_violations,
)

__all__ = [
    "KupiecResult",
    "KupiecPOFOutput",
    "kupiec_pof_test",
    "quick_kupiec_check",
    "ViolationSeries",
    "detect_violations",
    "VaRBacktestRunner",
    "VaRBacktestResult",
]
