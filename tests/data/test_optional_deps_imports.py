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


def test_lazy_kraken_symbol_raises_helpful_error_when_ccxt_missing(monkeypatch):
    """
    Simulate 'ccxt' missing even if it's installed, by intercepting importlib.import_module
    when src.data.kraken is imported and forcing a ModuleNotFoundError('ccxt').
    """
    real_import_module = importlib.import_module

    def fake_import_module(name: str, package: str | None = None):
        if name == "src.data.kraken":
            # Simulate that importing kraken fails due to missing ccxt.
            raise ModuleNotFoundError("No module named 'ccxt'")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    data_mod = importlib.import_module("src.data")

    # Accessing the optional symbol should now raise a helpful error.
    with pytest.raises(ModuleNotFoundError) as ei:
        _ = getattr(data_mod, "get_kraken_client")

    msg = str(ei.value)
    assert "Optional dependency missing" in msg
    assert "ccxt" in msg
