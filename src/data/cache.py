"""
Data Cache: Parquet-basierter Cache für normalisierte OHLCV-Daten.

Wave A (Stability): Data Contract Validation at Cache Boundaries
"""
import glob
import os
import re
from typing import Optional
import logging

import pandas as pd

from . import REQUIRED_OHLCV_COLUMNS
from .cache_atomic import atomic_write, atomic_read
from .contracts import validate_ohlcv
from ..core.errors import DataContractError

logger = logging.getLogger(__name__)


class ParquetCache:
    """
    Parquet-basierter Cache für normalisierte OHLCV-Daten.
    """

    def __init__(self, cache_dir: str = "./data_cache", validate_on_load: bool = False, validate_on_save: bool = False) -> None:
        """
        Initialize ParquetCache.
        
        Args:
            cache_dir: Directory for cache files
            validate_on_load: Validate data contract when loading from cache (default: False for backward compatibility)
            validate_on_save: Validate data contract when saving to cache (default: False for backward compatibility)
            
        Note:
            For production use, it's recommended to enable validation:
            cache = ParquetCache(validate_on_load=True, validate_on_save=True)
        """
        self.cache_dir = cache_dir
        self.validate_on_load = validate_on_load
        self.validate_on_save = validate_on_save
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
            DataContractError: Wenn Validierung fehlschlägt (validate_on_save=True)
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

        # Wave A (Stability): Data Contract Validation on Save
        if self.validate_on_save:
            is_valid, errors = validate_ohlcv(df, strict=True, require_tz=True)
            if not is_valid:
                raise DataContractError(
                    f"OHLCV validation failed before caching: {errors[0]}",
                    hint="Ensure data is valid before caching",
                    context={
                        "errors": errors,
                        "shape": df.shape,
                        "cache_key": key,
                    }
                )
            logger.debug(f"Data contract validation passed for cache key: {key}")

        cache_path = self._get_cache_path(key)
        atomic_write(df, cache_path, compression=compression, checksum=False)

    def load(self, key: str) -> pd.DataFrame:
        """
        Lädt DataFrame aus Cache mit Corruption Detection.

        Führt Integritätsprüfung durch beim Laden:
        - Prüft ob Datei existiert
        - Versucht Parquet-Datei zu laden
        - Validiert Data Contract (wenn validate_on_load=True)
        - Gibt aussagekräftige Fehlermeldung bei Corruption (kein Silent Fail)

        Args:
            key: Cache-Key für Dateiname

        Returns:
            Geladener DataFrame aus Cache

        Raises:
            FileNotFoundError: Wenn Cache-Datei nicht gefunden
            DataContractError: Wenn Validierung fehlschlägt (validate_on_load=True)
            CacheCorruptionError: Wenn Datei korrupt oder unleserlich
        """
        cache_path = self._get_cache_path(key)
        if not os.path.exists(cache_path):
            raise FileNotFoundError(
                f"Cache nicht gefunden für Key: '{key}'. "
                f"Erwarteter Pfad: {cache_path}"
            )
        
        df = atomic_read(cache_path, verify_checksum=False)
        
        # Wave A (Stability): Data Contract Validation on Load
        if self.validate_on_load:
            is_valid, errors = validate_ohlcv(df, strict=True, require_tz=True)
            if not is_valid:
                logger.warning(
                    f"Cached data validation failed for key '{key}': {errors[0]}"
                )
                raise DataContractError(
                    f"OHLCV validation failed after loading from cache: {errors[0]}",
                    hint="Cache may be corrupted. Consider clearing and re-fetching.",
                    context={
                        "errors": errors,
                        "shape": df.shape,
                        "cache_key": key,
                        "cache_path": cache_path,
                    }
                )
            logger.debug(f"Data contract validation passed for cache key: {key}")
        
        return df

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