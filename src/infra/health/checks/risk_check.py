"""
Risk Management Health Check
==============================

Verifies risk management modules are operational.
"""

from __future__ import annotations

from typing import Any, Dict

from src.infra.health.checks.base_check import (
    BaseHealthCheck,
    CheckResult,
    HealthStatus,
)


class RiskHealthCheck(BaseHealthCheck):
    """Health check for risk management."""
    
    def __init__(self):
        super().__init__("Risk Management")
    
    def check(self) -> CheckResult:
        """
        Check risk management health.
        
        Verifies:
        - Risk module can be imported
        - Core risk management classes are available
        
        Returns:
            CheckResult with risk management status
        """
        start_time = self._measure_time()
        details: Dict[str, Any] = {}
        
        try:
            # Check if risk module can be imported
            try:
                import src.risk
                details["risk_module_import"] = "OK"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.RED,
                    message=f"Cannot import risk module: {e}",
                    details=details,
                )
            
            # Check for key risk components
            from pathlib import Path
            risk_dir = Path("src/risk")
            if risk_dir.exists():
                py_files = list(risk_dir.glob("*.py"))
                details["risk_files_count"] = len(py_files)
                
                # Check for common risk management files
                expected_files = ["position_sizer.py", "guards.py", "limits.py"]
                found_files = [f.name for f in py_files]
                
                available = [f for f in expected_files if f in found_files]
                missing = [f for f in expected_files if f not in found_files]
                
                details["available_components"] = available
                if missing:
                    details["missing_components"] = missing
            else:
                return self._create_result(
                    status=HealthStatus.RED,
                    message="Risk directory not found",
                    details=details,
                )
            
            response_time = self._measure_time() - start_time
            
            if missing:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message=f"Some risk components missing: {', '.join(missing)}",
                    details=details,
                    response_time_ms=response_time,
                )
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Risk management is operational",
                details=details,
                response_time_ms=response_time,
            )
            
        except Exception as e:
            response_time = self._measure_time() - start_time
            return self._create_result(
                status=HealthStatus.RED,
                message=f"Risk health check failed: {e}",
                details=details,
                response_time_ms=response_time,
            )
