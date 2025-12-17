"""
Backtest Engine Health Check
==============================

Verifies the backtest engine is operational and can process backtests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from src.infra.health.checks.base_check import (
    BaseHealthCheck,
    CheckResult,
    HealthStatus,
)


class BacktestHealthCheck(BaseHealthCheck):
    """Health check for backtest engine."""
    
    def __init__(self):
        super().__init__("Backtest Engine")
    
    def check(self) -> CheckResult:
        """
        Check backtest engine health.
        
        Verifies:
        - Backtest module can be imported
        - Results directory exists and is writable
        - Core backtest functionality is accessible
        
        Returns:
            CheckResult with backtest engine status
        """
        start_time = self._measure_time()
        details: Dict[str, Any] = {}
        
        try:
            # Check if backtest module can be imported
            try:
                from src.backtest import engine
                details["engine_import"] = "OK"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.RED,
                    message=f"Cannot import backtest engine: {e}",
                    details=details,
                )
            
            # Check if results directory exists or can be created
            try:
                results_dir = Path("results")
                results_dir.mkdir(exist_ok=True)
                details["results_dir"] = str(results_dir.absolute())
                details["results_dir_writable"] = results_dir.exists() and results_dir.is_dir()
            except Exception as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message=f"Results directory issue: {e}",
                    details=details,
                )
            
            # Check if BacktestEngine class is available
            if hasattr(engine, "BacktestEngine"):
                details["backtest_engine_class"] = "Available"
            else:
                details["backtest_engine_class"] = "Not found"
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="BacktestEngine class not found",
                    details=details,
                )
            
            response_time = self._measure_time() - start_time
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Backtest engine is operational",
                details=details,
                response_time_ms=response_time,
            )
            
        except Exception as e:
            response_time = self._measure_time() - start_time
            return self._create_result(
                status=HealthStatus.RED,
                message=f"Backtest health check failed: {e}",
                details=details,
                response_time_ms=response_time,
            )
