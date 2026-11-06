from __future__ import annotations

import importlib
import sys
import types

import pytest


def _ensure_fake_pandas(monkeypatch):
    """
    Diese Tests zielen auf ccxt-Optionalität, nicht auf pandas.
    In minimalen Test-Envs kann pandas fehlen; wir stubben es daher für reine Import-Checks.
    """
    if "pandas" in sys.modules:
        return
    fake_pd = types.ModuleType("pandas")

    class _FakeDataFrame:  # pragma: no cover
        pass

    class _FakeDatetimeIndex:  # pragma: no cover
        pass

    setattr(fake_pd, "DataFrame", _FakeDataFrame)
    setattr(fake_pd, "DatetimeIndex", _FakeDatetimeIndex)
    monkeypatch.setitem(sys.modules, "pandas", fake_pd)


def test_import_exchange_ccxt_shim_does_not_import_ccxt(monkeypatch):
    sys.modules.pop("ccxt", None)
    _ensure_fake_pandas(monkeypatch)
    importlib.import_module("src.exchange.ccxt_client")
    assert "ccxt" not in sys.modules


def test_import_data_exchange_client_shim_does_not_import_ccxt():
    sys.modules.pop("ccxt", None)
    importlib.import_module("src.data.exchange_client")
    assert "ccxt" not in sys.modules


def test_shim_raises_helpful_error_on_instantiation_when_ccxt_missing(monkeypatch):
    """
    Ensure ccxt absence only errors on demand (instantiation/load), not at import-time.
    """
    # Make sure any accidental cached module is cleared.
    sys.modules.pop("ccxt", None)

    # Import shim (should not import ccxt)
    _ensure_fake_pandas(monkeypatch)
    shim_mod = importlib.import_module("src.exchange.ccxt_client")
    assert "ccxt" not in sys.modules

    # Patch importlib to simulate provider import failing due to missing ccxt.
    real_import_module = importlib.import_module

    def fake_import_module(name: str, package: str | None = None):
        if name in (
            "src.data.providers.ccxt_exchange_client",
            "src.data.providers.resilient_ccxt_exchange_client",
        ):
            raise ModuleNotFoundError("No module named 'ccxt'")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    # Now trigger on-demand loading
    with pytest.raises(ModuleNotFoundError) as ei:
        shim_mod._load_impl()

    msg = str(ei.value)
    assert "ccxt" in msg.lower()
    assert "pip install" in msg.lower()
