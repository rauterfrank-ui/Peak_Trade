"""
Risk Health Check

Prüft die Verfügbarkeit und Funktionalität der Risk-Management-Module.
"""

from .base_check import BaseHealthCheck, HealthCheckResult, HealthStatus


class RiskHealthCheck(BaseHealthCheck):
    """Health-Check für Risk-Management"""

    def __init__(self):
        super().__init__("risk")

    async def check(self) -> HealthCheckResult:
        """
        Prüfe Risk-Management-Module und Konfiguration.
        
        Returns:
            HealthCheckResult mit Status
        """
        details = {}
        
        try:
            # Prüfe ob Risk-Module importierbar sind
            try:
                from src.risk import calc_position_size, PositionRequest
                details["risk_module"] = "available"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.RED,
                    message="Risk module not available",
                    details=details,
                    error=str(e),
                )
            
            # Prüfe Config
            try:
                from src.core import load_config
                cfg = load_config()
                details["config_loaded"] = True
                
                # Check risk-related config
                if hasattr(cfg, "risk"):
                    details["risk_per_trade"] = cfg.risk.risk_per_trade
                    details["max_position_size"] = cfg.risk.max_position_size
                    details["max_daily_loss"] = cfg.risk.max_daily_loss
                    
                    # Optional fields
                    if hasattr(cfg.risk, "max_drawdown"):
                        details["max_drawdown"] = cfg.risk.max_drawdown
                    
                    # Validate risk parameters
                    warnings = []
                    if cfg.risk.risk_per_trade > 0.02:
                        warnings.append("risk_per_trade > 2% (high risk)")
                    if cfg.risk.max_position_size > 0.5:
                        warnings.append("max_position_size > 50% (high concentration)")
                    if cfg.risk.max_daily_loss > 0.05:
                        warnings.append("max_daily_loss > 5% (high risk)")
                    
                    if warnings:
                        details["warnings"] = warnings
                        return self._create_result(
                            status=HealthStatus.YELLOW,
                            message="Risk parameters have warnings",
                            details=details,
                        )
            except Exception as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="Config loading issues",
                    details=details,
                    error=str(e),
                )
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Risk management healthy",
                details=details,
            )
            
        except Exception as e:
            return self._create_result(
                status=HealthStatus.RED,
                message="Unexpected error during risk health check",
                details=details,
                error=str(e),
            )
