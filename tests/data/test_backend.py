"""
Tests für Data Backend Layer (src/data/backend.py)
==================================================
Testet PandasBackend, PolarsBackend (optional), DuckDBBackend (optional).

NOTE: src/data/backend.py nicht implementiert - deferred to future phase
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Skip all tests in this module if backend doesn't exist
pytest.skip("src.data.backend not implemented yet", allow_module_level=True)

from src.data.backend import (
    DataBackend,
    DuckDBBackend,
    PandasBackend,
    PolarsBackend,
    build_data_backend_from_config,
)


# ============================================================================
# Helpers
# ============================================================================


def _is_polars_available() -> bool:
    """Prüft ob polars installiert ist."""
    try:
        import polars  # noqa: F401

        return True
    except ImportError:
        return False


def _is_duckdb_available() -> bool:
    """Prüft ob duckdb installiert ist."""
    try:
        import duckdb  # noqa: F401

        return True
    except ImportError:
        return False


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_df():
    """Sample pandas DataFrame für Tests."""
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2023-01-01", periods=10, freq="1h"),
            "open": [100.0 + i for i in range(10)],
            "high": [101.0 + i for i in range(10)],
            "low": [99.0 + i for i in range(10)],
            "close": [100.5 + i for i in range(10)],
            "volume": [1000 + i * 10 for i in range(10)],
        }
    )


@pytest.fixture
def temp_parquet_file(sample_df, tmp_path):
    """Temporäre Parquet-Datei für Tests."""
    parquet_path = tmp_path / "test_data.parquet"
    sample_df.to_parquet(parquet_path, index=False)
    return parquet_path


# ============================================================================
# Tests: PandasBackend (Default)
# ============================================================================


def test_pandas_backend_name():
    """PandasBackend hat korrekten Namen."""
    backend = PandasBackend()
    assert backend.name == "pandas"


def test_pandas_backend_to_pandas_idempotent(sample_df):
    """PandasBackend.to_pandas() ist idempotent für pandas DataFrames."""
    backend = PandasBackend()
    result = backend.to_pandas(sample_df)

    assert isinstance(result, pd.DataFrame)
    assert result is sample_df  # Same object


def test_pandas_backend_read_parquet(temp_parquet_file, sample_df):
    """PandasBackend kann Parquet lesen."""
    backend = PandasBackend()
    df = backend.read_parquet(temp_parquet_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(sample_df)
    assert list(df.columns) == list(sample_df.columns)


def test_pandas_backend_read_parquet_not_found():
    """PandasBackend wirft FileNotFoundError bei fehlender Datei."""
    backend = PandasBackend()

    with pytest.raises(FileNotFoundError, match="not found"):
        backend.read_parquet("nonexistent.parquet")


def test_pandas_backend_to_pandas_invalid_type():
    """PandasBackend.to_pandas() wirft TypeError bei ungültigem Typ."""
    backend = PandasBackend()

    with pytest.raises(TypeError, match="Cannot convert"):
        backend.to_pandas([1, 2, 3])  # Liste ist nicht kompatibel


# ============================================================================
# Tests: PolarsBackend (Optional)
# ============================================================================


def test_polars_backend_installation_guard():
    """PolarsBackend wirft RuntimeError wenn polars nicht installiert."""
    # Dieser Test prüft nur, dass ein ImportError korrekt behandelt wird
    try:
        import polars  # noqa: F401

        pytest.skip("polars ist installiert, Test nicht relevant")
    except ImportError:
        # polars nicht installiert → Backend sollte RuntimeError werfen
        with pytest.raises(RuntimeError, match="polars not installed"):
            PolarsBackend()


@pytest.mark.skipif(
    condition=not _is_polars_available(),
    reason="polars nicht installiert",
)
def test_polars_backend_name():
    """PolarsBackend hat korrekten Namen."""
    backend = PolarsBackend()
    assert backend.name == "polars"


@pytest.mark.skipif(
    condition=not _is_polars_available(),
    reason="polars nicht installiert",
)
def test_polars_backend_to_pandas_from_polars():
    """PolarsBackend kann polars DataFrame zu pandas konvertieren."""
    import polars as pl

    backend = PolarsBackend()

    # Polars DataFrame erstellen
    df_polars = pl.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [4.0, 5.0, 6.0],
        }
    )

    # Konvertiere zu pandas
    df_pandas = backend.to_pandas(df_polars)

    assert isinstance(df_pandas, pd.DataFrame)
    assert len(df_pandas) == 3
    assert list(df_pandas.columns) == ["a", "b"]


@pytest.mark.skipif(
    condition=not _is_polars_available(),
    reason="polars nicht installiert",
)
def test_polars_backend_to_pandas_already_pandas(sample_df):
    """PolarsBackend.to_pandas() ist idempotent für pandas DataFrames."""
    backend = PolarsBackend()
    result = backend.to_pandas(sample_df)

    assert isinstance(result, pd.DataFrame)
    assert result is sample_df  # Same object


@pytest.mark.skipif(
    condition=not _is_polars_available(),
    reason="polars nicht installiert",
)
def test_polars_backend_read_parquet(temp_parquet_file, sample_df):
    """PolarsBackend kann Parquet lesen (schneller als pandas)."""
    backend = PolarsBackend()
    df = backend.read_parquet(temp_parquet_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(sample_df)


# ============================================================================
# Tests: DuckDBBackend (Optional)
# ============================================================================


def test_duckdb_backend_installation_guard():
    """DuckDBBackend wirft RuntimeError wenn duckdb nicht installiert."""
    try:
        import duckdb  # noqa: F401

        pytest.skip("duckdb ist installiert, Test nicht relevant")
    except ImportError:
        # duckdb nicht installiert → Backend sollte RuntimeError werfen
        with pytest.raises(RuntimeError, match="duckdb not installed"):
            DuckDBBackend()


@pytest.mark.skipif(
    condition=not _is_duckdb_available(),
    reason="duckdb nicht installiert",
)
def test_duckdb_backend_name():
    """DuckDBBackend hat korrekten Namen."""
    backend = DuckDBBackend()
    assert backend.name == "duckdb"


@pytest.mark.skipif(
    condition=not _is_duckdb_available(),
    reason="duckdb nicht installiert",
)
def test_duckdb_backend_to_pandas_already_pandas(sample_df):
    """DuckDBBackend.to_pandas() ist idempotent für pandas DataFrames."""
    backend = DuckDBBackend()
    result = backend.to_pandas(sample_df)

    assert isinstance(result, pd.DataFrame)
    assert result is sample_df  # Same object


@pytest.mark.skipif(
    condition=not _is_duckdb_available(),
    reason="duckdb nicht installiert",
)
def test_duckdb_backend_read_parquet(temp_parquet_file, sample_df):
    """DuckDBBackend kann Parquet lesen (sehr schnell)."""
    backend = DuckDBBackend()
    df = backend.read_parquet(temp_parquet_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(sample_df)


@pytest.mark.skipif(
    condition=not _is_duckdb_available(),
    reason="duckdb nicht installiert",
)
def test_duckdb_backend_read_parquet_not_found():
    """DuckDBBackend wirft FileNotFoundError bei fehlender Datei."""
    backend = DuckDBBackend()

    with pytest.raises(FileNotFoundError, match="not found"):
        backend.read_parquet("nonexistent.parquet")


# ============================================================================
# Tests: Factory (build_data_backend_from_config)
# ============================================================================


def test_build_backend_default_pandas():
    """Factory erstellt PandasBackend als Default."""

    class MockConfig:
        def get(self, key, default=None):
            return default

    backend = build_data_backend_from_config(MockConfig())

    assert isinstance(backend, PandasBackend)
    assert backend.name == "pandas"


def test_build_backend_explicit_pandas():
    """Factory erstellt PandasBackend wenn explizit konfiguriert."""

    class MockConfig:
        def get(self, key, default=None):
            if key == "data.backend":
                return "pandas"
            return default

    backend = build_data_backend_from_config(MockConfig())

    assert isinstance(backend, PandasBackend)


@pytest.mark.skipif(
    condition=not _is_polars_available(),
    reason="polars nicht installiert",
)
def test_build_backend_polars():
    """Factory erstellt PolarsBackend wenn konfiguriert."""

    class MockConfig:
        def get(self, key, default=None):
            if key == "data.backend":
                return "polars"
            return default

    backend = build_data_backend_from_config(MockConfig())

    assert isinstance(backend, PolarsBackend)
    assert backend.name == "polars"


@pytest.mark.skipif(
    condition=not _is_duckdb_available(),
    reason="duckdb nicht installiert",
)
def test_build_backend_duckdb():
    """Factory erstellt DuckDBBackend wenn konfiguriert."""

    class MockConfig:
        def get(self, key, default=None):
            if key == "data.backend":
                return "duckdb"
            return default

    backend = build_data_backend_from_config(MockConfig())

    assert isinstance(backend, DuckDBBackend)
    assert backend.name == "duckdb"


def test_build_backend_invalid():
    """Factory wirft ValueError bei unbekanntem Backend."""

    class MockConfig:
        def get(self, key, default=None):
            if key == "data.backend":
                return "invalid_backend"
            return default

    with pytest.raises(ValueError, match="Unknown data backend"):
        build_data_backend_from_config(MockConfig())


def test_build_backend_polars_not_installed():
    """Factory wirft RuntimeError wenn polars gewünscht aber nicht installiert."""
    try:
        import polars  # noqa: F401

        pytest.skip("polars ist installiert, Test nicht relevant")
    except ImportError:
        pass

    class MockConfig:
        def get(self, key, default=None):
            if key == "data.backend":
                return "polars"
            return default

    with pytest.raises(RuntimeError, match="polars not installed"):
        build_data_backend_from_config(MockConfig())


def test_build_backend_duckdb_not_installed():
    """Factory wirft RuntimeError wenn duckdb gewünscht aber nicht installiert."""
    try:
        import duckdb  # noqa: F401

        pytest.skip("duckdb ist installiert, Test nicht relevant")
    except ImportError:
        pass

    class MockConfig:
        def get(self, key, default=None):
            if key == "data.backend":
                return "duckdb"
            return default

    with pytest.raises(RuntimeError, match="duckdb not installed"):
        build_data_backend_from_config(MockConfig())
