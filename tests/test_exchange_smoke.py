"""
Peak_Trade Exchange Layer Smoke Tests
=====================================

Offline smoke tests for the exchange layer.

1. Dataclasses, dummy trading client, and protocol checks (no venue).
2. Operative CCXT constructor/factory success using existing OKX names.
3. Fail-closed rejection of foreign / undeclared / missing venue ids.

No network. No Live. No Testnet wire. Dummy is simulation, not a venue.
"""

import pytest

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


def test_ccxt_client_construction_operative_okx():
    """Operative constructor success uses the existing OKX ccxt class id."""
    pytest.importorskip("ccxt", reason="Optional dependency missing: ccxt")
    client = CcxtExchangeClient("okx")

    assert client.get_name() == "okx"
    assert "okx" in repr(client)


def test_ccxt_client_construction_with_credentials_operative_okx():
    """Operative constructor still accepts credential kwargs for the OKX id."""
    pytest.importorskip("ccxt", reason="Optional dependency missing: ccxt")
    client = CcxtExchangeClient(
        "okx",
        api_key="test_key",
        secret="test_secret",
    )

    assert client.get_name() == "okx"
    assert "with API-Key" in repr(client)


def test_ccxt_client_foreign_venue_rejected():
    """A foreign venue id is not a second productive ccxt venue."""
    with pytest.raises(ValueError, match="noncanonical_venue_rejected"):
        CcxtExchangeClient("foreign_venue")


def test_ccxt_client_invalid_exchange():
    """Undeclared ccxt ids fail closed at the operative venue boundary."""
    with pytest.raises(ValueError, match="noncanonical_venue_rejected"):
        CcxtExchangeClient("undeclared_venue")


def test_ccxt_client_available_timeframes_operative_okx():
    """Timeframe listing is exercised through the gated OKX constructor."""
    pytest.importorskip("ccxt", reason="Optional dependency missing: ccxt")
    client = CcxtExchangeClient("okx")

    timeframes = client.get_available_timeframes()
    assert isinstance(timeframes, list)
    assert len(timeframes) > 0


def test_ccxt_client_implements_protocol_operative_okx():
    """The gated OKX ccxt client satisfies the read-only ExchangeClient protocol."""
    pytest.importorskip("ccxt", reason="Optional dependency missing: ccxt")
    client = CcxtExchangeClient("okx")

    assert isinstance(client, ExchangeClient)


def test_build_exchange_client_from_config_foreign_venue_rejected(tmp_path):
    """Alternate/foreign factory ids are rejected; they are not remapped to OKX."""
    config_text = """
[exchange]
id = "foreign_venue"
sandbox = true
"""
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(config_text, encoding="utf-8")

    cfg = load_config(cfg_path)
    with pytest.raises(ValueError, match="noncanonical_venue_rejected"):
        build_exchange_client_from_config(cfg)


def test_build_exchange_client_from_config_okx_europe_eea(tmp_path):
    """Factory success path maps the existing Peak_Trade OKX name onto ccxt okx."""
    pytest.importorskip("ccxt", reason="Optional dependency missing: ccxt")
    config_text = """
[exchange]
id = "okx_europe_eea"
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

    assert client.get_name() == "okx"


def test_build_exchange_client_noncanonical_rejected(tmp_path):
    """Factory rejects a noncanonical venue id."""
    config_text = """
[exchange]
id = "noncanonical_venue"
sandbox = true
"""
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(config_text, encoding="utf-8")

    cfg = load_config(cfg_path)
    with pytest.raises(ValueError, match="noncanonical_venue_rejected"):
        build_exchange_client_from_config(cfg)


def test_build_exchange_client_missing_exchange_id_fail_closed(tmp_path):
    """Test: Factory fail-closed, wenn exchange.id fehlt (kein Venue-Fallback)."""
    config_text = """
[general]
base_currency = "EUR"
"""
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(config_text, encoding="utf-8")

    cfg = load_config(cfg_path)
    with pytest.raises(ValueError, match="exchange.id is required"):
        build_exchange_client_from_config(cfg)


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


def test_integration_noncanonical_ccxt_id_rejected():
    """Former public-HTTP integration path is not a current operative venue."""
    with pytest.raises(ValueError, match="noncanonical_venue_rejected"):
        CcxtExchangeClient("example_venue")


def test_integration_from_config_requires_explicit_exchange_id():
    """Canonical config has no exchange.id; factory must fail closed (no implicit venue)."""
    cfg = load_config()
    with pytest.raises(ValueError, match="exchange.id is required"):
        build_exchange_client_from_config(cfg)
