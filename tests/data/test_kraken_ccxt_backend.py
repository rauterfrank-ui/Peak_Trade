from __future__ import annotations

import importlib
import sys
import types
from typing import Optional

import pytest


class FakeExchange:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.load_markets_called = False

    def load_markets(self):
        self.load_markets_called = True
        return {"BTC/EUR": {}}

    def fetch_ohlcv(self, symbol: str, timeframe: str, since=None, limit=None):
        assert symbol == "BTC/EUR"
        assert timeframe == "1h"
        assert since == 1700000000000
        assert limit == 2
        # Deterministic OHLCV rows: [ts, o, h, l, c, v]
        return [
            [1700000000000, "1.0", 2, 0.5, "1.5", "10"],
            [1700003600000, 1.1, "2.1", "0.6", 1.6, 11],
        ]


def test_fetch_ohlcv_canonical_mapping(monkeypatch):
    # Provide a fake ccxt module so backend remains deterministic and offline.
    fake_ccxt = types.ModuleType("ccxt")

    def kraken(cfg: dict):
        return FakeExchange(cfg)

    setattr(fake_ccxt, "kraken", kraken)
    monkeypatch.setitem(sys.modules, "ccxt", fake_ccxt)

    mod = importlib.import_module("src.data.providers.kraken_ccxt_backend")
    KrakenCcxtBackend = getattr(mod, "KrakenCcxtBackend")

    backend = KrakenCcxtBackend(enable_rate_limit=True, timeout_ms=12345)
    rows = backend.fetch_ohlcv(
        symbol="BTC/EUR",
        timeframe="1h",
        since_ms=1700000000000,
        limit=2,
    )

    assert len(rows) == 2
    for rec in rows:
        assert set(rec.keys()) == {"ts_ms", "open", "high", "low", "close", "volume"}
        assert isinstance(rec["ts_ms"], int)
        assert isinstance(rec["open"], float)
        assert isinstance(rec["high"], float)
        assert isinstance(rec["low"], float)
        assert isinstance(rec["close"], float)
        assert isinstance(rec["volume"], float)

    assert rows[0]["ts_ms"] == 1700000000000
    assert rows[0]["open"] == 1.0
    assert rows[0]["high"] == 2.0
    assert rows[0]["low"] == 0.5
    assert rows[0]["close"] == 1.5
    assert rows[0]["volume"] == 10.0


def test_missing_ccxt_raises_helpful_error(monkeypatch):
    sys.modules.pop("ccxt", None)

    real_import_module = importlib.import_module

    def fake_import_module(name: str, package: Optional[str] = None) -> types.ModuleType:
        if name == "ccxt":
            raise ModuleNotFoundError("No module named 'ccxt'")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    from src.data.providers.kraken_ccxt_backend import KrakenCcxtBackend

    backend = KrakenCcxtBackend()
    with pytest.raises(ModuleNotFoundError) as ei:
        backend.fetch_ohlcv("BTC/EUR", "1h")

    msg = str(ei.value)
    assert "Optional dependency missing" in msg
    assert "ccxt" in msg
