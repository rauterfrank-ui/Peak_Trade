# tests/test_kraken_live_client.py
"""
Peak_Trade: Tests für KrakenLiveClient (Option A Slice 5)
=========================================================

Tests für:
- TradingExchangeClient Protocol-Konformität
- Factory-Integration (build_trading_client_from_config)
- Credential- und Validierungs-Checks

WICHTIG: Keine echten API-Calls! Tests nutzen Mocks oder fehlende Credentials.
"""

from __future__ import annotations

import pytest

from src.exchange.base import TradingExchangeClient, ExchangeOrderStatus
from src.exchange.kraken_live import (
    KrakenLiveClient,
    KrakenLiveConfig,
    create_kraken_live_client_from_config,
)
from src.exchange.kraken_testnet import ExchangeAuthenticationError


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def kraken_live_config() -> KrakenLiveConfig:
    """KrakenLiveConfig ohne gesetzte Credentials (für Unit-Tests)."""
    return KrakenLiveConfig(
        base_url="https://api.kraken.com",
        api_key_env_var="KRAKEN_API_KEY",
        api_secret_env_var="KRAKEN_API_SECRET",
    )


@pytest.fixture
def kraken_live_client(kraken_live_config: KrakenLiveConfig) -> KrakenLiveClient:
    """KrakenLiveClient-Instanz (ohne Credentials)."""
    return KrakenLiveClient(kraken_live_config)


# =============================================================================
# Protocol Conformance
# =============================================================================


class TestProtocolConformance:
    """Tests für TradingExchangeClient Protocol-Konformität."""

    def test_implements_protocol(self, kraken_live_client: KrakenLiveClient) -> None:
        """KrakenLiveClient implementiert TradingExchangeClient."""
        assert isinstance(kraken_live_client, TradingExchangeClient)

    def test_has_required_methods(self, kraken_live_client: KrakenLiveClient) -> None:
        """Alle Protocol-Methoden sind vorhanden."""
        assert hasattr(kraken_live_client, "get_name")
        assert hasattr(kraken_live_client, "place_order")
        assert hasattr(kraken_live_client, "cancel_order")
        assert hasattr(kraken_live_client, "get_order_status")
        assert callable(kraken_live_client.get_name)
        assert callable(kraken_live_client.place_order)
        assert callable(kraken_live_client.cancel_order)
        assert callable(kraken_live_client.get_order_status)


# =============================================================================
# Basic Behaviour
# =============================================================================


class TestBasicBehaviour:
    """Basis-Tests für KrakenLiveClient."""

    def test_get_name(self, kraken_live_client: KrakenLiveClient) -> None:
        """get_name gibt 'kraken_live' zurück."""
        assert kraken_live_client.get_name() == "kraken_live"

    def test_has_credentials_false_without_env(self, kraken_live_client: KrakenLiveClient) -> None:
        """Ohne ENV-Variablen ist has_credentials False."""
        assert kraken_live_client.has_credentials is False

    def test_place_order_requires_credentials(self, kraken_live_client: KrakenLiveClient) -> None:
        """place_order wirft ExchangeAuthenticationError ohne Credentials."""
        with pytest.raises(ExchangeAuthenticationError) as exc_info:
            kraken_live_client.place_order("BTC/EUR", "buy", 0.01, "market")
        assert "KRAKEN_API_KEY" in str(exc_info.value)

    def test_place_order_validates_quantity(self, kraken_live_client: KrakenLiveClient) -> None:
        """place_order wirft ValueError bei quantity <= 0."""
        with pytest.raises(ValueError, match="quantity"):
            kraken_live_client.place_order("BTC/EUR", "buy", 0, "market")
        with pytest.raises(ValueError, match="quantity"):
            kraken_live_client.place_order("BTC/EUR", "buy", -0.01, "market")

    def test_place_order_limit_requires_price(self, kraken_live_client: KrakenLiveClient) -> None:
        """place_order mit order_type=limit erfordert limit_price."""
        with pytest.raises(ValueError, match="limit_price"):
            kraken_live_client.place_order("BTC/EUR", "buy", 0.01, "limit")


# =============================================================================
# Factory
# =============================================================================


class TestFactory:
    """Tests für create_kraken_live_client_from_config."""

    def test_factory_creates_client(self) -> None:
        """Factory erstellt KrakenLiveClient aus Config."""
        cfg: dict = {
            "exchange.kraken_live.base_url": "https://api.kraken.com",
            "exchange.kraken_live.api_key_env_var": "KRAKEN_API_KEY",
            "exchange.kraken_live.api_secret_env_var": "KRAKEN_API_SECRET",
        }

        class MockConfig:
            def get(self, key: str, default: object = None) -> object:
                return cfg.get(key, default)

        client = create_kraken_live_client_from_config(MockConfig())
        assert isinstance(client, KrakenLiveClient)
        assert client.get_name() == "kraken_live"

    def test_build_trading_client_kraken_live(self) -> None:
        """build_trading_client_from_config mit default_type=kraken_live."""
        from src.exchange import build_trading_client_from_config

        cfg: dict = {
            "exchange.default_type": "kraken_live",
            "exchange.kraken_live.base_url": "https://api.kraken.com",
            "exchange.kraken_live.api_key_env_var": "KRAKEN_API_KEY",
            "exchange.kraken_live.api_secret_env_var": "KRAKEN_API_SECRET",
        }

        class MockConfig:
            def get(self, key: str, default: object = None) -> object:
                return cfg.get(key, default)

        client = build_trading_client_from_config(MockConfig())
        assert isinstance(client, KrakenLiveClient)
        assert client.get_name() == "kraken_live"
