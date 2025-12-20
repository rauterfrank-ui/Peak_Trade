"""
Peak_Trade Kraken Data Module
==============================
OHLCV-Datenbeschaffung von Kraken mit Parquet-Caching.

Features:
- ccxt-basierte Kraken-Integration
- Automatisches Parquet-Caching
- UTC-DatetimeIndex
- Error-Handling mit ProviderError
"""

import ccxt
import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import logging

from ..core.config_registry import get_config
from ..core.errors import ProviderError, CacheError, chain_error

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
        ProviderError: Bei Verbindungsproblemen oder API-Fehlern
        CacheError: Bei Cache-Lese-/Schreibproblemen
        
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
        try:
            df = pd.read_parquet(cache_path)
            df.index = pd.to_datetime(df.index, utc=True)
            return df
        except Exception as e:
            raise CacheError(
                f"Failed to read cache file: {cache_path}",
                hint="Try clearing the cache with clear_cache() or check file permissions",
                context={"cache_path": str(cache_path), "symbol": symbol, "timeframe": timeframe},
                cause=e
            )
    
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
            try:
                df.to_parquet(cache_path)
            except Exception as e:
                # Log but don't fail on cache write errors
                logger.warning(f"Failed to write cache: {e}")
        
        logger.info(f"Geladen: {len(df)} Bars von {df.index[0]} bis {df.index[-1]}")
        return df
        
    except ccxt.NetworkError as e:
        logger.error(f"Netzwerkfehler bei Kraken: {e}")
        raise ProviderError(
            f"Network error connecting to Kraken API",
            hint="Check your internet connection and verify Kraken API status at status.kraken.com",
            context={"symbol": symbol, "timeframe": timeframe, "limit": limit},
            cause=e
        )
    except ccxt.RateLimitExceeded as e:
        logger.error(f"Kraken Rate Limit überschritten: {e}")
        raise ProviderError(
            f"Kraken API rate limit exceeded",
            hint="Wait 60 seconds before retrying or reduce request frequency",
            context={"symbol": symbol, "timeframe": timeframe},
            cause=e
        )
    except ccxt.AuthenticationError as e:
        logger.error(f"Kraken Authentifizierungsfehler: {e}")
        raise ProviderError(
            f"Kraken API authentication failed",
            hint="Check API credentials in environment variables (KRAKEN_API_KEY, KRAKEN_API_SECRET)",
            context={"symbol": symbol},
            cause=e
        )
    except ccxt.ExchangeError as e:
        logger.error(f"Kraken API-Fehler: {e}")
        raise ProviderError(
            f"Kraken API error: {str(e)}",
            hint=f"Check if symbol '{symbol}' is valid and supported by Kraken",
            context={"symbol": symbol, "timeframe": timeframe},
            cause=e
        )
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Laden von Kraken-Daten: {e}")
        raise chain_error(
            e,
            f"Unexpected error fetching data from Kraken",
            hint="Check logs for details",
            context={"symbol": symbol, "timeframe": timeframe}
        )


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
