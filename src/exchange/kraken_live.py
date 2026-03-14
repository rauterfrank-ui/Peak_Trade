# src/exchange/kraken_live.py
"""
Peak_Trade: Kraken Live Exchange Client (Option A Slice 5)
=========================================================

Implementiert einen Exchange-Client für echte Kraken Live-Orders.
Erfüllt das TradingExchangeClient Protocol für den bounded-pilot Flow.

WICHTIG: Dieser Client sendet ECHTE Orders an die Kraken Live-API!
         Nur nach Governance-Freigabe und Entry Contract nutzen.

Features:
- Order-Platzierung via Kraken REST API (AddOrder)
- Order-Status-Abfrage (QueryOrders)
- Order-Stornierung (CancelOrder)
- Credentials aus KRAKEN_API_KEY, KRAKEN_API_SECRET (ENV)

Sicherheitsmerkmale:
- API-Keys NUR aus Environment-Variablen
- Keine validate_only-Option (echte Orders)
- Strikte Trennung von KrakenTestnetClient (andere ENV-Vars)
"""

from __future__ import annotations

import hashlib
import hmac
import base64
import logging
import os
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from src.exchange.base import (
    ExchangeOrderResult,
    ExchangeOrderStatus,
    TradingOrderSide,
    TradingOrderType,
)

logger = logging.getLogger(__name__)

# Reuse from kraken_testnet
from src.exchange.kraken_testnet import (
    ExchangeAPIError,
    ExchangeAuthenticationError,
    ExchangeOrderError,
    ExchangeNetworkError,
    ExchangeRateLimitError,
    to_kraken_symbol,
)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class KrakenLiveConfig:
    """
    Konfiguration für den Kraken Live Client.

    Attributes:
        base_url: Basis-URL für die Kraken API
        api_key_env_var: Name der ENV-Variable für den API-Key
        api_secret_env_var: Name der ENV-Variable für das API-Secret
        timeout_seconds: Timeout für HTTP-Requests
        max_retries: Max. Anzahl Retries bei Netzwerkfehlern
        rate_limit_ms: Rate-Limit-Pause zwischen Requests in ms
    """

    base_url: str = "https://api.kraken.com"
    api_key_env_var: str = "KRAKEN_API_KEY"
    api_secret_env_var: str = "KRAKEN_API_SECRET"
    timeout_seconds: float = 30.0
    max_retries: int = 3
    rate_limit_ms: int = 1000

    def load_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """Lädt API-Credentials aus Environment-Variablen."""
        api_key = os.environ.get(self.api_key_env_var)
        api_secret = os.environ.get(self.api_secret_env_var)
        return api_key, api_secret


def _kraken_status_to_exchange_status(kraken_status: str, vol_exec: float) -> ExchangeOrderStatus:
    """Mappt Kraken-Status auf ExchangeOrderStatus."""
    s = (kraken_status or "").lower()
    if s in ("pending",):
        return ExchangeOrderStatus.PENDING
    if s in ("open",):
        return ExchangeOrderStatus.PARTIALLY_FILLED if vol_exec > 0 else ExchangeOrderStatus.OPEN
    if s in ("closed", "filled"):
        return ExchangeOrderStatus.FILLED
    if s in ("canceled", "cancelled"):
        return ExchangeOrderStatus.CANCELLED
    if s in ("expired",):
        return ExchangeOrderStatus.EXPIRED
    if s in ("rejected",):
        return ExchangeOrderStatus.REJECTED
    return ExchangeOrderStatus.PENDING


# =============================================================================
# Kraken Live Client
# =============================================================================


