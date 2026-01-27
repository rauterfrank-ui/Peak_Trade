"""
Peak_Trade Data Backend Layer (optional acceleration)
=====================================================

Ziel:
- Einheitliche API für Data-I/O (z.B. Parquet) und Konvertierung zu pandas
- Optional beschleunigte Backends (Polars, DuckDB) ohne harte Dependencies
- Safe-by-default: Default ist PandasBackend

Hinweis:
- Strategy API bleibt pandas: Strategien erwarten pd.DataFrame.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class DataBackend(Protocol):
    """Minimaler Backend-Contract für Data-I/O + pandas-Konvertierung."""

    @property
    def name(self) -> str:  # pragma: no cover
        ...

    def read_parquet(self, path: str | Path) -> pd.DataFrame:  # pragma: no cover
        ...

    def to_pandas(self, obj: Any) -> pd.DataFrame:  # pragma: no cover
        ...


@dataclass
class PandasBackend:
    """Default Backend: pandas (keine optionalen Dependencies)."""

    @property
    def name(self) -> str:
        return "pandas"

    def read_parquet(self, path: str | Path) -> pd.DataFrame:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"not found: {p}")
        return pd.read_parquet(p)

    def to_pandas(self, obj: Any) -> pd.DataFrame:
        if isinstance(obj, pd.DataFrame):
            return obj
        raise TypeError(f"Cannot convert {type(obj)} to pandas DataFrame")


@dataclass
class PolarsBackend:
    """
    Optional Backend: Polars.

    - Import wird lazy gemacht (RuntimeError wenn polars nicht installiert)
    - read_parquet gibt pandas.DataFrame zurück (Strategy API bleibt pandas)
    """

    def __post_init__(self) -> None:
        try:
            import polars as pl
        except Exception as e:  # pragma: no cover
            raise RuntimeError("polars not installed") from e
        self._pl = pl

    @property
    def name(self) -> str:
        return "polars"

    def read_parquet(self, path: str | Path) -> pd.DataFrame:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"not found: {p}")
        df = self._pl.read_parquet(str(p))
        return self.to_pandas(df)

    def to_pandas(self, obj: Any) -> pd.DataFrame:
        if isinstance(obj, pd.DataFrame):
            return obj
        # Polars DataFrame
        if obj.__class__.__module__.startswith("polars"):
            return obj.to_pandas()
        raise TypeError(f"Cannot convert {type(obj)} to pandas DataFrame")


@dataclass
class DuckDBBackend:
    """
    Optional Backend: DuckDB (für sehr schnelles Parquet Reading).

    - Import wird lazy gemacht (RuntimeError wenn duckdb nicht installiert)
    - read_parquet gibt pandas.DataFrame zurück
    """

    def __post_init__(self) -> None:
        try:
            import duckdb
        except Exception as e:  # pragma: no cover
            raise RuntimeError("duckdb not installed") from e
        self._duckdb = duckdb

    @property
    def name(self) -> str:
        return "duckdb"

    def read_parquet(self, path: str | Path) -> pd.DataFrame:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"not found: {p}")
        # DuckDB Parquet reader
        con = self._duckdb.connect(database=":memory:")
        try:
            return con.execute("SELECT * FROM read_parquet(?)", [str(p)]).df()
        finally:
            try:
                con.close()
            except Exception:
                pass

    def to_pandas(self, obj: Any) -> pd.DataFrame:
        if isinstance(obj, pd.DataFrame):
            return obj
        raise TypeError(f"Cannot convert {type(obj)} to pandas DataFrame")


def build_data_backend_from_config(cfg: Any) -> DataBackend:
    """
    Factory: erstellt DataBackend aus Config.

    Erwartete Keys (tolerant):
    - cfg.get("data.backend") -> "pandas" | "polars" | "duckdb"
    - oder dict: {"data": {"backend": "polars"}}
    """

    backend: str | None = None

    # PeakConfig-like: dotted get
    if hasattr(cfg, "get"):
        try:
            backend = cfg.get("data.backend", None)
        except TypeError:
            # Some get() impls don't support default parameter
            backend = cfg.get("data.backend")

    # Mapping-like
    if backend is None and isinstance(cfg, dict):
        data_section = cfg.get("data", {})
        if isinstance(data_section, dict):
            backend = data_section.get("backend")

    backend_norm = str(backend).strip().lower() if backend is not None else "pandas"

    if backend_norm in ("pandas", "", "default"):
        return PandasBackend()
    if backend_norm == "polars":
        return PolarsBackend()
    if backend_norm == "duckdb":
        return DuckDBBackend()

    raise ValueError(f"Unknown data backend: {backend_norm}")


# ============================================================================
# Provider Registry (lazy imports; optional deps)
# ============================================================================

# IMPORTANT:
# Do NOT import provider modules at import time (e.g. Kraken via ccxt).
# Keep src.data.backend importable in minimal envs.
REGISTRY: dict[str, tuple[str, str]] = {
    "kraken_ccxt": ("src.data.providers.kraken_ccxt_backend", "KrakenCcxtBackend"),
}


def get_backend(backend_id: str, **kwargs: Any) -> Any:
    """
    Lazy factory for provider backends (e.g. kraken_ccxt).

    This function must remain importable without optional dependencies.
    The optional dependency is only required when the provider backend actually
    performs an operation that needs it (e.g. KrakenCcxtBackend._exchange()).
    """
    backend_norm = str(backend_id).strip().lower()
    if backend_norm not in REGISTRY:
        raise KeyError(f"Unknown backend_id: {backend_norm}. Available: {sorted(REGISTRY.keys())}")

    module_name, class_name = REGISTRY[backend_norm]
    import importlib

    mod = importlib.import_module(module_name)
    cls = getattr(mod, class_name)
    return cls(**kwargs)


__all__ = [
    "DataBackend",
    "PandasBackend",
    "PolarsBackend",
    "DuckDBBackend",
    "build_data_backend_from_config",
    "REGISTRY",
    "get_backend",
]
