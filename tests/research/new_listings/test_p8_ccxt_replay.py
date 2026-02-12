# tests/research/new_listings/test_p8_ccxt_replay.py
"""
P8: CCXT read-only collector + offline replay.
- Unit tests: mock ccxt (no network), replay from fixtures.
- Optional integration test: @pytest.mark.network for real fetch.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.research.new_listings.collectors.base import CollectorContext
from src.research.new_listings.collectors.ccxt_ticker import CcxtTickerCollector, _get_ccxt_config
from src.research.new_listings.collectors.replay import ReplayCollector, _get_replay_config
from src.research.new_listings.runner import build_collectors


def test_replay_collector_contract(tmp_path: Path) -> None:
    """ReplayCollector reads JSON fixtures and emits RawEvents (offline, no network)."""
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "source": "replay",
                    "venue_type": "ccxt",
                    "observed_at": "2026-02-09T12:00:00Z",
                    "payload": {"exchange": "kraken", "symbol": "BTC/EUR", "ticker": {"last": 1.0}},
                }
            ]
        ),
        encoding="utf-8",
    )
    cfg = {"sources": {"replay": {"dir": str(tmp_path), "enabled": True}}}
    c = ReplayCollector(cfg)
    ctx = CollectorContext(run_id="nl_test", config_hash="0" * 64)
    out = c.collect(ctx)
    assert len(out) == 1
    e = out[0]
    assert e.source == "replay"
    assert e.venue_type == "ccxt"
    assert e.observed_at == "2026-02-09T12:00:00Z"
    assert e.payload.get("symbol") == "BTC/EUR"
    assert e.payload.get("ticker", {}).get("last") == 1.0


def test_replay_collector_disabled_returns_empty(tmp_path: Path) -> None:
    cfg = {"sources": {"replay": {"dir": str(tmp_path), "enabled": False}}}
    c = ReplayCollector(cfg)
    ctx = CollectorContext(run_id="nl_test", config_hash="0" * 64)
    assert list(c.collect(ctx)) == []


def test_replay_collector_empty_dir_returns_empty(tmp_path: Path) -> None:
    cfg = {"sources": {"replay": {"dir": str(tmp_path), "enabled": True}}}
    c = ReplayCollector(cfg)
    ctx = CollectorContext(run_id="nl_test", config_hash="0" * 64)
    assert list(c.collect(ctx)) == []


def test_ccxt_ticker_collector_contract_mock() -> None:
    """CcxtTickerCollector with mocked ccxt (no network): emits RawEvents from fetch_tickers."""
    mock_exchange = MagicMock()
    mock_exchange.fetch_markets.return_value = [{"id": "btceur", "symbol": "BTC/EUR"}]
    mock_exchange.fetch_tickers.return_value = {
        "BTC/EUR": {"symbol": "BTC/EUR", "last": 100.0, "bid": 99.0, "ask": 101.0},
    }
    mock_klass = MagicMock(return_value=mock_exchange)
    mock_ccxt = MagicMock()
    mock_ccxt.kraken = mock_klass
    mock_ccxt.NetworkError = Exception
    mock_ccxt.ExchangeError = Exception

    cfg = {
        "sources": {
            "ccxt": {
                "exchange": "kraken",
                "max_markets": 10,
                "rate_limit_ms": 1200,
                "enabled": True,
            }
        }
    }
    with patch.dict(sys.modules, {"ccxt": mock_ccxt}):
        collector = CcxtTickerCollector(cfg)
        ctx = CollectorContext(run_id="nl_test", config_hash="0" * 64)
        events = list(collector.collect(ctx))

    assert len(events) >= 1
    e = events[0]
    assert e.source == "ccxt_ticker"
    assert e.venue_type == "ccxt"
    assert "observed_at" in e.payload
    assert e.payload.get("exchange") == "kraken"
    assert e.payload.get("symbol") == "BTC/EUR"
    mock_exchange.fetch_markets.assert_called_once()
    mock_exchange.fetch_tickers.assert_called_once()


def test_get_ccxt_config_defaults() -> None:
    assert _get_ccxt_config({})["exchange"] == "kraken"
    assert _get_ccxt_config({})["enabled"] is True
    assert _get_ccxt_config({})["max_markets"] == 50
    assert (
        _get_ccxt_config({"sources": {"ccxt": {"exchange": "binance", "max_markets": 5}}})[
            "exchange"
        ]
        == "binance"
    )
    assert (
        _get_ccxt_config({"sources": {"ccxt": {"exchange": "binance", "max_markets": 5}}})[
            "max_markets"
        ]
        == 5
    )


def test_get_replay_config_defaults() -> None:
    default_dir = Path("out/research/new_listings/replay")
    assert _get_replay_config({}, default_dir)["enabled"] is True
    assert _get_replay_config({"sources": {"replay": {"dir": "/tmp/replay"}}}, default_dir)[
        "dir"
    ] == Path("/tmp/replay")


def test_build_collectors_ccxt_and_replay() -> None:
    cfg = {
        "collectors": ["manual_seed", "replay"],
        "sources": {"ccxt": {"enabled": False}, "replay": {"enabled": True}},
    }
    collectors = build_collectors(cfg["collectors"], cfg)
    names = [c.name for c in collectors]
    assert "manual_seed" in names
    assert "replay" in names
    assert "ccxt_ticker" not in names  # ccxt not in list

    cfg2 = {
        "collectors": ["manual_seed", "ccxt_ticker", "replay"],
        "sources": {"ccxt": {"enabled": False}, "replay": {"enabled": True}},
    }
    collectors2 = build_collectors(cfg2["collectors"], cfg2)
    names2 = [c.name for c in collectors2]
    assert "manual_seed" in names2
    assert "replay" in names2
    assert "ccxt_ticker" not in names2  # skipped because sources.ccxt.enabled is False
    assert len(collectors2) == 2


@pytest.mark.network
def test_ccxt_ticker_collector_integration_real_fetch() -> None:
    """Optional: real CCXT public fetch (marked network). Run with pytest -m network to execute."""
    pytest.importorskip("ccxt")
    cfg = {
        "sources": {
            "ccxt": {
                "exchange": "kraken",
                "max_markets": 3,
                "rate_limit_ms": 1200,
                "enabled": True,
            }
        }
    }
    collector = CcxtTickerCollector(cfg)
    ctx = CollectorContext(run_id="nl_net", config_hash="0" * 64)
    events = list(collector.collect(ctx))
    assert len(events) >= 1
    assert all(e.source == "ccxt_ticker" and e.venue_type == "ccxt" for e in events)
