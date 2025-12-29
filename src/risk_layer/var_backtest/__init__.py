"""
VaR Backtesting Module
======================

Provides statistical backtesting capabilities for VaR models,
including:
- Kupiec Proportion of Failures (POF) test
- Christoffersen Independence & Conditional Coverage tests (Risk Layer v1.0)
- Basel Traffic Light System (Risk Layer v1.0)

This module is designed for research and backtesting only.
It is NOT intended for real-time/live trading validation.
"""

from src.risk_layer.var_backtest.kupiec_pof import (
    KupiecPOFOutput,
    KupiecResult,
    kupiec_pof_test,
    quick_kupiec_check,
    # Phase 7: Direct n/x/alpha API
    KupiecLRResult,
    kupiec_lr_uc,
    kupiec_from_exceedances,
)
from src.risk_layer.var_backtest.var_backtest_runner import (
    VaRBacktestResult,
    VaRBacktestRunner,
)
from src.risk_layer.var_backtest.violation_detector import (
    ViolationSeries,
    detect_violations,
)

# Risk Layer v1.0 - Extended Backtesting
from src.risk_layer.var_backtest.christoffersen_tests import (
    ChristoffersenResult,
    christoffersen_independence_test,
    christoffersen_conditional_coverage_test,
    run_full_var_backtest,
)
from src.risk_layer.var_backtest.traffic_light import (
    BaselZone,
    TrafficLightResult,
    TrafficLightMonitor,
    basel_traffic_light,
    compute_zone_thresholds,
    traffic_light_recommendation,
)

# Phase 9A: Duration-Based Independence Diagnostic
from src.risk_layer.var_backtest.duration_diagnostics import (
    DurationDiagnosticResult,
    ExponentialTestResult,
    extract_exceedance_durations,
    duration_independence_diagnostic,
    format_duration_diagnostic,
)

# Phase 9B: Rolling-Window Evaluation
from src.risk_layer.var_backtest.rolling_evaluation import (
    RollingEvaluationResult,
    RollingSummary,
    RollingWindowResult,
    rolling_evaluation,
    format_rolling_summary,
    get_failing_windows,
    get_worst_window,
)

__all__ = [
    # Kupiec POF Test
    "KupiecResult",
    "KupiecPOFOutput",
    "kupiec_pof_test",
    "quick_kupiec_check",
    # Phase 7: Direct n/x/alpha API
    "KupiecLRResult",
    "kupiec_lr_uc",
    "kupiec_from_exceedances",
    # Violation Detection
    "ViolationSeries",
    "detect_violations",
    # Backtest Runner
    "VaRBacktestRunner",
    "VaRBacktestResult",
    # Christoffersen Tests (Risk Layer v1.0)
    "ChristoffersenResult",
    "christoffersen_independence_test",
    "christoffersen_conditional_coverage_test",
    "run_full_var_backtest",
    # Basel Traffic Light (Risk Layer v1.0)
    "BaselZone",
    "TrafficLightResult",
    "TrafficLightMonitor",
    "basel_traffic_light",
    "compute_zone_thresholds",
    "traffic_light_recommendation",
    # Phase 9A: Duration-Based Independence Diagnostic
    "DurationDiagnosticResult",
    "ExponentialTestResult",
    "extract_exceedance_durations",
    "duration_independence_diagnostic",
    "format_duration_diagnostic",
    # Phase 9B: Rolling-Window Evaluation
    "RollingEvaluationResult",
    "RollingSummary",
    "RollingWindowResult",
    "rolling_evaluation",
    "format_rolling_summary",
    "get_failing_windows",
    "get_worst_window",
]
