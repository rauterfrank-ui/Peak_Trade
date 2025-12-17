# src/exchange/kraken_testnet.py
"""
Peak_Trade: Kraken Testnet Exchange Client (Phase 35)
======================================================

Implementiert einen Exchange-Client fuer Kraken Testnet/Demo-Orders.

WICHTIG: Dieser Client ist AUSSCHLIESSLICH fuer Testnet/Demo-Nutzung!
         Echtes Live-Trading ist in Phase 35 NICHT implementiert.

Features:
- Order-Platzierung via Testnet-API
- Order-Status-Abfrage
- Mapping von OrderRequest -> API-Payload
- Mapping von API-Response -> OrderFill

Sicherheitsmerkmale:
- API-Keys werden NUR aus Environment-Variablen gelesen
- Keine hartcodierten Credentials
- Strenge Validierung vor jedem API-Call

API-Dokumentation:
- Kraken REST API: https://docs.kraken.com/api/
- Testnet: Kraken bietet kein echtes Testnet, daher nutzen wir:
  - Demo-Modus mit validate=true (Orders werden validiert, aber nicht ausgefuehrt)
  - Oder externe Testnet-Endpoints (falls verfuegbar)
"""
from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import logging
import os
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import requests

from src.orders.base import OrderFill, OrderRequest

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class ExchangeAPIError(Exception):
    """Basisklasse fuer Exchange-API-Fehler."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ExchangeAuthenticationError(ExchangeAPIError):
    """API-Key oder Secret ungueltig oder fehlend."""
    pass


class ExchangeOrderError(ExchangeAPIError):
    """Fehler bei der Order-Verarbeitung."""
    pass


class ExchangeRateLimitError(ExchangeAPIError):
    """Rate-Limit erreicht."""
    pass


class ExchangeNetworkError(ExchangeAPIError):
    """Netzwerkfehler bei API-Call."""
    pass


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class KrakenTestnetConfig:
    """
    Konfiguration fuer den Kraken Testnet Client.

    Attributes:
        base_url: Basis-URL fuer die Kraken API
        api_key_env_var: Name der ENV-Variable fuer den API-Key
        api_secret_env_var: Name der ENV-Variable fuer das API-Secret
        validate_only: Wenn True, werden Orders nur validiert (nicht ausgefuehrt)
        timeout_seconds: Timeout fuer HTTP-Requests
        max_retries: Max. Anzahl Retries bei Netzwerkfehlern
        rate_limit_ms: Rate-Limit-Pause zwischen Requests in ms
    """

    base_url: str = "https://api.kraken.com"
    api_key_env_var: str = "KRAKEN_TESTNET_API_KEY"
    api_secret_env_var: str = "KRAKEN_TESTNET_API_SECRET"
    validate_only: bool = True  # WICHTIG: Default ist True fuer Safety
    timeout_seconds: float = 30.0
    max_retries: int = 3
    rate_limit_ms: int = 1000

    def load_credentials(self) -> tuple[str | None, str | None]:
        """
        Laedt API-Credentials aus Environment-Variablen.

        Returns:
            Tuple von (api_key, api_secret), jeweils None wenn nicht gesetzt
        """
        api_key = os.environ.get(self.api_key_env_var)
        api_secret = os.environ.get(self.api_secret_env_var)
        return api_key, api_secret


# =============================================================================
# Response Dataclasses
# =============================================================================


@dataclass
class KrakenOrderResponse:
    """
    Response-Daten fuer eine Kraken Order.

    Attributes:
        txid: Transaction-ID(s) der Order
        descr: Order-Beschreibung
        validate_only: Ob die Order nur validiert wurde
        raw: Rohe API-Response
    """

    txid: list[str] = field(default_factory=list)
    descr: dict[str, Any] = field(default_factory=dict)
    validate_only: bool = False
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class KrakenOrderStatus:
    """
    Status einer Kraken Order.

    Attributes:
        txid: Transaction-ID der Order
        status: Order-Status (open, closed, canceled, expired)
        vol: Bestellte Menge
        vol_exec: Ausgefuehrte Menge
        avg_price: Durchschnittlicher Ausfuehrungspreis
        fee: Gebuehr
        timestamp: Zeitstempel der letzten Aenderung
        raw: Rohe API-Response
    """

    txid: str
    status: str
    vol: float
    vol_exec: float
    avg_price: float | None = None
    fee: float | None = None
    timestamp: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Symbol Mapping
# =============================================================================


# Mapping von Standard-Symbolen zu Kraken-Symbolen
SYMBOL_TO_KRAKEN: dict[str, str] = {
    "BTC/EUR": "XXBTZEUR",
    "BTC/USD": "XXBTZUSD",
    "ETH/EUR": "XETHZEUR",
    "ETH/USD": "XETHZUSD",
    "XRP/EUR": "XXRPZEUR",
    "XRP/USD": "XXRPZUSD",
    "LTC/EUR": "XLTCZEUR",
    "LTC/USD": "XLTCZUSD",
    "SOL/EUR": "SOLEUR",
    "SOL/USD": "SOLUSD",
    "DOT/EUR": "DOTEUR",
    "DOT/USD": "DOTUSD",
    "ADA/EUR": "ADAEUR",
    "ADA/USD": "ADAUSD",
}

# Reverse Mapping
KRAKEN_TO_SYMBOL: dict[str, str] = {v: k for k, v in SYMBOL_TO_KRAKEN.items()}


def to_kraken_symbol(symbol: str) -> str:
    """
    Konvertiert ein Standard-Symbol zu einem Kraken-Symbol.

    Args:
        symbol: Standard-Symbol (z.B. "BTC/EUR")

    Returns:
        Kraken-Symbol (z.B. "XXBTZEUR")

    Raises:
        ValueError: Bei unbekanntem Symbol
    """
    if symbol in SYMBOL_TO_KRAKEN:
        return SYMBOL_TO_KRAKEN[symbol]

    # Versuche direkte Verwendung (falls bereits Kraken-Format)
    if "/" not in symbol:
        return symbol

    # Versuche einfache Konvertierung: BTC/EUR -> BTCEUR
    simple = symbol.replace("/", "")
    return simple


def from_kraken_symbol(kraken_symbol: str) -> str:
    """
    Konvertiert ein Kraken-Symbol zu einem Standard-Symbol.

    Args:
        kraken_symbol: Kraken-Symbol (z.B. "XXBTZEUR")

    Returns:
        Standard-Symbol (z.B. "BTC/EUR")
    """
    if kraken_symbol in KRAKEN_TO_SYMBOL:
        return KRAKEN_TO_SYMBOL[kraken_symbol]

    # Fallback: Versuche zu parsen
    return kraken_symbol


# =============================================================================
# Kraken Testnet Client
# =============================================================================


class KrakenTestnetClient:
    """
    Kraken Testnet/Demo Exchange Client fuer Phase 35.

    Dieser Client ermoeglicht:
    - Order-Platzierung via Testnet-API (validate_only=true)
    - Order-Status-Abfragen
    - Mapping zwischen Peak_Trade-Strukturen und Kraken-API

    Sicherheitsmerkmale:
    - API-Keys werden NUR aus Environment-Variablen gelesen
    - Default: validate_only=True (Orders werden nicht echt ausgefuehrt)
    - Alle API-Calls werden geloggt

    WICHTIG: In Phase 35 werden Orders nur im Demo/Validate-Modus verarbeitet!

    Example:
        >>> config = KrakenTestnetConfig(
        ...     api_key_env_var="KRAKEN_TESTNET_API_KEY",
        ...     api_secret_env_var="KRAKEN_TESTNET_API_SECRET",
        ...     validate_only=True,
        ... )
        >>> client = KrakenTestnetClient(config)
        >>> order = OrderRequest(symbol="BTC/EUR", side="buy", quantity=0.01)
        >>> txid = client.create_order(order)
    """

    def __init__(self, config: KrakenTestnetConfig) -> None:
        """
        Initialisiert den Kraken Testnet Client.

        Args:
            config: KrakenTestnetConfig mit API-Einstellungen

        Raises:
            ExchangeAuthenticationError: Wenn keine API-Credentials gefunden
        """
        self._config = config
        self._api_key, self._api_secret = config.load_credentials()

        # Session fuer Connection-Pooling
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Peak_Trade/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
        })

        # Rate-Limiting
        self._last_request_time: float = 0.0

        logger.info(
            f"[KRAKEN TESTNET] Client initialisiert: "
            f"base_url={config.base_url}, "
            f"validate_only={config.validate_only}, "
            f"api_key_set={self._api_key is not None}"
        )

    @property
    def has_credentials(self) -> bool:
        """True wenn API-Credentials gesetzt sind."""
        return self._api_key is not None and self._api_secret is not None

    def _get_nonce(self) -> str:
        """Generiert einen Nonce fuer API-Requests."""
        return str(int(time.time() * 1000))

    def _sign_request(self, url_path: str, data: dict[str, Any]) -> str:
        """
        Signiert einen API-Request mit HMAC-SHA512.

        Args:
            url_path: API-Pfad (z.B. "/0/private/AddOrder")
            data: Request-Daten (inkl. nonce)

        Returns:
            Base64-encodierte Signatur
        """
        if not self._api_secret:
            raise ExchangeAuthenticationError("API-Secret nicht gesetzt")

        # Nonce muss im data dict sein
        nonce = data.get("nonce", "")

        # URL-encode der Daten
        post_data = urllib.parse.urlencode(data)

        # Signature: SHA256(nonce + postdata) + urlpath
        sha256_hash = hashlib.sha256((nonce + post_data).encode()).digest()
        message = url_path.encode() + sha256_hash

        # HMAC-SHA512
        secret_decoded = base64.b64decode(self._api_secret)
        signature = hmac.new(secret_decoded, message, hashlib.sha512)

        return base64.b64encode(signature.digest()).decode()

    def _rate_limit_wait(self) -> None:
        """Wartet falls noetig, um Rate-Limit einzuhalten."""
        if self._config.rate_limit_ms <= 0:
            return

        elapsed_ms = (time.time() - self._last_request_time) * 1000
        wait_ms = self._config.rate_limit_ms - elapsed_ms

        if wait_ms > 0:
            time.sleep(wait_ms / 1000.0)

    def _make_public_request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Fuehrt einen Public API Request aus.

        Args:
            endpoint: API-Endpoint (z.B. "/0/public/Ticker")
            params: Query-Parameter

        Returns:
            API-Response als Dict

        Raises:
            ExchangeNetworkError: Bei Netzwerkfehlern
            ExchangeAPIError: Bei API-Fehlern
        """
        self._rate_limit_wait()

        url = f"{self._config.base_url}{endpoint}"

        try:
            response = self._session.get(
                url,
                params=params,
                timeout=self._config.timeout_seconds,
            )
            self._last_request_time = time.time()

            response.raise_for_status()
            data = response.json()

            # Kraken-spezifische Fehlerbehandlung
            if data.get("error"):
                errors = data["error"]
                raise ExchangeAPIError(
                    f"Kraken API Error: {errors}",
                    status_code=response.status_code,
                    response=data,
                )

            return data.get("result", {})

        except requests.exceptions.Timeout:
            raise ExchangeNetworkError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise ExchangeNetworkError(f"Network error: {e}")

    def _make_private_request(
        self, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Fuehrt einen Private (authentifizierten) API Request aus.

        Args:
            endpoint: API-Endpoint (z.B. "/0/private/AddOrder")
            data: POST-Daten

        Returns:
            API-Response als Dict

        Raises:
            ExchangeAuthenticationError: Bei fehlenden Credentials
            ExchangeNetworkError: Bei Netzwerkfehlern
            ExchangeAPIError: Bei API-Fehlern
        """
        if not self.has_credentials:
            raise ExchangeAuthenticationError(
                f"API-Credentials nicht gesetzt. "
                f"Setze {self._config.api_key_env_var} und {self._config.api_secret_env_var}"
            )

        self._rate_limit_wait()

        url = f"{self._config.base_url}{endpoint}"

        # Nonce hinzufuegen
        post_data = data or {}
        post_data["nonce"] = self._get_nonce()

        # Request signieren
        signature = self._sign_request(endpoint, post_data)

        headers = {
            "API-Key": self._api_key,
            "API-Sign": signature,
        }

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

            # Kraken-spezifische Fehlerbehandlung
            if result.get("error"):
                errors = result["error"]
                error_str = ", ".join(errors) if isinstance(errors, list) else str(errors)

                # Spezifische Fehler erkennen
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

    # =========================================================================
    # Order-Methoden
    # =========================================================================

    def create_order(self, order: OrderRequest) -> str:
        """
        Sendet einen Order-Request an das Testnet.

        Im validate_only-Modus wird die Order nur validiert, aber nicht ausgefuehrt.
        Dies ist das Default-Verhalten in Phase 35.

        Args:
            order: OrderRequest-Objekt

        Returns:
            Exchange-Order-ID (txid) oder "VALIDATED" bei validate_only

        Raises:
            ExchangeOrderError: Bei Order-Fehlern
            ExchangeAuthenticationError: Bei Auth-Fehlern
        """
        logger.info(
            f"[KRAKEN TESTNET] create_order: "
            f"{order.side.upper()} {order.quantity} {order.symbol} @ {order.order_type}"
        )

        # Symbol konvertieren
        kraken_symbol = to_kraken_symbol(order.symbol)

        # Order-Typ mapping
        order_type = "market" if order.order_type == "market" else "limit"

        # Request-Daten bauen
        data: dict[str, Any] = {
            "pair": kraken_symbol,
            "type": order.side,  # "buy" oder "sell"
            "ordertype": order_type,
            "volume": str(order.quantity),
        }

        # Limit-Preis wenn vorhanden
        if order.order_type == "limit" and order.limit_price is not None:
            data["price"] = str(order.limit_price)

        # Validate-Only-Flag (WICHTIG fuer Testnet)
        if self._config.validate_only:
            data["validate"] = "true"
            logger.info("[KRAKEN TESTNET] validate_only=true - Order wird nur validiert")

        # Client-ID wenn vorhanden
        if order.client_id:
            # Kraken nutzt 'userref' fuer Client-IDs (nur Integer)
            # Wir hashen die client_id zu einem Integer
            userref = abs(hash(order.client_id)) % (2**31)
            data["userref"] = str(userref)

        try:
            result = self._make_private_request("/0/private/AddOrder", data)

            # Response parsen
            response = KrakenOrderResponse(
                txid=result.get("txid", []),
                descr=result.get("descr", {}),
                validate_only=self._config.validate_only,
                raw=result,
            )

            if self._config.validate_only:
                logger.info(
                    f"[KRAKEN TESTNET] Order validiert: descr={response.descr}"
                )
                return "VALIDATED"

            if response.txid:
                txid = response.txid[0]
                logger.info(f"[KRAKEN TESTNET] Order platziert: txid={txid}")
                return txid

            raise ExchangeOrderError(
                "Keine Transaction-ID in Response",
                response=result,
            )

        except ExchangeAPIError:
            raise
        except Exception as e:
            raise ExchangeOrderError(f"Order creation failed: {e}")

    def fetch_order_status(self, exchange_order_id: str) -> KrakenOrderStatus:
        """
        Fragt den Status einer Order ab.

        Args:
            exchange_order_id: Die Transaction-ID (txid) der Order

        Returns:
            KrakenOrderStatus mit aktuellen Daten

        Raises:
            ExchangeOrderError: Wenn Order nicht gefunden
            ExchangeAuthenticationError: Bei Auth-Fehlern
        """
        if exchange_order_id == "VALIDATED":
            # Validierte Orders haben keinen echten Status
            return KrakenOrderStatus(
                txid="VALIDATED",
                status="validated",
                vol=0.0,
                vol_exec=0.0,
                raw={"validated": True},
            )

        logger.debug(f"[KRAKEN TESTNET] fetch_order_status: txid={exchange_order_id}")

        data = {"txid": exchange_order_id}

        try:
            result = self._make_private_request("/0/private/QueryOrders", data)

            if exchange_order_id not in result:
                raise ExchangeOrderError(
                    f"Order not found: {exchange_order_id}",
                    response=result,
                )

            order_data = result[exchange_order_id]

            # Timestamp parsen
            timestamp = None
            if "closetm" in order_data:
                timestamp = datetime.fromtimestamp(
                    float(order_data["closetm"]), tz=UTC
                )
            elif "opentm" in order_data:
                timestamp = datetime.fromtimestamp(
                    float(order_data["opentm"]), tz=UTC
                )

            return KrakenOrderStatus(
                txid=exchange_order_id,
                status=order_data.get("status", "unknown"),
                vol=float(order_data.get("vol", 0)),
                vol_exec=float(order_data.get("vol_exec", 0)),
                avg_price=float(order_data.get("price", 0)) or None,
                fee=float(order_data.get("fee", 0)) or None,
                timestamp=timestamp,
                raw=order_data,
            )

        except ExchangeAPIError:
            raise
        except Exception as e:
            raise ExchangeOrderError(f"Order status query failed: {e}")

    def fetch_order_as_fill(self, exchange_order_id: str, original_order: OrderRequest) -> OrderFill | None:
        """
        Wandelt Order-Status in ein OrderFill um (wenn ausgefuehrt).

        Args:
            exchange_order_id: Die Transaction-ID (txid) der Order
            original_order: Die urspruengliche OrderRequest

        Returns:
            OrderFill wenn Order ausgefuehrt, sonst None
        """
        status = self.fetch_order_status(exchange_order_id)

        # Nur bei geschlossenen/ausgefuehrten Orders ein Fill erzeugen
        if status.status not in ("closed", "filled"):
            return None

        if status.vol_exec <= 0:
            return None

        return OrderFill(
            symbol=original_order.symbol,
            side=original_order.side,
            quantity=status.vol_exec,
            price=status.avg_price or 0.0,
            timestamp=status.timestamp or datetime.now(UTC),
            fee=status.fee,
            fee_currency="EUR",  # Kraken nutzt meist die Quote-Waehrung
        )

    def cancel_order(self, exchange_order_id: str) -> bool:
        """
        Storniert eine offene Order.

        Args:
            exchange_order_id: Die Transaction-ID (txid) der Order

        Returns:
            True wenn erfolgreich storniert

        Raises:
            ExchangeOrderError: Bei Stornierungsfehlern
        """
        if exchange_order_id == "VALIDATED":
            logger.info("[KRAKEN TESTNET] Validierte Order kann nicht storniert werden")
            return True

        logger.info(f"[KRAKEN TESTNET] cancel_order: txid={exchange_order_id}")

        data = {"txid": exchange_order_id}

        try:
            result = self._make_private_request("/0/private/CancelOrder", data)

            count = result.get("count", 0)
            if count > 0:
                logger.info(f"[KRAKEN TESTNET] Order storniert: count={count}")
                return True

            return False

        except ExchangeAPIError:
            raise
        except Exception as e:
            raise ExchangeOrderError(f"Order cancellation failed: {e}")

    # =========================================================================
    # Market-Data-Methoden (Public)
    # =========================================================================

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        """
        Holt aktuelle Ticker-Daten fuer ein Symbol.

        Args:
            symbol: Trading-Pair (z.B. "BTC/EUR")

        Returns:
            Dict mit Ticker-Daten (last, bid, ask, etc.)
        """
        kraken_symbol = to_kraken_symbol(symbol)
        result = self._make_public_request("/0/public/Ticker", {"pair": kraken_symbol})

        # Kraken gibt Dict mit Symbol als Key zurueck
        ticker_data = next(iter(result.values()), {})

        return {
            "symbol": symbol,
            "last": float(ticker_data.get("c", [0])[0]) if ticker_data.get("c") else None,
            "bid": float(ticker_data.get("b", [0])[0]) if ticker_data.get("b") else None,
            "ask": float(ticker_data.get("a", [0])[0]) if ticker_data.get("a") else None,
            "volume": float(ticker_data.get("v", [0, 0])[1]) if ticker_data.get("v") else None,
            "raw": ticker_data,
        }

    def fetch_balance(self) -> dict[str, float]:
        """
        Holt Account-Balances.

        Returns:
            Dict von Asset -> Balance

        Raises:
            ExchangeAuthenticationError: Bei Auth-Fehlern
        """
        result = self._make_private_request("/0/private/Balance")

        balances: dict[str, float] = {}
        for asset, balance in result.items():
            with contextlib.suppress(ValueError, TypeError):
                balances[asset] = float(balance)

        return balances

    def close(self) -> None:
        """Schliesst die HTTP-Session."""
        self._session.close()
        logger.debug("[KRAKEN TESTNET] Session geschlossen")

    def __enter__(self) -> KrakenTestnetClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


# =============================================================================
# Factory-Funktion
# =============================================================================


def create_kraken_testnet_client_from_config(
    cfg: PeakConfig,
    config_prefix: str = "exchange.kraken_testnet",
) -> KrakenTestnetClient:
    """
    Factory-Funktion fuer KrakenTestnetClient aus PeakConfig.

    Args:
        cfg: PeakConfig-Instanz
        config_prefix: Config-Pfad-Prefix (default: "exchange.kraken_testnet")

    Returns:
        Konfigurierter KrakenTestnetClient

    Example:
        >>> from src.core.peak_config import load_config
        >>> cfg = load_config("config/config.toml")
        >>> client = create_kraken_testnet_client_from_config(cfg)
    """

    config = KrakenTestnetConfig(
        base_url=cfg.get(f"{config_prefix}.base_url", "https://api.kraken.com"),
        api_key_env_var=cfg.get(f"{config_prefix}.api_key_env_var", "KRAKEN_TESTNET_API_KEY"),
        api_secret_env_var=cfg.get(f"{config_prefix}.api_secret_env_var", "KRAKEN_TESTNET_API_SECRET"),
        validate_only=cfg.get(f"{config_prefix}.validate_only", True),
        timeout_seconds=float(cfg.get(f"{config_prefix}.timeout_seconds", 30.0)),
        max_retries=int(cfg.get(f"{config_prefix}.max_retries", 3)),
        rate_limit_ms=int(cfg.get(f"{config_prefix}.rate_limit_ms", 1000)),
    )

    return KrakenTestnetClient(config)
