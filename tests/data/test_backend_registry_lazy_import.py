from __future__ import annotations

import builtins
import importlib
import sys
import types

import pytest


def test_backend_registry_is_lazy_for_ccxt(monkeypatch):
    # Ensure a clean-ish slate for the assertion.
    sys.modules.pop("ccxt", None)

    # src.data.backend currently imports pandas; keep the test runnable in minimal envs.
    if "pandas" not in sys.modules:
        fake_pd = types.ModuleType("pandas")

        class _FakeDataFrame:  # pragma: no cover
            pass

        setattr(fake_pd, "DataFrame", _FakeDataFrame)
        setattr(fake_pd, "read_parquet", lambda *_args, **_kwargs: None)
        monkeypatch.setitem(sys.modules, "pandas", fake_pd)

    backend_mod = importlib.import_module("src.data.backend")
    assert "ccxt" not in sys.modules

    backend = backend_mod.get_backend("kraken_ccxt")
    assert backend is not None
    assert backend.__class__.__name__ == "KrakenCcxtBackend"
    assert "ccxt" not in sys.modules  # still lazy

    # Only when we actually fetch should ccxt be required.
    sys.modules.pop("ccxt", None)

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name == "ccxt":
            raise ModuleNotFoundError("No module named 'ccxt'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ModuleNotFoundError):
        backend.fetch_ohlcv("BTC/EUR", "1h")
