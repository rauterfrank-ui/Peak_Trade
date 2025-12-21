"""
Data Cache: Parquet-basierter Cache für normalisierte OHLCV-Daten.
"""

import glob
import os
import re
from typing import Optional

import pandas as pd

from . import REQUIRED_OHLCV_COLUMNS
from .cache_atomic import atomic_write, atomic_read


class ParquetCache:
    """
    Parquet-basierter Cache für normalisierte OHLCV-Daten.
    """

    def __init__(self, cache_dir: str = "./data_cache") -> None:
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def save(
        self,
        df: pd.DataFrame,
        key: str,
        compression: str = "snappy",
    ) -> None:
        """
        Speichert DataFrame als Parquet mit atomaren Schreiboperationen.

        Atomic Write Contract:
        - Schreibt zuerst in temporäre Datei (.tmp)
        - Führt fsync() aus um Daten auf Disk zu flushen
        - Verwendet os.replace() (atomic auf POSIX) für finales Rename
        - Räumt .tmp bei Fehler automatisch auf

        Dies verhindert Datenverlust bei Crash/Interrupt während des Schreibens.

        Args:
            df: DataFrame mit DatetimeIndex und OHLCV-Spalten
            key: Cache-Key für Dateiname
            compression: Parquet-Kompression (default: snappy)

        Raises:
            ValueError: Wenn df nicht DatetimeIndex hat oder OHLCV-Spalten fehlen
            CacheCorruptionError: Wenn atomares Schreiben fehlschlägt
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError(
                "DataFrame muss DatetimeIndex haben für Caching. "
                f"Aktueller Index: {type(df.index).__name__}"
            )

        missing_cols = set(REQUIRED_OHLCV_COLUMNS) - set(df.columns)
        if missing_cols:
            raise ValueError(
                "DataFrame muss OHLCV-Spalten enthalten für Caching. "
                f"Fehlend: {sorted(missing_cols)}"
            )

        cache_path = self._get_cache_path(key)
        atomic_write(df, cache_path, compression=compression, checksum=False)

    def load(self, key: str) -> pd.DataFrame:
        """
        Lädt DataFrame aus Cache mit Corruption Detection.

        Führt Integritätsprüfung durch beim Laden:
        - Prüft ob Datei existiert
        - Versucht Parquet-Datei zu laden
        - Gibt aussagekräftige Fehlermeldung bei Corruption (kein Silent Fail)

        Args:
            key: Cache-Key für Dateiname

        Returns:
            Geladener DataFrame aus Cache

        Raises:
            FileNotFoundError: Wenn Cache-Datei nicht gefunden
            CacheCorruptionError: Wenn Datei korrupt oder unleserlich
        """
        cache_path = self._get_cache_path(key)
        if not os.path.exists(cache_path):
            raise FileNotFoundError(
                f"Cache nicht gefunden für Key: '{key}'. Erwarteter Pfad: {cache_path}"
            )
        return atomic_read(cache_path, verify_checksum=False)

    def exists(self, key: str) -> bool:
        """
        Prüft, ob Cache existiert.
        """
        cache_path = self._get_cache_path(key)
        return os.path.exists(cache_path)

    def clear(self, key: Optional[str] = None) -> None:
        """
        Löscht Cache-Dateien.
        """
        if key is None:
            pattern = os.path.join(self.cache_dir, "*.parquet")
            for filepath in glob.glob(pattern):
                os.remove(filepath)
        else:
            cache_path = self._get_cache_path(key)
            if os.path.exists(cache_path):
                os.remove(cache_path)

    def _get_cache_path(self, key: str) -> str:
        """
        Generiert Dateipfad für einen Cache-Key.
        """
        sanitized = re.sub(r"[^\w\-_]", "_", key)
        filename = f"{sanitized}.parquet"
        return os.path.join(self.cache_dir, filename)