class KrakenLiveClient:
    """
    Kraken Live Exchange Client (TradingExchangeClient).

    Implementiert das TradingExchangeClient Protocol für echte Live-Orders.
    Nutzt KRAKEN_API_KEY und KRAKEN_API_SECRET aus der Umgebung.

    WICHTIG: Sendet echte Orders! Nur nach Governance-Freigabe nutzen.

    Example:
        >>> config = KrakenLiveConfig()
        >>> client = KrakenLiveClient(config)
        >>> order_id = client.place_order("BTC/EUR", "buy", 0.01, "market")
        >>> status = client.get_order_status(order_id)
    """

    def __init__(self, config: KrakenLiveConfig) -> None:
        self._config = config
        self._api_key, self._api_secret = config.load_credentials()

        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Peak_Trade/1.0 (KrakenLive)",
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        self._last_request_time: float = 0.0

        logger.info(
            f"[KRAKEN LIVE] Client initialisiert: base_url={config.base_url}, "
            f"api_key_set={self._api_key is not None}"
        )

    @property
    def has_credentials(self) -> bool:
        """True wenn API-Credentials gesetzt sind."""
        return self._api_key is not None and self._api_secret is not None

    def get_name(self) -> str:
        """Name des Exchange-Clients (TradingExchangeClient Protocol)."""
        return "kraken_live"

    def _get_nonce(self) -> str:
        return str(int(time.time() * 1000))

    def _sign_request(self, url_path: str, data: Dict[str, Any]) -> str:
        if not self._api_secret:
            raise ExchangeAuthenticationError("API-Secret nicht gesetzt")
        nonce = data.get("nonce", "")
        post_data = urllib.parse.urlencode(data)
        sha256_hash = hashlib.sha256((nonce + post_data).encode()).digest()
        message = url_path.encode() + sha256_hash
        secret_decoded = base64.b64decode(self._api_secret)
        signature = hmac.new(secret_decoded, message, hashlib.sha512)
        return base64.b64encode(signature.digest()).decode()

    def _rate_limit_wait(self) -> None:
        if self._config.rate_limit_ms <= 0:
            return
        elapsed_ms = (time.time() - self._last_request_time) * 1000
        wait_ms = self._config.rate_limit_ms - elapsed_ms
        if wait_ms > 0:
            time.sleep(wait_ms / 1000.0)

    def _make_private_request(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.has_credentials:
            raise ExchangeAuthenticationError(
                f"API-Credentials nicht gesetzt. "
                f"Setze {self._config.api_key_env_var} und {self._config.api_secret_env_var}"
            )
        self._rate_limit_wait()
        url = f"{self._config.base_url}{endpoint}"
        post_data = data or {}
        post_data["nonce"] = self._get_nonce()
        signature = self._sign_request(endpoint, post_data)
        headers = {"API-Key": self._api_key, "API-Sign": signature}

        try:
            response = self._session.post(
                url,
                data=post_data,
                headers=headers,
                timeout=self._config.timeout_seconds,
            )
            self._last_request_time = time.time()
            response.raise_for_status()
            result = response.json()

            if result.get("error"):
                errors = result["error"]
                error_str = ", ".join(errors) if isinstance(errors, list) else str(errors)
                if "EAPI:Invalid key" in error_str or "Invalid" in error_str:
                    raise ExchangeAuthenticationError(
                        f"Authentication failed: {error_str}",
                        status_code=response.status_code,
                        response=result,
                    )
                if "Rate limit" in error_str or "EAPI:Rate limit" in error_str:
                    raise ExchangeRateLimitError(
                        f"Rate limit exceeded: {error_str}",
                        status_code=response.status_code,
                        response=result,
                    )
                raise ExchangeAPIError(
                    f"Kraken API Error: {error_str}",
                    status_code=response.status_code,
                    response=result,
                )
            return result.get("result", {})

        except requests.exceptions.Timeout:
            raise ExchangeNetworkError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise ExchangeNetworkError(f"Network error: {e}")

    def place_order(
        self,
        symbol: str,
        side: TradingOrderSide,
        quantity: float,
        order_type: TradingOrderType = "market",
        limit_price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> str:
        """
        Platziert eine Order auf der Kraken Live-API (TradingExchangeClient Protocol).

        WICHTIG: Echte Order! Kein validate_only.
        """
        if quantity <= 0:
            raise ValueError(f"quantity muss > 0 sein: {quantity}")
        if order_type == "limit" and limit_price is None:
            raise ValueError("limit_price erforderlich für Limit-Orders")
        if limit_price is not None and limit_price <= 0:
            raise ValueError(f"limit_price muss > 0 sein: {limit_price}")

        logger.info(f"[KRAKEN LIVE] place_order: {side.upper()} {quantity} {symbol} @ {order_type}")

        kraken_symbol = to_kraken_symbol(symbol)
        ordertype = "market" if order_type == "market" else "limit"

        data: Dict[str, Any] = {
            "pair": kraken_symbol,
            "type": side,
            "ordertype": ordertype,
            "volume": str(quantity),
        }
        if order_type == "limit" and limit_price is not None:
            data["price"] = str(limit_price)
        if client_order_id:
            userref = abs(hash(client_order_id)) % (2**31)
            data["userref"] = str(userref)

        try:
            result = self._make_private_request("/0/private/AddOrder", data)
            txid_list = result.get("txid", [])
            if not txid_list:
                raise ExchangeOrderError(
                    "Keine Transaction-ID in Response",
                    response=result,
                )
            txid = txid_list[0]
            logger.info(f"[KRAKEN LIVE] Order platziert: txid={txid}")
            return txid
        except ExchangeAPIError:
            raise
        except Exception as e:
            raise ExchangeOrderError(f"Order creation failed: {e}")

    def get_order_status(self, exchange_order_id: str) -> ExchangeOrderResult:
        """
        Fragt den Status einer Order ab (TradingExchangeClient Protocol).
        """
        logger.debug(f"[KRAKEN LIVE] get_order_status: txid={exchange_order_id}")

        data = {"txid": exchange_order_id}
        try:
            result = self._make_private_request("/0/private/QueryOrders", data)
            if exchange_order_id not in result:
                raise ExchangeOrderError(
                    f"Order not found: {exchange_order_id}",
                    response=result,
                )
            order_data = result[exchange_order_id]
            status_str = order_data.get("status", "unknown")
            vol = float(order_data.get("vol", 0))
            vol_exec = float(order_data.get("vol_exec", 0))
            avg_price = float(order_data.get("price", 0)) or None
            fee = float(order_data.get("fee", 0)) or None

            exchange_status = _kraken_status_to_exchange_status(status_str, vol_exec)
            return ExchangeOrderResult(
                exchange_order_id=exchange_order_id,
                status=exchange_status,
                filled_qty=vol_exec,
                avg_price=avg_price,
                fee=fee,
                fee_currency="EUR",
                raw=order_data,
            )
        except ExchangeAPIError:
            raise
        except Exception as e:
            raise ExchangeOrderError(f"Order status query failed: {e}")

    def cancel_order(self, exchange_order_id: str) -> bool:
        """
        Storniert eine offene Order (TradingExchangeClient Protocol).
        """
        logger.info(f"[KRAKEN LIVE] cancel_order: txid={exchange_order_id}")

        data = {"txid": exchange_order_id}
        try:
            result = self._make_private_request("/0/private/CancelOrder", data)
            count = result.get("count", 0)
            if count > 0:
                logger.info(f"[KRAKEN LIVE] Order storniert: count={count}")
                return True
            return False
        except ExchangeAPIError:
            raise
        except Exception as e:
            raise ExchangeOrderError(f"Order cancellation failed: {e}")

    def close(self) -> None:
        """Schließt die HTTP-Session."""
        self._session.close()
        logger.debug("[KRAKEN LIVE] Session geschlossen")

    def __enter__(self) -> "KrakenLiveClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# =============================================================================
# Factory
# =============================================================================


def create_kraken_live_client_from_config(
    cfg: Any,
    config_prefix: str = "exchange.kraken_live",
) -> KrakenLiveClient:
    """
    Factory für KrakenLiveClient aus PeakConfig.

    Args:
        cfg: PeakConfig-Instanz (oder kompatibel mit .get())
        config_prefix: Config-Pfad-Prefix

    Returns:
        Konfigurierter KrakenLiveClient
    """
    config = KrakenLiveConfig(
        base_url=cfg.get(f"{config_prefix}.base_url", "https://api.kraken.com"),
        api_key_env_var=cfg.get(f"{config_prefix}.api_key_env_var", "KRAKEN_API_KEY"),
        api_secret_env_var=cfg.get(f"{config_prefix}.api_secret_env_var", "KRAKEN_API_SECRET"),
        timeout_seconds=float(cfg.get(f"{config_prefix}.timeout_seconds", 30.0)),
        max_retries=int(cfg.get(f"{config_prefix}.max_retries", 3)),
        rate_limit_ms=int(cfg.get(f"{config_prefix}.rate_limit_ms", 1000)),
    )
    return KrakenLiveClient(config)
