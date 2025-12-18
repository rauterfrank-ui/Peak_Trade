"""
Live Trading Health Check

Prüft die Verfügbarkeit und Funktionalität der Live-Trading-Module.
"""

from .base_check import BaseHealthCheck, HealthCheckResult, HealthStatus


class LiveHealthCheck(BaseHealthCheck):
    """Health-Check für Live-Trading"""

    def __init__(self):
        super().__init__("live")

    async def check(self) -> HealthCheckResult:
        """
        Prüfe Live-Trading-Module und Safety-Settings.
        
        Returns:
            HealthCheckResult mit Status
        """
        details = {}
        
        try:
            # Prüfe ob Live-Module importierbar sind
            try:
                from src.live import DryRunBroker, PaperBroker
                details["live_module"] = "available"
            except ImportError as e:
                # Live-Module nicht verfügbar ist OK (noch nicht implementiert)
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="Live module not available (expected in early stages)",
                    details=details,
                    error=str(e),
                )
            
            # Prüfe Config und Safety-Settings
            try:
                from src.core import load_config
                cfg = load_config()
                details["config_loaded"] = True
                
                # Check environment settings
                if hasattr(cfg, "environment"):
                    details["mode"] = cfg.environment.mode
                    details["enable_live_trading"] = cfg.environment.enable_live_trading
                    details["testnet_dry_run"] = cfg.environment.testnet_dry_run
                    
                    # Check if live trading is properly gated
                    if cfg.environment.enable_live_trading:
                        if cfg.environment.mode == "live":
                            return self._create_result(
                                status=HealthStatus.RED,
                                message="Live trading is enabled! This should be carefully reviewed.",
                                details=details,
                            )
                        else:
                            details["warning"] = "enable_live_trading=true but mode is not 'live'"
                    
                    # Safe configuration
                    if cfg.environment.mode == "paper" and not cfg.environment.enable_live_trading:
                        details["safe_mode"] = True
            except Exception as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="Config loading issues",
                    details=details,
                    error=str(e),
                )
            
            return self._create_result(
                status=HealthStatus.GREEN,
                message="Live trading configuration healthy",
                details=details,
            )
            
        except Exception as e:
            return self._create_result(
                status=HealthStatus.RED,
                message="Unexpected error during live health check",
                details=details,
                error=str(e),
            )
