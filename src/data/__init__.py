from __future__ import annotations

from typing import Any

# Keep src.data importable in minimal environments.
# Do not import optional provider modules at import time.

REQUIRED_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]

__all__ = [
    "REQUIRED_OHLCV_COLUMNS",
    "FakeCandleSource",
    "LiveCandle",
    "ShadowPaperConfig",
    "LiveExchangeConfig",
    "load_shadow_paper_config",
    "load_live_exchange_config",
    "MarketDataCacheHealth",
    "load_market_data_cache_window",
    "check_data_health_only",
    "get_real_market_smokes_config",
    "list_available_cache_files",
    "CsvLoader",
    "UnixSecondsOhlcCsvLoader",
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
    "FakeCandleSource": ("src.data.simulation_candles", "FakeCandleSource"),
    "LiveCandle": ("src.data.simulation_candles", "LiveCandle"),
    "ShadowPaperConfig": ("src.data.simulation_candles", "ShadowPaperConfig"),
    "LiveExchangeConfig": ("src.data.simulation_candles", "LiveExchangeConfig"),
    "load_shadow_paper_config": ("src.data.simulation_candles", "load_shadow_paper_config"),
    "load_live_exchange_config": ("src.data.simulation_candles", "load_live_exchange_config"),
    "MarketDataCacheHealth": ("src.data.market_data_cache_loader", "MarketDataCacheHealth"),
    "load_market_data_cache_window": (
        "src.data.market_data_cache_loader",
        "load_market_data_cache_window",
    ),
    "check_data_health_only": ("src.data.market_data_cache_loader", "check_data_health_only"),
    "get_real_market_smokes_config": (
        "src.data.market_data_cache_loader",
        "get_real_market_smokes_config",
    ),
    "list_available_cache_files": (
        "src.data.market_data_cache_loader",
        "list_available_cache_files",
    ),
    "CsvLoader": ("src.data.loader", "CsvLoader"),
    "UnixSecondsOhlcCsvLoader": ("src.data.loader", "UnixSecondsOhlcCsvLoader"),
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
    msg = (
        f"Optional dependency missing while importing '{symbol}'.\n\n"
        f"Install the missing package (often 'ccxt') and retry.\n\n"
        f"Examples:\n"
        f"  pip install ccxt\n"
        f'  pip install -e ".[ccxt]"\n'
    )
    return ModuleNotFoundError(msg)


def __getattr__(name: str) -> Any:
    if name not in _OPTIONAL_SYMBOLS:
        raise AttributeError(f"module 'src.data' has no attribute {name!r}")

    module_name, attr_name = _OPTIONAL_SYMBOLS[name]
    try:
        import importlib

        mod = importlib.import_module(module_name)
        return getattr(mod, attr_name)
    except ModuleNotFoundError as exc:
        exc_name = getattr(exc, "name", "") or ""
        if exc_name == "ccxt" or "ccxt" in str(exc):
            raise _optional_dep_error(name, exc) from exc
        raise


def __dir__() -> list[str]:
    return sorted(set(globals().keys()) | set(_OPTIONAL_SYMBOLS.keys()))
