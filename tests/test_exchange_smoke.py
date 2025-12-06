"""
Peak_Trade Exchange Layer Smoke Tests
=====================================

Smoke- und Integration-Tests für den Exchange-Layer.

WICHTIG: Diese Datei enthält zwei Kategorien von Tests:

1. OFFLINE-TESTS (Standard)
   - Laufen OHNE Netzwerkzugriff
   - Testen Dataclasses, Konstruktoren, Protokolle
   - Werden bei jedem `pytest`-Lauf ausgeführt
   - Keine API-Keys erforderlich

2. INTEGRATION-TESTS (Opt-in)
   - Machen ECHTE HTTP-Requests zur Exchange (Kraken)
   - Standardmäßig GESKIPPT
   - Nur für manuelles Testen der Exchange-Anbindung gedacht
   - NICHT Teil der normalen CI/Dev-Suite

INTEGRATION-TESTS AKTIVIEREN:
-----------------------------
Um die Integration-Tests auszuführen, setze die Umgebungsvariable:

    export PEAK_TRADE_EXCHANGE_TESTS=1
    pytest tests/test_exchange_smoke.py -v

Oder in einer Zeile:

    PEAK_TRADE_EXCHANGE_TESTS=1 pytest tests/test_exchange_smoke.py -v

HINWEISE zu Integration-Tests:
- Erfordern Internetzugang (zu api.kraken.com)
- Für Public-API-Tests (Ticker, OHLCV, Markets) sind KEINE API-Keys nötig
- Für authentifizierte Tests (Balance, Orders) müssten API-Keys gesetzt sein
- Diese Tests sind bewusst NICHT Teil der CI-Pipeline

Phase 38: Ergänzt um TradingExchangeClient-Offline-Tests (DummyExchangeClient).
"""

import os
import pytest
import pandas as pd

from src.exchange.base import Ticker, Balance, ExchangeClient, TradingExchangeClient
from src.exchange.ccxt_client import CcxtExchangeClient
from src.exchange.dummy_client import DummyExchangeClient
from src.exchange import build_exchange_client_from_config, build_trading_client_from_config
from src.core.peak_config import load_config


# ============================================================================
# OFFLINE-TESTS (kein Netzwerkzugriff)
# ============================================================================


def test_ticker_dataclass():
    """Test: Ticker-Dataclass funktioniert korrekt."""
    ticker = Ticker(
        symbol="BTC/EUR",
        last=50000.0,
        bid=49990.0,
        ask=50010.0,
        timestamp=1704067200000,
    )

    assert ticker.symbol == "BTC/EUR"
    assert ticker.last == 50000.0
    assert ticker.bid == 49990.0
    assert ticker.ask == 50010.0

    # Spread-Berechnung
    spread = ticker.spread()
    assert spread is not None
    assert spread > 0

    spread_bps = ticker.spread_bps()
    assert spread_bps is not None
    assert spread_bps > 0


def test_ticker_spread_none_when_missing():
    """Test: Spread ist None wenn bid/ask fehlen."""
    ticker = Ticker(symbol="BTC/EUR", last=50000.0)

    assert ticker.spread() is None
    assert ticker.spread_bps() is None


def test_balance_dataclass():
    """Test: Balance-Dataclass funktioniert korrekt."""
    balance = Balance(
        free={"BTC": 1.5, "EUR": 10000.0},
        used={"BTC": 0.5, "EUR": 0.0},
        total={"BTC": 2.0, "EUR": 10000.0},
    )

    assert balance.free["BTC"] == 1.5
    assert balance.used["BTC"] == 0.5
    assert balance.total["BTC"] == 2.0

    # get_asset Helper
    btc = balance.get_asset("BTC")
    assert btc["free"] == 1.5
    assert btc["used"] == 0.5
    assert btc["total"] == 2.0

    # non_zero_assets
    assets = balance.non_zero_assets()
    assert "BTC" in assets
    assert "EUR" in assets


def test_balance_get_asset_missing():
    """Test: get_asset gibt 0.0 für unbekannte Assets zurück."""
    balance = Balance()

    unknown = balance.get_asset("UNKNOWN")
    assert unknown["free"] == 0.0
    assert unknown["used"] == 0.0
    assert unknown["total"] == 0.0


