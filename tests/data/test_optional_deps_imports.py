from __future__ import annotations

import importlib
import sys
import types

import pytest


def test_import_backend_does_not_import_ccxt(monkeypatch):
    # Ensure a clean-ish slate for the assertion.
    sys.modules.pop("ccxt", None)

    # Ensure `import src.data.backend` can run even if pandas isn't installed in this env.
    if "pandas" not in sys.modules:
        fake_pd = types.ModuleType("pandas")

        class _FakeDataFrame:  # pragma: no cover
            pass

        setattr(fake_pd, "DataFrame", _FakeDataFrame)
        setattr(fake_pd, "read_parquet", lambda *_args, **_kwargs: None)
        monkeypatch.setitem(sys.modules, "pandas", fake_pd)

    importlib.import_module("src.data.backend")

    # Core assertion: importing backend must not eagerly import ccxt.
    assert "ccxt" not in sys.modules


def test_data_package_does_not_export_removed_venue_client(monkeypatch):
    data_mod = importlib.import_module("src.data")
    assert not hasattr(data_mod, "get_kraken_client")
    assert not hasattr(data_mod, "KrakenLiveCandleSource")
