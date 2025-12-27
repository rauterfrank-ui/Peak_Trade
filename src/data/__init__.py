"""
Peak_Trade Data Module
=======================
Datenbeschaffung, Normalisierung, Caching und Preprocessing.
"""

# WICHTIG: Konstanten ZUERST definieren, bevor Module importiert werden
REQUIRED_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]

# Kraken-Integration (bestehend)
from .kraken import get_kraken_client, fetch_ohlcv_df, clear_cache

# Data-Layer-Komponenten (neu)
from .loader import CsvLoader, KrakenCsvLoader
from .normalizer import DataNormalizer, resample_ohlcv
from .cache import ParquetCache

# Vollständige Export-Liste
__all__ = [
    # Konstanten
    "REQUIRED_OHLCV_COLUMNS",
    # Kraken-Integration
    "get_kraken_client",
    "fetch_ohlcv_df",
    "clear_cache",
    # Data-Layer
    "CsvLoader",
    "KrakenCsvLoader",
    "DataNormalizer",
    "resample_ohlcv",
    "ParquetCache",
]
# Kraken-Pipeline (neu)
from .kraken_pipeline import (
    KrakenDataPipeline,
    fetch_kraken_data,
    test_kraken_connection,
)

# Update __all__
__all__.extend(
    [
        "KrakenDataPipeline",
        "fetch_kraken_data",
        "test_kraken_connection",
    ]
)

# Phase 31: Kraken Live Candle Source
from .kraken_live import (
    KrakenLiveCandleSource,
    FakeCandleSource,
    LiveCandle,
    ShadowPaperConfig,
    LiveExchangeConfig,
    load_shadow_paper_config,
    load_live_exchange_config,
    create_kraken_source_from_config,
)

__all__.extend(
    [
        "KrakenLiveCandleSource",
        "FakeCandleSource",
        "LiveCandle",
        "ShadowPaperConfig",
        "LiveExchangeConfig",
        "load_shadow_paper_config",
        "load_live_exchange_config",
        "create_kraken_source_from_config",
    ]
)

# Phase 79: Kraken Cache Loader with Data-QC
from .kraken_cache_loader import (
    KrakenDataHealth,
    load_kraken_cache_window,
    check_data_health_only,
    get_real_market_smokes_config,
    list_available_cache_files,
)

__all__.extend(
    [
        "KrakenDataHealth",
        "load_kraken_cache_window",
        "check_data_health_only",
        "get_real_market_smokes_config",
        "list_available_cache_files",
    ]
)

# Wave A (Stability): Data Contract Gate
from .contracts import validate_ohlcv

__all__.extend(
    [
        "validate_ohlcv",
    ]
)

# Wave A (Stability): Atomic Cache Operations
from .cache_atomic import (
    atomic_write,
    atomic_read,
)

__all__.extend(
    [
        "atomic_write",
        "atomic_read",
    ]
)

# Wave B (Stability): Cache Manifest System
from .cache_manifest import (
    CacheManifest,
    FileEntry,
)

__all__.extend(
    [
        "CacheManifest",
        "FileEntry",
    ]
)
