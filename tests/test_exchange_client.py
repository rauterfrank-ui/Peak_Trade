# tests/test_exchange_client.py
"""
Peak_Trade: Tests fuer KrakenTestnetClient (Phase 35)
=====================================================

Tests fuer den Exchange-Client ohne echte Netzwerk-Calls.
Verwendet Mocking um API-Responses zu simulieren.

WICHTIG: Diese Tests machen KEINE echten API-Calls!
         Alle Netzwerk-Operationen werden gemockt.
"""
from __future__ import annotations

import base64
import hashlib
import json
import pytest
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

from src.exchange.kraken_testnet import (
    KrakenTestnetClient,
    KrakenTestnetConfig,
    KrakenOrderResponse,
    KrakenOrderStatus,
    ExchangeAPIError,
    ExchangeAuthenticationError,
    ExchangeOrderError,
    ExchangeNetworkError,
    ExchangeRateLimitError,
    to_kraken_symbol,
    from_kraken_symbol,
    SYMBOL_TO_KRAKEN,
)
from src.orders.base import OrderRequest, OrderFill


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_config() -> KrakenTestnetConfig:
    """Erstellt eine Test-Konfiguration."""
    return KrakenTestnetConfig(
        base_url="https://api.kraken.com",
        api_key_env_var="TEST_API_KEY",
        api_secret_env_var="TEST_API_SECRET",
        validate_only=True,
        timeout_seconds=10.0,
        max_retries=1,
        rate_limit_ms=0,  # Kein Rate-Limit in Tests
    )


