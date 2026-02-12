"""
Resilient CCXT Exchange Client (Provider Module)
================================================

ccxt ist optional und darf nur in Provider-Modulen importiert werden.
Dieses Modul enthält die bestehende ResilientExchangeClient Implementierung.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import ccxt

from src.core.resilience import circuit_breaker, retry_with_backoff, health_check

logger = logging.getLogger(__name__)


class ResilientExchangeClient:
    """
    Exchange client with circuit breaker and retry logic (read-only).
    """

    def __init__(self, exchange_id: str = "kraken", config: Optional[Dict[str, Any]] = None):
        self.exchange_id = exchange_id
        self.config = config or {}

        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class(self.config)
            logger.info(f"ResilientExchangeClient initialized for {exchange_id}")
        except AttributeError:
            raise ValueError(f"Unknown exchange: {exchange_id}")

        health_check.register(f"exchange_{exchange_id}", self._health_check)

    @circuit_breaker(failure_threshold=3, recovery_timeout=60)
    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 100, since: Optional[int] = None
    ) -> List[List]:
        logger.debug(f"Fetching OHLCV: {symbol} {timeframe} (limit={limit})")
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol, timeframe=timeframe, limit=limit, since=since
            )
            logger.debug(f"Successfully fetched {len(ohlcv)} candles for {symbol}")
            return ohlcv
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching OHLCV for {symbol}: {e}")
            raise
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching OHLCV for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching OHLCV for {symbol}: {e}")
            raise

    @circuit_breaker(failure_threshold=3, recovery_timeout=60)
    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    def fetch_balance(self) -> Dict[str, Any]:
        logger.debug("Fetching account balance")
        try:
            balance = self.exchange.fetch_balance()
            logger.debug("Successfully fetched account balance")
            return balance
        except ccxt.AuthenticationError as e:
            logger.error(f"Authentication error fetching balance: {e}")
            raise
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching balance: {e}")
            raise
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching balance: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching balance: {e}")
            raise

    @circuit_breaker(failure_threshold=5, recovery_timeout=30)
    @retry_with_backoff(max_attempts=2, base_delay=0.5)
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        logger.debug(f"Fetching ticker for {symbol}")
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            logger.debug(f"Successfully fetched ticker for {symbol}")
            return ticker
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching ticker for {symbol}: {e}")
            raise
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching ticker for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching ticker for {symbol}: {e}")
            raise

    def _health_check(self) -> Tuple[bool, str]:
        try:
            if hasattr(self.exchange, "fetch_status"):
                status = self.exchange.fetch_status()
                if status.get("status") == "ok":
                    return True, f"Exchange {self.exchange_id} is operational"
                return False, f"Exchange {self.exchange_id} status: {status.get('status')}"
            self.exchange.load_markets()
            return True, f"Exchange {self.exchange_id} API is accessible"
        except Exception as e:
            logger.error(f"Exchange health check failed: {e}")
            return False, f"Exchange {self.exchange_id} health check failed: {str(e)}"


__all__ = ["ResilientExchangeClient"]
