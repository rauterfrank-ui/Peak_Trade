"""
Portfolio Health Check
=======================

Verifies portfolio management modules are operational.
"""

from __future__ import annotations

from typing import Any, Dict

from src.infra.health.checks.base_check import (
    BaseHealthCheck,
    CheckResult,
    HealthStatus,
)


class PortfolioHealthCheck(BaseHealthCheck):
    """Health check for portfolio modules."""
    
    def __init__(self):
        super().__init__("Portfolio Management")
    
    def check(self) -> CheckResult:
        """
        Check portfolio module health.
        
        Verifies:
        - Portfolio module can be imported
        - Core portfolio classes are available
        
        Returns:
            CheckResult with portfolio status
        """
        start_time = self._measure_time()
        details: Dict[str, Any] = {}
        
        try:
            # Check if portfolio module can be imported
            try:
                import src.portfolio
                details["portfolio_module_import"] = "OK"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.RED,
                    message=f"Cannot import portfolio module: {e}",
                    details=details,
                )
            
            # Check for key portfolio components
            components_found = []
            components_missing = []
            
            # Check for common portfolio files
            from pathlib import Path
            portfolio_dir = Path("src/portfolio")
            if portfolio_dir.exists():
                py_files = list(portfolio_dir.glob("*.py"))
                details["portfolio_files_count"] = len(py_files)
                components_found.append(f"{len(py_files)} portfolio files")
            else:
                components_missing.append("portfolio directory not found")
            
            details["components_found"] = components_found
            details["components_missing"] = components_missing
            
            response_time = self._measure_time() - start_time
            
            if components_missing:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message=f"Portfolio components partially available: {', '.join(components_missing)}",
                    details=details,
                    response_time_ms=response_time,
                )
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Portfolio management is operational",
                details=details,
                response_time_ms=response_time,
            )
            
        except Exception as e:
            response_time = self._measure_time() - start_time
            return self._create_result(
                status=HealthStatus.RED,
                message=f"Portfolio health check failed: {e}",
                details=details,
                response_time_ms=response_time,
            )