def test_ccxt_client_construction():
    """Test: CcxtExchangeClient kann mit gültiger Exchange-ID erstellt werden."""
    client = CcxtExchangeClient("kraken")

    assert client.get_name() == "kraken"
    assert repr(client) == "<CcxtExchangeClient(kraken, no API-Key)>"


def test_ccxt_client_construction_with_credentials():
    """Test: CcxtExchangeClient mit API-Key."""
    client = CcxtExchangeClient(
        "kraken",
        api_key="test_key",
        secret="test_secret",
    )

    assert client.get_name() == "kraken"
    assert "with API-Key" in repr(client)


def test_ccxt_client_invalid_exchange():
    """Test: Ungültige Exchange-ID wirft ValueError."""
    with pytest.raises(ValueError, match="Unknown ccxt exchange id"):
        CcxtExchangeClient("invalid_exchange_xyz")


def test_ccxt_client_available_timeframes():
    """Test: Timeframes können abgerufen werden (offline)."""
    client = CcxtExchangeClient("kraken")

    timeframes = client.get_available_timeframes()
    assert isinstance(timeframes, list)
    # Kraken unterstützt mehrere Timeframes
    assert len(timeframes) > 0


def test_ccxt_client_implements_protocol():
    """Test: CcxtExchangeClient implementiert ExchangeClient-Protokoll."""
    client = CcxtExchangeClient("kraken")

    # Protocol-Check
    assert isinstance(client, ExchangeClient)


def test_build_exchange_client_from_config(tmp_path):
    """Test: Factory-Funktion erstellt Client aus Config."""
    config_text = """
[exchange]
id = "binance"
sandbox = true
enable_rate_limit = true

[exchange.credentials]
api_key = ""
secret = ""
"""
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(config_text, encoding="utf-8")

    cfg = load_config(cfg_path)
    client = build_exchange_client_from_config(cfg)

    assert client.get_name() == "binance"


def test_build_exchange_client_defaults(tmp_path):
    """Test: Factory verwendet Defaults wenn Config minimal ist."""
    config_text = """
[general]
base_currency = "EUR"
"""
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(config_text, encoding="utf-8")

    cfg = load_config(cfg_path)
    client = build_exchange_client_from_config(cfg)

    # Default ist "kraken"
    assert client.get_name() == "kraken"


# ============================================================================
# PHASE 38: TRADING EXCHANGE CLIENT OFFLINE-TESTS
# ============================================================================
# Diese Tests prüfen das TradingExchangeClient-Protokoll und den
# DummyExchangeClient OHNE Netzwerkzugriff.
# ============================================================================


def test_trading_client_protocol_compliance():
    """Test: DummyExchangeClient implementiert TradingExchangeClient-Protokoll."""
    client = DummyExchangeClient(simulated_prices={"BTC/EUR": 50000.0})

    # Protocol-Check
    assert isinstance(client, TradingExchangeClient)

    # Alle erforderlichen Methoden vorhanden
    assert hasattr(client, "get_name")
    assert hasattr(client, "place_order")
    assert hasattr(client, "cancel_order")
    assert hasattr(client, "get_order_status")


def test_trading_client_factory_from_config():
    """Test: build_trading_client_from_config() erstellt funktionierenden Client."""
    cfg = load_config("config/config.toml")
    client = build_trading_client_from_config(cfg)

    # Sollte DummyExchangeClient sein (default_type = "dummy")
    assert isinstance(client, TradingExchangeClient)
    assert client.get_name() == "dummy"

    # Client sollte Orders platzieren können
    order_id = client.place_order("BTC/EUR", "buy", 0.01, "market")
    assert order_id is not None
    assert order_id.startswith("DUMMY-")


def test_trading_client_order_execution():
    """Test: DummyExchangeClient führt Orders korrekt aus (Offline)."""
    client = DummyExchangeClient(
        simulated_prices={"BTC/EUR": 50000.0, "ETH/EUR": 3000.0},
        fee_bps=10.0,
    )

    # Market-Order platzieren
    order_id = client.place_order(
        symbol="BTC/EUR",
        side="buy",
        quantity=0.1,
        order_type="market",
    )

    # Status abfragen
    from src.exchange.base import ExchangeOrderStatus

    status = client.get_order_status(order_id)
    assert status.status == ExchangeOrderStatus.FILLED
    assert status.filled_qty == 0.1
    assert status.avg_price is not None
    assert status.fee is not None


