"""
Kraken Data Pipeline Integration
==================================
Vollständige Pipeline: Kraken → Normalizer → Cache → Backtest-Ready

Workflow:
1. fetch_ohlcv_df() holt rohe Daten von Kraken
2. DataNormalizer normalisiert in Peak_Trade-Format
3. ParquetCache speichert für schnellen Zugriff
4. Optional: Resampling für andere Timeframes
"""

import logging
from pathlib import Path

import pandas as pd

from ..core.config_registry import get_config
from .cache import ParquetCache
from .kraken import fetch_ohlcv_df, get_kraken_client
from .normalizer import DataNormalizer, resample_ohlcv

logger = logging.getLogger(__name__)


class KrakenDataPipeline:
    """
    Vollständige Kraken-Daten-Pipeline mit Caching.

    Usage:
        >>> pipeline = KrakenDataPipeline()
        >>> df = pipeline.fetch_and_prepare("BTC/USD", timeframe="1h", limit=720)
        >>> print(df.head())
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        use_cache: bool = True
    ) -> None:
        """
        Args:
            cache_dir: Cache-Verzeichnis (default: aus config.toml)
            use_cache: Cache verwenden?
        """
        config = get_config()

        if cache_dir is None:
            # config ist jetzt ein Dict, nicht mehr ein Pydantic-Objekt
            data_dir = config.get("data", {}).get("data_dir", "data")
            cache_dir = str(Path(data_dir) / "cache")

        self.cache = ParquetCache(cache_dir=cache_dir)
        use_cache_cfg = config.get("data", {}).get("use_cache", True)
        self.use_cache = use_cache and use_cache_cfg
        self.normalizer = DataNormalizer()

    def fetch_and_prepare(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 720,
        since_ms: int | None = None,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Holt und bereitet OHLCV-Daten von Kraken auf.

        Workflow:
        1. Prüfe Cache (wenn use_cache=True und nicht force_refresh)
        2. Falls nicht im Cache: Von Kraken holen
        3. Normalisieren in Peak_Trade-Format
        4. In Cache speichern
        5. Return normalisierte Daten

        Args:
            symbol: Trading-Pair (z.B. "BTC/USD")
            timeframe: Zeitrahmen ("1m", "5m", "1h", "1d")
            limit: Anzahl Bars (max. 720)
            since_ms: Start-Timestamp in Millisekunden
            force_refresh: Cache ignorieren und neu von Kraken holen?

        Returns:
            Normalisierter DataFrame (DatetimeIndex UTC, OHLCV-Spalten)

        Example:
            >>> pipeline = KrakenDataPipeline()
            >>> df = pipeline.fetch_and_prepare("BTC/USD", "1h", limit=100)
            >>> print(df.columns)
            Index(['open', 'high', 'low', 'close', 'volume'], dtype='object')
        """
        # Cache-Key generieren
        cache_key = self._generate_cache_key(symbol, timeframe, limit, since_ms)

        # 1. Cache-Check (wenn aktiviert und nicht force_refresh)
        if self.use_cache and not force_refresh and self.cache.exists(cache_key):
            logger.info(f"📦 Lade aus Cache: {cache_key}")
            return self.cache.load(cache_key)

        # 2. Von Kraken holen
        logger.info(f"🌐 Hole von Kraken: {symbol} {timeframe} (limit={limit})")
        df_raw = fetch_ohlcv_df(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            since_ms=since_ms,
            use_cache=False  # Kraken-eigener Cache deaktiviert, wir nutzen unseren
        )

        # 3. Normalisieren (Kraken-Daten sind bereits im richtigen Format)
        # Aber wir prüfen trotzdem und stellen sicher
        df_normalized = self.normalizer.normalize(
            df_raw,
            ensure_utc=True,
            drop_extra_columns=True
        )

        # 4. In Cache speichern
        if self.use_cache:
            logger.info(f"💾 Speichere in Cache: {cache_key}")
            self.cache.save(df_normalized, key=cache_key)

        logger.info(f"✅ Geladen: {len(df_normalized)} Bars ({df_normalized.index[0]} bis {df_normalized.index[-1]})")
        return df_normalized

    def fetch_and_resample(
        self,
        symbol: str,
        source_timeframe: str = "1m",
        target_timeframe: str = "1h",
        limit: int = 720,
        since_ms: int | None = None,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Holt Daten in einem Timeframe und resampled sie.

        Nützlich wenn:
        - Kraken hat nur bestimmte Timeframes
        - Man will flexibel zwischen Timeframes wechseln

        Args:
            symbol: Trading-Pair
            source_timeframe: Quell-Timeframe von Kraken
            target_timeframe: Ziel-Timeframe nach Resampling
            limit: Anzahl Bars (vom Quell-Timeframe)
            since_ms: Start-Timestamp
            force_refresh: Cache ignorieren?

        Returns:
            Resampled DataFrame

        Example:
            >>> pipeline = KrakenDataPipeline()
            >>> # Hole 1-Minuten-Daten und resample auf 15min
            >>> df = pipeline.fetch_and_resample(
            ...     "BTC/USD",
            ...     source_timeframe="1m",
            ...     target_timeframe="15m",
            ...     limit=1440  # 1 Tag in 1-Minuten-Bars
            ... )
            >>> print(len(df))  # ~96 Bars (1440 / 15)
        """
        # 1. Quell-Daten holen
        df_source = self.fetch_and_prepare(
            symbol=symbol,
            timeframe=source_timeframe,
            limit=limit,
            since_ms=since_ms,
            force_refresh=force_refresh
        )

        # 2. Resamplen
        logger.info(f"🔄 Resampling: {source_timeframe} → {target_timeframe}")
        df_resampled = resample_ohlcv(df_source, freq=target_timeframe)

        # 3. Optional: Resampled-Daten auch cachen
        if self.use_cache:
            cache_key = self._generate_cache_key(
                symbol, f"{source_timeframe}_to_{target_timeframe}", len(df_resampled), since_ms
            )
            self.cache.save(df_resampled, key=cache_key)

        logger.info(f"✅ Resampled: {len(df_source)} → {len(df_resampled)} Bars")
        return df_resampled

    def clear_cache(self, symbol: str | None = None) -> None:
        """
        Löscht Cache-Einträge.

        Args:
            symbol: Spezifisches Symbol (oder None für alle)

        Example:
            >>> pipeline = KrakenDataPipeline()
            >>> pipeline.clear_cache("BTC/USD")  # Nur BTC/USD löschen
            >>> pipeline.clear_cache()            # Gesamten Cache löschen
        """
        if symbol:
            # Alle Keys für dieses Symbol löschen
            # (komplexer: müsste alle Keys durchsuchen)
            logger.warning("Symbol-spezifisches Löschen noch nicht implementiert")
            self.cache.clear()
        else:
            logger.info("🗑️  Lösche gesamten Cache")
            self.cache.clear()

    def _generate_cache_key(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
        since_ms: int | None
    ) -> str:
        """Generiert eindeutigen Cache-Key."""
        key_parts = [
            symbol.replace("/", "_"),
            timeframe,
            f"limit{limit}"
        ]
        if since_ms:
            key_parts.append(f"since{since_ms}")

        return "_".join(key_parts)


# Convenience-Funktionen für schnellen Zugriff

def fetch_kraken_data(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 720,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Convenience-Funktion: Holt Kraken-Daten mit voller Pipeline.

    Args:
        symbol: Trading-Pair (z.B. "BTC/USD")
        timeframe: Zeitrahmen
        limit: Anzahl Bars
        use_cache: Cache verwenden?

    Returns:
        Normalisierter DataFrame

    Example:
        >>> from src.data import fetch_kraken_data
        >>> df = fetch_kraken_data("BTC/USD", "1h", limit=100)
    """
    pipeline = KrakenDataPipeline(use_cache=use_cache)
    return pipeline.fetch_and_prepare(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit
    )


def test_kraken_connection() -> bool:
    """
    Testet Kraken-Verbindung.

    Returns:
        True wenn Verbindung OK, sonst False

    Example:
        >>> from src.data import test_kraken_connection
        >>> if test_kraken_connection():
        ...     print("Kraken OK!")
    """
    try:
        client = get_kraken_client()
        # Teste mit minimalem Request
        client.fetch_ticker("BTC/USD")
        logger.info("✅ Kraken-Verbindung OK")
        return True
    except Exception as e:
        logger.error(f"❌ Kraken-Verbindung fehlgeschlagen: {e}")
        return False
