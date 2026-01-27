from __future__ import annotations

from typing import Any

# NOTE:
# Keep src.data importable in minimal environments.
# Do NOT import optional provider modules (e.g. kraken -> ccxt) at import time.

# WICHTIG: Konstanten bleiben top-level verfügbar (dependency-free).
REQUIRED_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]

# Public API surface.
# Wir halten __init__ dependency-free; alle Symbole werden via __getattr__ lazy geladen.
__all__ = [
    "REQUIRED_OHLCV_COLUMNS",
    # Kraken / ccxt (optional)
    "get_kraken_client",
    "fetch_ohlcv_df",
    "clear_cache",
    "KrakenDataPipeline",
    "fetch_kraken_data",
    "test_kraken_connection",
    "KrakenLiveCandleSource",
    "FakeCandleSource",
    "LiveCandle",
    "ShadowPaperConfig",
    "LiveExchangeConfig",
    "load_shadow_paper_config",
    "load_live_exchange_config",
    "create_kraken_source_from_config",
    "KrakenDataHealth",
    "load_kraken_cache_window",
    "check_data_health_only",
    "get_real_market_smokes_config",
    "list_available_cache_files",
    # Core data utilities (non-ccxt, but still lazy to keep src.data import light)
    "CsvLoader",
    "KrakenCsvLoader",
    "DataNormalizer",
    "resample_ohlcv",
    "ParquetCache",
    "validate_ohlcv",
    "atomic_write",
    "atomic_read",
    "CacheManifest",
    "FileEntry",
]

_OPTIONAL_SYMBOLS: dict[str, tuple[str, str]] = {
    # Kraken provider (+ pipelines) -> may depend on ccxt
    "get_kraken_client": ("src.data.kraken", "get_kraken_client"),
    "fetch_ohlcv_df": ("src.data.kraken", "fetch_ohlcv_df"),
    "clear_cache": ("src.data.kraken", "clear_cache"),
    "KrakenDataPipeline": ("src.data.kraken_pipeline", "KrakenDataPipeline"),
    "fetch_kraken_data": ("src.data.kraken_pipeline", "fetch_kraken_data"),
    "test_kraken_connection": ("src.data.kraken_pipeline", "test_kraken_connection"),
    "KrakenLiveCandleSource": ("src.data.kraken_live", "KrakenLiveCandleSource"),
    "FakeCandleSource": ("src.data.kraken_live", "FakeCandleSource"),
    "LiveCandle": ("src.data.kraken_live", "LiveCandle"),
    "ShadowPaperConfig": ("src.data.kraken_live", "ShadowPaperConfig"),
    "LiveExchangeConfig": ("src.data.kraken_live", "LiveExchangeConfig"),
    "load_shadow_paper_config": ("src.data.kraken_live", "load_shadow_paper_config"),
    "load_live_exchange_config": ("src.data.kraken_live", "load_live_exchange_config"),
    "create_kraken_source_from_config": (
        "src.data.kraken_live",
        "create_kraken_source_from_config",
    ),
    "KrakenDataHealth": ("src.data.kraken_cache_loader", "KrakenDataHealth"),
    "load_kraken_cache_window": ("src.data.kraken_cache_loader", "load_kraken_cache_window"),
    "check_data_health_only": ("src.data.kraken_cache_loader", "check_data_health_only"),
    "get_real_market_smokes_config": (
        "src.data.kraken_cache_loader",
        "get_real_market_smokes_config",
    ),
    "list_available_cache_files": ("src.data.kraken_cache_loader", "list_available_cache_files"),
    # Core utilities (safe, but lazy for lightweight imports)
    "CsvLoader": ("src.data.loader", "CsvLoader"),
    "KrakenCsvLoader": ("src.data.loader", "KrakenCsvLoader"),
    "DataNormalizer": ("src.data.normalizer", "DataNormalizer"),
    "resample_ohlcv": ("src.data.normalizer", "resample_ohlcv"),
    "ParquetCache": ("src.data.cache", "ParquetCache"),
    "validate_ohlcv": ("src.data.contracts", "validate_ohlcv"),
    "atomic_write": ("src.data.cache_atomic", "atomic_write"),
    "atomic_read": ("src.data.cache_atomic", "atomic_read"),
    "CacheManifest": ("src.data.cache_manifest", "CacheManifest"),
    "FileEntry": ("src.data.cache_manifest", "FileEntry"),
}


def _optional_dep_error(symbol: str, exc: ModuleNotFoundError) -> ModuleNotFoundError:
    """
    Liefert eine hilfreiche Fehlermeldung für on-demand Imports.
    Wir zielen hier explizit auf den häufigsten Fall: ccxt fehlt.
    """
    msg = (
        f"Optional dependency missing while importing '{symbol}'.\n\n"
        f"This symbol is provided by the Kraken data provider, which depends on 'ccxt'.\n"
        f"Install ccxt (or the project's optional extra that includes ccxt) and retry.\n\n"
        f"Examples:\n"
        f"  pip install ccxt\n"
        f"  # or (if your project defines an extra)\n"
        f'  pip install -e ".[<extra-that-includes-ccxt>]"\n'
    )
    return ModuleNotFoundError(msg)


def __getattr__(name: str) -> Any:
    """
    Lazy-load optional provider symbols (PEP 562).

    This keeps `import src.data` and transitively `import src.data.backend` working
    without optional deps like ccxt.
    """
    if name not in _OPTIONAL_SYMBOLS:
        raise AttributeError(f"module 'src.data' has no attribute {name!r}")

    module_name, attr_name = _OPTIONAL_SYMBOLS[name]
    try:
        import importlib

        mod = importlib.import_module(module_name)
        return getattr(mod, attr_name)
    except ModuleNotFoundError as exc:
        # Wrap only ccxt-missing with a helpful message; otherwise preserve original error.
        exc_name = getattr(exc, "name", "") or ""
        if exc_name == "ccxt" or "ccxt" in str(exc):
            raise _optional_dep_error(name, exc) from exc
        raise


def __dir__() -> list[str]:
    # Improves autocomplete / dir(src.data)
    return sorted(set(globals().keys()) | set(_OPTIONAL_SYMBOLS.keys()))
