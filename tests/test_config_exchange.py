# tests/test_config_exchange.py
"""
Peak_Trade: Tests für Exchange-Config (Phase 38)
================================================

Tests für:
1. Exchange-Config wird korrekt aus TOML geladen
2. default_type hat den erwarteten Wert
3. build_trading_client_from_config() gibt richtigen Client zurück
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.peak_config import PeakConfig, load_config
from src.exchange import (
    TradingExchangeClient,
    build_trading_client_from_config,
)
from src.exchange.dummy_client import DummyExchangeClient

# =============================================================================
# PeakConfig-basierte Tests
# =============================================================================


class TestExchangeConfigLoading:
    """Tests für Exchange-Config-Loading via PeakConfig."""

    def test_load_default_type_from_config(self) -> None:
        """Test: default_type wird aus config.toml geladen."""
        cfg = load_config("config/config.toml")

        default_type = cfg.get("exchange.default_type")
        assert default_type is not None
        assert default_type == "dummy"

    def test_load_default_type_from_test_config(self) -> None:
        """Test: default_type wird aus config.test.toml geladen."""
        cfg = load_config("config/config.test.toml")

        default_type = cfg.get("exchange.default_type")
        assert default_type is not None
        assert default_type == "dummy"

    def test_load_dummy_config_values(self) -> None:
        """Test: Dummy-Config-Werte werden korrekt geladen."""
        cfg = load_config("config/config.toml")

        btc_price = cfg.get("exchange.dummy.btc_eur_price")
        eth_price = cfg.get("exchange.dummy.eth_eur_price")
        fee_bps = cfg.get("exchange.dummy.fee_bps")

        assert btc_price == 50000.0
        assert eth_price == 3000.0
        assert fee_bps == 10.0

    def test_default_type_fallback(self) -> None:
        """Test: Ohne exchange-Block wird 'dummy' als Default verwendet."""
        # Simuliere Config ohne [exchange]-Block
        minimal_cfg = PeakConfig(raw={"general": {"base_currency": "EUR"}})

        default_type = minimal_cfg.get("exchange.default_type", "dummy")
        assert default_type == "dummy"


# =============================================================================
# Factory-Funktion Tests
# =============================================================================


class TestBuildTradingClientFromConfig:
    """Tests für build_trading_client_from_config Factory."""

    def test_build_dummy_client_from_config(self) -> None:
        """Test: Factory erstellt DummyExchangeClient bei default_type='dummy'."""
        cfg = load_config("config/config.toml")

        client = build_trading_client_from_config(cfg)

        assert isinstance(client, DummyExchangeClient)
        assert isinstance(client, TradingExchangeClient)
        assert client.get_name() == "dummy"

    def test_build_client_uses_config_prices(self) -> None:
        """Test: Factory übergibt Preise aus Config an DummyClient."""
        cfg = load_config("config/config.toml")

        client = build_trading_client_from_config(cfg)

        # Preise sollten aus Config kommen
        btc_price = client.get_price("BTC/EUR")
        eth_price = client.get_price("ETH/EUR")

        assert btc_price == 50000.0
        assert eth_price == 3000.0

    def test_build_client_unknown_type_raises(self, tmp_path: Path) -> None:
        """Test: Unbekannter default_type wirft ValueError."""
        config_text = """
[exchange]
default_type = "unknown_exchange"
"""
        cfg_path = tmp_path / "config.toml"
        cfg_path.write_text(config_text, encoding="utf-8")

        cfg = load_config(cfg_path)

        with pytest.raises(ValueError, match="Unbekannter exchange.default_type"):
            build_trading_client_from_config(cfg)

    def test_build_client_minimal_config(self, tmp_path: Path) -> None:
        """Test: Minimale Config (ohne [exchange]) nutzt Defaults."""
        config_text = """
[general]
base_currency = "EUR"
"""
        cfg_path = tmp_path / "config.toml"
        cfg_path.write_text(config_text, encoding="utf-8")

        cfg = load_config(cfg_path)

        # Sollte DummyClient mit Default-Preisen erstellen
        client = build_trading_client_from_config(cfg)

        assert isinstance(client, DummyExchangeClient)
        assert client.get_name() == "dummy"
        # Default-Preise sollten gesetzt sein
        assert client.get_price("BTC/EUR") == 50000.0


# =============================================================================
# Pydantic-Config Tests
# =============================================================================


class TestPydanticExchangeConfig:
    """Tests für Pydantic ExchangeConfig."""

    def test_exchange_config_in_settings(self) -> None:
        """Test: Settings enthält exchange-Feld."""
        from src.core.config_pydantic import ExchangeConfig, Settings

        # Erstelle Settings mit Minimal-Daten
        settings = Settings(
            backtest={"initial_cash": 10000},
            risk={},
            data={},
            live={},
            validation={},
        )

        assert hasattr(settings, "exchange")
        assert isinstance(settings.exchange, ExchangeConfig)
        assert settings.exchange.default_type == "dummy"

    def test_exchange_config_default_values(self) -> None:
        """Test: ExchangeConfig hat korrekte Defaults."""
        from src.core.config_pydantic import ExchangeConfig

        config = ExchangeConfig()

        assert config.default_type == "dummy"
        assert config.dummy.btc_eur_price == 50000.0
        assert config.dummy.fee_bps == 10.0

    def test_exchange_config_custom_values(self) -> None:
        """Test: ExchangeConfig akzeptiert Custom-Werte."""
        from src.core.config_pydantic import ExchangeConfig, ExchangeDummyConfig

        config = ExchangeConfig(
            default_type="kraken_testnet",
            dummy=ExchangeDummyConfig(btc_eur_price=60000.0),
        )

        assert config.default_type == "kraken_testnet"
        assert config.dummy.btc_eur_price == 60000.0


# =============================================================================
# Integration Tests
# =============================================================================


class TestConfigIntegration:
    """Integration-Tests für Config + Client-Erstellung."""

    def test_full_flow_config_to_client(self) -> None:
        """Test: Kompletter Flow von Config-Loading bis Client-Nutzung."""
        # 1. Config laden
        cfg = load_config("config/config.toml")

        # 2. Client erstellen
        client = build_trading_client_from_config(cfg)

        # 3. Client nutzen
        order_id = client.place_order("BTC/EUR", "buy", 0.01, "market")

        # 4. Ergebnis prüfen
        status = client.get_order_status(order_id)
        assert status.status.value == "filled"
        assert status.filled_qty == 0.01

    def test_test_config_creates_working_client(self) -> None:
        """Test: Test-Config erstellt funktionierenden Client."""
        cfg = load_config("config/config.test.toml")
        client = build_trading_client_from_config(cfg)

        # Sollte BTC/EUR handeln können
        order_id = client.place_order("BTC/EUR", "sell", 0.5, "market")
        status = client.get_order_status(order_id)

        assert status.status.value == "filled"




