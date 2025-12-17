"""
Data Cache: Parquet-basierter Cache für normalisierte OHLCV-Daten.
"""
import glob
import os
import re

import pandas as pd

from . import REQUIRED_OHLCV_COLUMNS


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
        Speichert DataFrame als Parquet.
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
        df.to_parquet(cache_path, compression=compression, index=True)

    def load(self, key: str) -> pd.DataFrame:
        """
        Lädt DataFrame aus Cache.
        """
        cache_path = self._get_cache_path(key)
        if not os.path.exists(cache_path):
            raise FileNotFoundError(
                f"Cache nicht gefunden für Key: '{key}'. "
                f"Erwarteter Pfad: {cache_path}"
            )
        return pd.read_parquet(cache_path)

    def exists(self, key: str) -> bool:
        """
        Prüft, ob Cache existiert.
        """
        cache_path = self._get_cache_path(key)
        return os.path.exists(cache_path)

    def clear(self, key: str | None = None) -> None:
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