# ============================================================================
# INTEGRATION-TESTS (erfordern Netzwerk & explizites Opt-in)
# ============================================================================
#
# ACHTUNG: Die folgenden Tests machen ECHTE HTTP-Requests zur Kraken-API!
#
# Diese Tests sind standardmäßig DEAKTIVIERT und werden nur ausgeführt, wenn
# die Environment-Variable PEAK_TRADE_EXCHANGE_TESTS gesetzt ist.
#
# AKTIVIERUNG:
#     export PEAK_TRADE_EXCHANGE_TESTS=1
#     pytest tests/test_exchange_smoke.py::test_integration_fetch_ticker -v
#
# ODER für alle Integration-Tests:
#     PEAK_TRADE_EXCHANGE_TESTS=1 pytest tests/test_exchange_smoke.py -v -k integration
#
# VORAUSSETZUNGEN:
#     - Internetzugang (zu api.kraken.com)
#     - Für Public-API-Tests: Keine API-Keys erforderlich
#     - Für authentifizierte Tests: KRAKEN_API_KEY und KRAKEN_API_SECRET setzen
#
# WICHTIG:
#     - Diese Tests sind NICHT Teil der normalen CI/Dev-Suite
#     - Sie dienen nur zum manuellen Testen der Exchange-Anbindung
#     - Sie können fehlschlagen, wenn die Exchange nicht erreichbar ist
#
# ============================================================================

EXCHANGE_TESTS_ENABLED = os.environ.get("PEAK_TRADE_EXCHANGE_TESTS", "").lower() in (
    "1",
    "true",
    "yes",
)


@pytest.mark.skipif(
    not EXCHANGE_TESTS_ENABLED,
    reason="Exchange-Tests erfordern PEAK_TRADE_EXCHANGE_TESTS=1",
)
def test_integration_fetch_ticker():
    """Integration-Test: Ticker von Kraken abrufen."""
    client = CcxtExchangeClient("kraken")

    ticker = client.fetch_ticker("BTC/EUR")

    assert ticker.symbol.startswith("BTC")
    assert ticker.last is not None
    assert ticker.last > 0


@pytest.mark.skipif(
    not EXCHANGE_TESTS_ENABLED,
    reason="Exchange-Tests erfordern PEAK_TRADE_EXCHANGE_TESTS=1",
)
def test_integration_fetch_ohlcv():
    """Integration-Test: OHLCV-Daten von Kraken abrufen."""
    client = CcxtExchangeClient("kraken")

    df = client.fetch_ohlcv("BTC/EUR", timeframe="1h", limit=10)

    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "open" in df.columns
    assert "high" in df.columns
    assert "low" in df.columns
    assert "close" in df.columns
    assert "volume" in df.columns

    # Index ist DatetimeIndex
    assert isinstance(df.index, pd.DatetimeIndex)


@pytest.mark.skipif(
    not EXCHANGE_TESTS_ENABLED,
    reason="Exchange-Tests erfordern PEAK_TRADE_EXCHANGE_TESTS=1",
)
def test_integration_fetch_markets():
    """Integration-Test: Märkte von Kraken abrufen."""
    client = CcxtExchangeClient("kraken")

    markets = client.fetch_markets()

    assert isinstance(markets, list)
    assert len(markets) > 0

    # Mindestens ein BTC-Markt sollte existieren
    btc_markets = [m for m in markets if m.get("base") == "BTC"]
    assert len(btc_markets) > 0


@pytest.mark.skipif(
    not EXCHANGE_TESTS_ENABLED,
    reason="Exchange-Tests erfordern PEAK_TRADE_EXCHANGE_TESTS=1",
)
def test_integration_from_config():
    """Integration-Test: Client aus config.toml funktioniert."""
    cfg = load_config()
    client = build_exchange_client_from_config(cfg)

    # Sollte funktionieren, auch ohne API-Key (nur Public-Daten)
    ticker = client.fetch_ticker("BTC/EUR")
    assert ticker.last is not None
