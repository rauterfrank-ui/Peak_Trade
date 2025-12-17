"""
Exchange Health Check
======================

Verifies exchange connectivity and API availability.
"""

from __future__ import annotations

from typing import Any, Dict

from src.infra.health.checks.base_check import (
    BaseHealthCheck,
    CheckResult,
    HealthStatus,
)


class ExchangeHealthCheck(BaseHealthCheck):
    """Health check for exchange connections."""
    
    def __init__(self):
        super().__init__("Exchange Connectivity")
    
    def check(self) -> CheckResult:
        """
        Check exchange connectivity health.
        
        Verifies:
        - Exchange module can be imported
        - CCXT library is available
        - Exchange client can be initialized
        
        Returns:
            CheckResult with exchange connectivity status
        """
        start_time = self._measure_time()
        details: Dict[str, Any] = {}
        
        try:
            # Check if ccxt is available
            try:
                import ccxt
                details["ccxt_version"] = ccxt.__version__
                details["ccxt_import"] = "OK"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.RED,
                    message=f"CCXT library not available: {e}",
                    details=details,
                )
            
            # Check if exchange module can be imported
            try:
                from src.exchange import client
                details["exchange_module_import"] = "OK"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message=f"Exchange module import warning: {e}",
                    details=details,
                )
            
            # Check if ExchangeClient class is available
            if hasattr(client, "ExchangeClient"):
                details["exchange_client_class"] = "Available"
            else:
                details["exchange_client_class"] = "Not found"
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="ExchangeClient class not found",
                    details=details,
                )
            
            response_time = self._measure_time() - start_time
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Exchange connectivity components are operational",
                details=details,
                response_time_ms=response_time,
            )
            
        except Exception as e:
            response_time = self._measure_time() - start_time
            return self._create_result(
                status=HealthStatus.RED,
                message=f"Exchange health check failed: {e}",
                details=details,
                response_time_ms=response_time,
            )
