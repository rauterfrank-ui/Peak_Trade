"""
Peak_Trade Kraken Data Module
==============================
OHLCV-Datenbeschaffung von Kraken mit Parquet-Caching.

Features:
- ccxt-basierte Kraken-Integration
- Automatisches Parquet-Caching
- UTC-DatetimeIndex
- Error-Handling
"""

import ccxt
import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import logging

from ..core.config_registry import get_config

logger = logging.getLogger(__name__)


def get_kraken_client() -> ccxt.kraken:
    """
    Erstellt Kraken-Client mit sicheren Defaults.
    
    Returns:
        Konfigurierter ccxt.kraken-Client
        
    Note:
        API-Keys aus Umgebungsvariablen, NICHT aus config.toml!
    """
    return ccxt.kraken({
        "enableRateLimit": True,
        "rateLimit": 1000,  # 1 Sekunde zwischen Requests
        "options": {"defaultType": "spot"},  # KEIN Margin/Futures!
    })



def _get_cache_path(symbol: str, timeframe: str) -> Path:
    """Erzeugt Cache-Pfad für OHLCV-Daten."""
    cfg = get_config()
    # config ist jetzt ein Dict, nicht mehr ein Pydantic-Objekt
    data_dir = cfg.get("data", {}).get("data_dir", "data")
    cache_dir = Path(data_dir) / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize symbol für Dateinamen (BTC/USD -> BTC_USD)
    safe_symbol = symbol.replace("/", "_")
    return cache_dir / f"{safe_symbol}_{timeframe}.parquet"


def fetch_ohlcv_df(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 720,
    since_ms: Optional[int] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Holt OHLCV-Daten von Kraken mit optionalem Caching.
    
    Args:
        symbol: Trading-Pair (z.B. "BTC/USD")
        timeframe: Zeitrahmen ("1m", "5m", "1h", "1d")
        limit: Anzahl Bars (max. 720)
        since_ms: Start-Timestamp in Millisekunden
        use_cache: Parquet-Cache verwenden?
        
    Returns:
        DataFrame mit UTC-DatetimeIndex
        Spalten: [open, high, low, close, volume]
        
    Raises:
        ccxt.NetworkError: Bei Verbindungsproblemen
        ccxt.ExchangeError: Bei API-Fehlern
        
    Example:
        >>> df = fetch_ohlcv_df("BTC/USD", "1h", limit=100)
        >>> print(df.head())
                             open     high      low    close  volume
        2024-12-01 00:00:00  50000  50100  49900  50050    10.5
    """
    cache_path = _get_cache_path(symbol, timeframe)
    
    # 1. Cache-Check
    if use_cache and cache_path.exists():
        logger.info(f"Lade {symbol} {timeframe} aus Cache: {cache_path}")
        df = pd.read_parquet(cache_path)
        df.index = pd.to_datetime(df.index, utc=True)
        return df
    
    # 2. Von Kraken holen
    logger.info(f"Hole {symbol} {timeframe} von Kraken (limit={limit})")
    
    try:
        client = get_kraken_client()
        ohlcv = client.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            since=since_ms
        )
        
        # 3. In DataFrame konvertieren
        df = pd.DataFrame(
            ohlcv,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        
        # 4. Timestamp -> UTC DateTime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df.set_index("timestamp", inplace=True)
        
        # 5. In Cache speichern
        if use_cache:
            logger.info(f"Speichere in Cache: {cache_path}")
            df.to_parquet(cache_path)
        
        logger.info(f"Geladen: {len(df)} Bars von {df.index[0]} bis {df.index[-1]}")
        return df
        
    except ccxt.NetworkError as e:
        logger.error(f"Netzwerkfehler bei Kraken: {e}")
        raise
    except ccxt.ExchangeError as e:
        logger.error(f"Kraken API-Fehler: {e}")
        raise


def clear_cache(symbol: Optional[str] = None, timeframe: Optional[str] = None) -> None:
    """
    Löscht Cache-Dateien.
    
    Args:
        symbol: Spezifisches Symbol (oder None für alle)
        timeframe: Spezifischer Timeframe (oder None für alle)
        
    Example:
        >>> clear_cache("BTC/USD", "1h")  # Nur BTC/USD 1h löschen
        >>> clear_cache()                  # Gesamten Cache löschen
    """
    cfg = get_config()
    cache_dir = Path(cfg.data.data_dir) / "cache"
    
    if not cache_dir.exists():
        logger.info("Cache-Verzeichnis existiert nicht")
        return
    
    if symbol and timeframe:
        # Spezifische Datei löschen
        cache_path = _get_cache_path(symbol, timeframe)
        if cache_path.exists():
            cache_path.unlink()
            logger.info(f"Cache gelöscht: {cache_path}")
    else:
        # Gesamten Cache löschen
        for cache_file in cache_dir.glob("*.parquet"):
            cache_file.unlink()
            logger.info(f"Cache gelöscht: {cache_file}")
        logger.info("Gesamter Cache gelöscht")
