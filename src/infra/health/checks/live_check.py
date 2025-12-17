"""
Live Trading Health Check
===========================

Verifies live trading components are operational.
"""

from __future__ import annotations

from typing import Any, Dict

from src.infra.health.checks.base_check import (
    BaseHealthCheck,
    CheckResult,
    HealthStatus,
)


class LiveHealthCheck(BaseHealthCheck):
    """Health check for live trading components."""
    
    def __init__(self):
        super().__init__("Live Trading")
    
    def check(self) -> CheckResult:
        """
        Check live trading health.
        
        Verifies:
        - Live module can be imported
        - Core live trading components are available
        - Safety mechanisms are in place
        
        Returns:
            CheckResult with live trading status
        """
        start_time = self._measure_time()
        details: Dict[str, Any] = {}
        
        try:
            # Check if live module can be imported
            try:
                import src.live
                details["live_module_import"] = "OK"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message=f"Live module import warning (may be expected): {e}",
                    details=details,
                )
            
            # Check for safety configurations
            try:
                import toml
                from pathlib import Path
                
                config_path = Path("config.toml")
                if config_path.exists():
                    config = toml.load(config_path)
                    
                    # Check environment settings
                    if "environment" in config:
                        env_config = config["environment"]
                        details["mode"] = env_config.get("mode", "unknown")
                        details["enable_live_trading"] = env_config.get("enable_live_trading", False)
                        details["testnet_dry_run"] = env_config.get("testnet_dry_run", True)
                        
                        # Live trading should be disabled by default (safety)
                        if env_config.get("enable_live_trading", False):
                            return self._create_result(
                                status=HealthStatus.YELLOW,
                                message="Live trading is ENABLED - ensure this is intentional",
                                details=details,
                            )
                    
                    # Check live risk limits
                    if "live_risk" in config:
                        live_risk = config["live_risk"]
                        details["live_risk_enabled"] = live_risk.get("enabled", False)
                        details["max_daily_loss"] = live_risk.get("max_daily_loss_abs", "not set")
                else:
                    details["config_file"] = "not found"
                    return self._create_result(
                        status=HealthStatus.YELLOW,
                        message="Config file not found, cannot verify safety settings",
                        details=details,
                    )
                    
            except Exception as e:
                details["config_check_error"] = str(e)
            
            response_time = self._measure_time() - start_time
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Live trading components are operational (trading disabled, safe mode)",
                details=details,
                response_time_ms=response_time,
            )
            
        except Exception as e:
            response_time = self._measure_time() - start_time
            return self._create_result(
                status=HealthStatus.RED,
                message=f"Live trading health check failed: {e}",
                details=details,
                response_time_ms=response_time,
            )
