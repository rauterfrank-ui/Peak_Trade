"""
Backtest Health Check

Prüft die Verfügbarkeit und Funktionalität der Backtest-Engine.
"""

import sys
from pathlib import Path

from .base_check import BaseHealthCheck, HealthCheckResult, HealthStatus


class BacktestHealthCheck(BaseHealthCheck):
    """Health-Check für Backtest Engine"""

    def __init__(self):
        super().__init__("backtest")

    async def check(self) -> HealthCheckResult:
        """
        Prüfe Backtest-Module und Konfiguration.
        
        Returns:
            HealthCheckResult mit Status
        """
        details = {}
        
        try:
            # Prüfe ob Backtest-Module importierbar sind
            try:
                from src.backtest import BacktestEngine
                details["backtest_module"] = "available"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.RED,
                    message="Backtest module not available",
                    details=details,
                    error=str(e),
                )
            
            # Prüfe Config
            try:
                from src.core import load_config
                cfg = load_config()
                details["config_loaded"] = True
                details["initial_cash"] = cfg.backtest.initial_cash
                details["results_dir"] = cfg.backtest.results_dir
            except Exception as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="Config loading issues",
                    details=details,
                    error=str(e),
                )
            
            # Prüfe ob Results-Directory existiert oder erstellt werden kann
            results_dir = Path(cfg.backtest.results_dir)
            if not results_dir.exists():
                try:
                    results_dir.mkdir(parents=True, exist_ok=True)
                    details["results_dir_created"] = True
                except Exception as e:
                    return self._create_result(
                        status=HealthStatus.YELLOW,
                        message="Cannot create results directory",
                        details=details,
                        error=str(e),
                    )
            else:
                details["results_dir_exists"] = True
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Backtest engine healthy",
                details=details,
            )
            
        except Exception as e:
            return self._create_result(
                status=HealthStatus.RED,
                message="Unexpected error during backtest health check",
                details=details,
                error=str(e),
            )
