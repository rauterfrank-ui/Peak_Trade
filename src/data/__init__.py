"""
Peak_Trade Data Module
=======================
Datenbeschaffung, Normalisierung, Caching und Preprocessing.
"""

# WICHTIG: Konstanten ZUERST definieren, bevor Module importiert werden
REQUIRED_OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]

# Kraken-Integration (bestehend)
from .cache import ParquetCache
from .kraken import clear_cache, fetch_ohlcv_df, get_kraken_client

# Data-Layer-Komponenten (neu)
from .loader import CsvLoader, KrakenCsvLoader
from .normalizer import DataNormalizer, resample_ohlcv

# Vollständige Export-Liste
__all__ = [
    # Konstanten
    "REQUIRED_OHLCV_COLUMNS",
    # Data-Layer
    "CsvLoader",
    "DataNormalizer",
    "KrakenCsvLoader",
    "ParquetCache",
    "clear_cache",
    "fetch_ohlcv_df",
    # Kraken-Integration
    "get_kraken_client",
    "resample_ohlcv",
]
# Kraken-Pipeline (neu)
from .kraken_pipeline import (
    KrakenDataPipeline,
    fetch_kraken_data,
    test_kraken_connection,
)

# Update __all__
__all__.extend([
    "KrakenDataPipeline",
    "fetch_kraken_data",
    "test_kraken_connection",
])

# Phase 31: Kraken Live Candle Source
from .kraken_live import (
    FakeCandleSource,
    KrakenLiveCandleSource,
    LiveCandle,
    LiveExchangeConfig,
    ShadowPaperConfig,
    create_kraken_source_from_config,
    load_live_exchange_config,
    load_shadow_paper_config,
)

__all__.extend([
    "FakeCandleSource",
    "KrakenLiveCandleSource",
    "LiveCandle",
    "LiveExchangeConfig",
    "ShadowPaperConfig",
    "create_kraken_source_from_config",
    "load_live_exchange_config",
    "load_shadow_paper_config",
])

# Phase 79: Kraken Cache Loader with Data-QC
from .kraken_cache_loader import (
    KrakenDataHealth,
    check_data_health_only,
    get_real_market_smokes_config,
    list_available_cache_files,
    load_kraken_cache_window,
)

__all__.extend([
    "KrakenDataHealth",
    "check_data_health_only",
    "get_real_market_smokes_config",
    "list_available_cache_files",
    "load_kraken_cache_window",
])
