"""
Portfolio Health Check

Prüft die Verfügbarkeit und Funktionalität der Portfolio-Module.
"""

from .base_check import BaseHealthCheck, HealthCheckResult, HealthStatus


class PortfolioHealthCheck(BaseHealthCheck):
    """Health-Check für Portfolio-Module"""

    def __init__(self):
        super().__init__("portfolio")

    async def check(self) -> HealthCheckResult:
        """
        Prüfe Portfolio-Module und Konfiguration.
        
        Returns:
            HealthCheckResult mit Status
        """
        details = {}
        
        try:
            # Prüfe ob Portfolio-Module importierbar sind
            try:
                from src.portfolio import PortfolioManager
                details["portfolio_module"] = "available"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.RED,
                    message="Portfolio module not available",
                    details=details,
                    error=str(e),
                )
            
            # Prüfe Config
            try:
                from src.core import load_config
                cfg = load_config()
                details["config_loaded"] = True
                
                # Check portfolio-related config
                if hasattr(cfg, "portfolio"):
                    details["portfolio_config"] = "available"
            except Exception as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="Config loading issues",
                    details=details,
                    error=str(e),
                )
            
            # Prüfe Risk-Module (wichtig für Portfolio)
            try:
                from src.risk import calc_position_size
                details["risk_module"] = "available"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="Risk module not available",
                    details=details,
                    error=str(e),
                )
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Portfolio modules healthy",
                details=details,
            )
            
        except Exception as e:
            return self._create_result(
                status=HealthStatus.RED,
                message="Unexpected error during portfolio health check",
                details=details,
                error=str(e),
            )
