"""
Exchange Health Check

Prüft die Verfügbarkeit von Exchange-Verbindungen (Kraken, Binance, Coinbase).
"""

from typing import Dict, List

from .base_check import BaseHealthCheck, HealthCheckResult, HealthStatus


class ExchangeHealthCheck(BaseHealthCheck):
    """Health-Check für Exchange-Verbindungen"""

    def __init__(self):
        super().__init__("exchange")

    async def check(self) -> HealthCheckResult:
        """
        Prüfe Exchange-Module und Konfiguration.
        
        Returns:
            HealthCheckResult mit Status
        """
        details: Dict[str, any] = {
            "exchanges_available": [],
            "exchanges_configured": [],
        }
        
        try:
            # Prüfe ob CCXT verfügbar ist
            try:
                import ccxt
                details["ccxt_version"] = ccxt.__version__
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.RED,
                    message="CCXT library not available",
                    details=details,
                    error=str(e),
                )
            
            # Prüfe Exchange-Module
            try:
                from src.exchange import ExchangeClient
                details["exchange_module"] = "available"
            except ImportError as e:
                return self._create_result(
                    status=HealthStatus.YELLOW,
                    message="Exchange module not available",
                    details=details,
                    error=str(e),
                )
            
            # Prüfe verfügbare Exchanges in CCXT
            supported_exchanges = ["kraken", "binance", "coinbasepro"]
            for exchange_id in supported_exchanges:
                if hasattr(ccxt, exchange_id):
                    details["exchanges_available"].append(exchange_id)
            
            # Prüfe Config für Exchange-Einstellungen
            try:
                from src.core import load_config
                cfg = load_config()
                
                # Check if exchange config exists
                if hasattr(cfg, "exchange"):
                    for exchange_id in supported_exchanges:
                        if hasattr(cfg.exchange, exchange_id):
                            details["exchanges_configured"].append(exchange_id)
            except Exception as e:
                # Config-Probleme sind nicht kritisch für Exchange Health
                details["config_warning"] = str(e)
            
            # Status bestimmen
            if len(details["exchanges_available"]) == 0:
                status = HealthStatus.RED
                message = "No exchanges available"
            elif len(details["exchanges_available"]) < len(supported_exchanges):
                status = HealthStatus.YELLOW
                message = f"Only {len(details['exchanges_available'])}/{len(supported_exchanges)} exchanges available"
            else:
                status = HealthStatus.GREEN
                message = "All exchanges available"
            
            return self._create_result(
                status=status,
                message=message,
                details=details,
            )
            
        except Exception as e:
            return self._create_result(
                status=HealthStatus.RED,
                message="Unexpected error during exchange health check",
                details=details,
                error=str(e),
            )