@pytest.fixture
def mock_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setzt Mock-Credentials in Environment."""
    # Generiere ein gueltiges Base64-Secret fuer HMAC
    mock_secret = base64.b64encode(b"test_secret_key_for_testing").decode()
    monkeypatch.setenv("TEST_API_KEY", "test_api_key")
    monkeypatch.setenv("TEST_API_SECRET", mock_secret)


@pytest.fixture
def client_with_credentials(
    mock_config: KrakenTestnetConfig,
    mock_credentials: None,
) -> KrakenTestnetClient:
    """Erstellt einen Client mit Mock-Credentials."""
    return KrakenTestnetClient(mock_config)


@pytest.fixture
def client_without_credentials(
    mock_config: KrakenTestnetConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> KrakenTestnetClient:
    """Erstellt einen Client ohne Credentials."""
    monkeypatch.delenv("TEST_API_KEY", raising=False)
    monkeypatch.delenv("TEST_API_SECRET", raising=False)
    return KrakenTestnetClient(mock_config)


@pytest.fixture
def sample_order() -> OrderRequest:
    """Erstellt eine Test-Order."""
    return OrderRequest(
        symbol="BTC/EUR",
        side="buy",
        quantity=0.01,
        order_type="market",
        client_id="test_order_001",
    )


# =============================================================================
# Symbol Mapping Tests
# =============================================================================


class TestSymbolMapping:
    """Tests fuer Symbol-Konvertierung."""

    def test_to_kraken_symbol_known(self) -> None:
        """Test: Bekannte Symbole werden korrekt konvertiert."""
        assert to_kraken_symbol("BTC/EUR") == "XXBTZEUR"
        assert to_kraken_symbol("ETH/EUR") == "XETHZEUR"
        assert to_kraken_symbol("BTC/USD") == "XXBTZUSD"

    def test_to_kraken_symbol_unknown(self) -> None:
        """Test: Unbekannte Symbole werden einfach formatiert."""
        result = to_kraken_symbol("NEW/COIN")
        assert result == "NEWCOIN"

    def test_to_kraken_symbol_already_kraken_format(self) -> None:
        """Test: Symbole im Kraken-Format bleiben unveraendert."""
        result = to_kraken_symbol("XXBTZEUR")
        assert result == "XXBTZEUR"

    def test_from_kraken_symbol_known(self) -> None:
        """Test: Bekannte Kraken-Symbole werden korrekt konvertiert."""
        assert from_kraken_symbol("XXBTZEUR") == "BTC/EUR"
        assert from_kraken_symbol("XETHZEUR") == "ETH/EUR"

    def test_from_kraken_symbol_unknown(self) -> None:
        """Test: Unbekannte Symbole werden unveraendert zurueckgegeben."""
        result = from_kraken_symbol("UNKNOWNSYM")
        assert result == "UNKNOWNSYM"


# =============================================================================
# Client Initialization Tests
# =============================================================================


class TestClientInitialization:
    """Tests fuer Client-Initialisierung."""

    def test_init_with_credentials(
        self,
        client_with_credentials: KrakenTestnetClient,
    ) -> None:
        """Test: Client mit Credentials wird korrekt initialisiert."""
        assert client_with_credentials.has_credentials is True

    def test_init_without_credentials(
        self,
        client_without_credentials: KrakenTestnetClient,
    ) -> None:
        """Test: Client ohne Credentials wird korrekt initialisiert."""
        assert client_without_credentials.has_credentials is False

    def test_config_load_credentials(
        self,
        mock_config: KrakenTestnetConfig,
        mock_credentials: None,
    ) -> None:
        """Test: Credentials werden aus Environment geladen."""
        api_key, api_secret = mock_config.load_credentials()
        assert api_key == "test_api_key"
        assert api_secret is not None


# =============================================================================
# Order Payload Tests
# =============================================================================


class TestOrderPayloadMapping:
    """Tests fuer Order-Request zu API-Payload Mapping."""

    def test_market_order_payload(self, sample_order: OrderRequest) -> None:
        """Test: Market-Order-Payload wird korrekt aufgebaut."""
        # Simuliere die Payload-Erstellung (ohne tatsaechlichen API-Call)
        kraken_symbol = to_kraken_symbol(sample_order.symbol)

        expected_payload = {
            "pair": "XXBTZEUR",
            "type": "buy",
            "ordertype": "market",
            "volume": "0.01",
        }

        assert kraken_symbol == expected_payload["pair"]
        assert sample_order.side == expected_payload["type"]
        assert str(sample_order.quantity) == expected_payload["volume"]

    def test_limit_order_payload(self) -> None:
        """Test: Limit-Order-Payload enthält Preis."""
        order = OrderRequest(
            symbol="BTC/EUR",
            side="sell",
            quantity=0.05,
            order_type="limit",
            limit_price=50000.0,
        )

        kraken_symbol = to_kraken_symbol(order.symbol)

        assert kraken_symbol == "XXBTZEUR"
        assert order.side == "sell"
        assert order.order_type == "limit"
        assert order.limit_price == 50000.0


# =============================================================================
# API Response Mapping Tests
# =============================================================================


class TestResponseMapping:
    """Tests fuer API-Response zu Dataclass Mapping."""

    def test_order_response_mapping(self) -> None:
        """Test: Order-Response wird korrekt gemappt."""
        raw_response = {
            "txid": ["OABC123-DEFG-456789"],
            "descr": {
                "order": "buy 0.01000000 XBTEUR @ market",
            },
        }

        response = KrakenOrderResponse(
            txid=raw_response["txid"],
            descr=raw_response["descr"],
            validate_only=True,
            raw=raw_response,
        )

        assert response.txid == ["OABC123-DEFG-456789"]
        assert "buy" in response.descr["order"]
        assert response.validate_only is True

    def test_order_status_mapping(self) -> None:
        """Test: Order-Status wird korrekt gemappt."""
        raw_status = {
            "status": "closed",
            "vol": "0.01000000",
            "vol_exec": "0.01000000",
            "price": "50000.0",
            "fee": "1.30",
            "opentm": 1700000000.0,
        }

        status = KrakenOrderStatus(
            txid="OABC123",
            status=raw_status["status"],
            vol=float(raw_status["vol"]),
            vol_exec=float(raw_status["vol_exec"]),
            avg_price=float(raw_status["price"]),
            fee=float(raw_status["fee"]),
            timestamp=datetime.fromtimestamp(raw_status["opentm"], tz=timezone.utc),
            raw=raw_status,
        )

        assert status.status == "closed"
        assert status.vol == 0.01
        assert status.vol_exec == 0.01
        assert status.avg_price == 50000.0
        assert status.fee == 1.30

    def test_order_fill_from_status(self, sample_order: OrderRequest) -> None:
        """Test: OrderFill wird korrekt aus Status erstellt."""
        status = KrakenOrderStatus(
            txid="TEST123",
            status="closed",
            vol=0.01,
            vol_exec=0.01,
            avg_price=50000.0,
            fee=1.30,
            timestamp=datetime.now(timezone.utc),
            raw={},
        )

        # Simuliere fetch_order_as_fill Logik
        if status.status in ("closed", "filled") and status.vol_exec > 0:
            fill = OrderFill(
                symbol=sample_order.symbol,
                side=sample_order.side,
                quantity=status.vol_exec,
                price=status.avg_price or 0.0,
                timestamp=status.timestamp or datetime.now(timezone.utc),
                fee=status.fee,
                fee_currency="EUR",
            )

            assert fill.symbol == "BTC/EUR"
            assert fill.side == "buy"
            assert fill.quantity == 0.01
            assert fill.price == 50000.0
            assert fill.fee == 1.30


# =============================================================================
# Mocked API Call Tests
# =============================================================================


class TestMockedAPICalls:
    """Tests mit gemockten API-Calls."""

    @patch("src.exchange.kraken_testnet.requests.Session")
    def test_create_order_validate_only(
        self,
        mock_session_class: MagicMock,
        mock_config: KrakenTestnetConfig,
        mock_credentials: None,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Order im validate_only-Modus gibt VALIDATED zurueck."""
        # Mock-Response aufsetzen
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": [],
            "result": {
                "descr": {"order": "buy 0.01 XBTEUR @ market"},
            },
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        # Client erstellen
        mock_config.validate_only = True
        client = KrakenTestnetClient(mock_config)

        # Order senden
        result = client.create_order(sample_order)

        assert result == "VALIDATED"
        mock_session.post.assert_called_once()

    @patch("src.exchange.kraken_testnet.requests.Session")
    def test_create_order_real_execution(
        self,
        mock_session_class: MagicMock,
        mock_config: KrakenTestnetConfig,
        mock_credentials: None,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Echte Order gibt Transaction-ID zurueck."""
        # Mock-Response aufsetzen
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": [],
            "result": {
                "txid": ["OTEST-ABC-123456"],
                "descr": {"order": "buy 0.01 XBTEUR @ market"},
            },
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        # Client mit validate_only=False
        mock_config.validate_only = False
        client = KrakenTestnetClient(mock_config)

        result = client.create_order(sample_order)

        assert result == "OTEST-ABC-123456"

    @patch("src.exchange.kraken_testnet.requests.Session")
    def test_fetch_ticker_success(
        self,
        mock_session_class: MagicMock,
        mock_config: KrakenTestnetConfig,
        mock_credentials: None,
    ) -> None:
        """Test: Ticker wird korrekt abgerufen."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": [],
            "result": {
                "XXBTZEUR": {
                    "c": ["50000.00", "0.1"],  # last
                    "b": ["49990.00", "0.5"],  # bid
                    "a": ["50010.00", "0.3"],  # ask
                    "v": ["100.0", "500.0"],   # volume
                },
            },
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        client = KrakenTestnetClient(mock_config)
        ticker = client.fetch_ticker("BTC/EUR")

        assert ticker["symbol"] == "BTC/EUR"
        assert ticker["last"] == 50000.0
        assert ticker["bid"] == 49990.0
        assert ticker["ask"] == 50010.0


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests fuer Fehlerbehandlung."""

    @patch("src.exchange.kraken_testnet.requests.Session")
    def test_api_error_response(
        self,
        mock_session_class: MagicMock,
        mock_config: KrakenTestnetConfig,
        mock_credentials: None,
    ) -> None:
        """Test: API-Fehler wird korrekt behandelt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": ["EGeneral:Invalid arguments"],
            "result": {},
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        client = KrakenTestnetClient(mock_config)

        with pytest.raises(ExchangeAPIError) as exc_info:
            client.fetch_ticker("BTC/EUR")

        assert "EGeneral:Invalid arguments" in str(exc_info.value)

    @patch("src.exchange.kraken_testnet.requests.Session")
    def test_authentication_error(
        self,
        mock_session_class: MagicMock,
        mock_config: KrakenTestnetConfig,
        mock_credentials: None,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Auth-Fehler wird korrekt behandelt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": ["EAPI:Invalid key"],
            "result": {},
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        client = KrakenTestnetClient(mock_config)

        with pytest.raises(ExchangeAuthenticationError) as exc_info:
            client.create_order(sample_order)

        assert "Invalid key" in str(exc_info.value)

    def test_no_credentials_error(
        self,
        client_without_credentials: KrakenTestnetClient,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Fehler bei fehlenden Credentials."""
        with pytest.raises(ExchangeAuthenticationError) as exc_info:
            client_without_credentials.create_order(sample_order)

        assert "Credentials nicht gesetzt" in str(exc_info.value)

    @patch("src.exchange.kraken_testnet.requests.Session")
    def test_rate_limit_error(
        self,
        mock_session_class: MagicMock,
        mock_config: KrakenTestnetConfig,
        mock_credentials: None,
        sample_order: OrderRequest,
    ) -> None:
        """Test: Rate-Limit-Fehler wird korrekt behandelt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "error": ["EAPI:Rate limit exceeded"],
            "result": {},
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        client = KrakenTestnetClient(mock_config)

        with pytest.raises(ExchangeRateLimitError) as exc_info:
            client.create_order(sample_order)

        assert "Rate limit" in str(exc_info.value)


# =============================================================================
# Config Tests
# =============================================================================


class TestConfig:
    """Tests fuer KrakenTestnetConfig."""

    def test_default_config(self) -> None:
        """Test: Default-Config hat sichere Werte."""
        config = KrakenTestnetConfig()

        assert config.base_url == "https://api.kraken.com"
        assert config.validate_only is True  # Safety-Default
        assert config.timeout_seconds == 30.0
        assert config.max_retries == 3

    def test_custom_config(self) -> None:
        """Test: Custom-Config wird korrekt uebernommen."""
        config = KrakenTestnetConfig(
            base_url="https://custom.url",
            validate_only=False,
            timeout_seconds=60.0,
            max_retries=5,
            rate_limit_ms=2000,
        )

        assert config.base_url == "https://custom.url"
        assert config.validate_only is False
        assert config.timeout_seconds == 60.0
        assert config.max_retries == 5
        assert config.rate_limit_ms == 2000
