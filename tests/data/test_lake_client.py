"""
Tests for Data Lake Client (src/data/lake/client.py)
=====================================================

Tests cover:
1. Graceful degradation when duckdb not installed
2. Full functionality when duckdb is installed
3. Connection management (open, close, context manager)
4. Parquet registration (files and folders)
5. SQL query execution
6. DataFrame creation

NOTE: Tests import directly from src.data.lake submodules (not src.data.lake)
to avoid triggering heavy imports in src.data.__init__.py.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Import directly from lake submodules to avoid src.data.__init__.py
from src.data.lake.client import LakeClient, is_lake_available
from src.data.lake.errors import (
    LakeNotAvailableError,
    LakeConnectionError,
    LakeQueryError,
)

# Test if duckdb is available
try:
    import duckdb
    DUCKDB_INSTALLED = True
except ImportError:
    DUCKDB_INSTALLED = False


# ============================================================================
# Test 1: Graceful Degradation (without duckdb)
# ============================================================================


def test_is_lake_available_without_duckdb():
    """Test is_lake_available() returns False when duckdb not installed."""
    if DUCKDB_INSTALLED:
        pytest.skip("duckdb is installed, skipping this test")

    # When duckdb not installed, is_lake_available() should return False
    assert not is_lake_available()


def test_lake_client_raises_without_duckdb():
    """
    Test LakeClient raises clear error when duckdb not installed.

    Note: This test only runs when duckdb is NOT installed.
    When duckdb IS installed, it's skipped.
    """
    if DUCKDB_INSTALLED:
        pytest.skip("duckdb is installed, skipping graceful degradation test")

    # If duckdb is not installed, LakeClient should raise immediately
    with pytest.raises(LakeNotAvailableError) as exc_info:
        LakeClient()

    # Check error message is helpful
    assert "not available" in str(exc_info.value).lower()
    assert "install" in str(exc_info.value).lower()


# ============================================================================
# Test 2: Basic Functionality (with duckdb)
# ============================================================================


@pytest.mark.skipif(not DUCKDB_INSTALLED, reason="duckdb not installed")
class TestLakeClientWithDuckDB:
    """Tests that require duckdb to be installed."""

    def test_create_in_memory_client(self):
        """Test creating an in-memory database client."""
        client = LakeClient(":memory:")
        assert not client.is_closed
        assert client.db_path == ":memory:"
        client.close()
        assert client.is_closed

    def test_context_manager(self):
        """Test LakeClient works as context manager."""
        with LakeClient(":memory:") as client:
            assert not client.is_closed
            result = client.query("SELECT 42 as answer")
            assert result.iloc[0]["answer"] == 42

        # Should be closed after exiting context
        assert client.is_closed

    def test_simple_query(self):
        """Test executing a simple SQL query."""
        with LakeClient(":memory:") as client:
            df = client.query("SELECT 1 as one, 2 as two")
            assert len(df) == 1
            assert df.iloc[0]["one"] == 1
            assert df.iloc[0]["two"] == 2

    def test_create_table_from_dataframe(self):
        """Test creating table from pandas DataFrame (roundtrip)."""
        # Create test DataFrame
        test_df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 30.1],
        })

        with LakeClient(":memory:") as client:
            # Create table
            client.create_table_from_df(test_df, "test_table")

            # Query it back
            result = client.query("SELECT * FROM test_table ORDER BY id")

            # Verify roundtrip
            assert len(result) == 3
            assert list(result["id"]) == [1, 2, 3]
            assert list(result["name"]) == ["Alice", "Bob", "Charlie"]
            assert list(result["value"]) == [10.5, 20.3, 30.1]

    def test_execute_ddl(self):
        """Test executing DDL statements."""
        with LakeClient(":memory:") as client:
            # Create table via execute
            client.execute("CREATE TABLE test (id INTEGER, name TEXT)")

            # Insert data
            client.execute("INSERT INTO test VALUES (1, 'test')")

            # Query back
            result = client.query("SELECT * FROM test")
            assert len(result) == 1
            assert result.iloc[0]["id"] == 1
            assert result.iloc[0]["name"] == "test"

    def test_register_parquet_file(self):
        """Test registering a single parquet file."""
        # Create test parquet file
        test_df = pd.DataFrame({
            "symbol": ["BTC", "ETH", "SOL"],
            "price": [50000.0, 3000.0, 100.0],
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            parquet_path = Path(tmpdir) / "test.parquet"
            test_df.to_parquet(parquet_path)

            with LakeClient(":memory:") as client:
                # Register parquet
                client.register_parquet_file(parquet_path, "crypto")

                # Query it
                result = client.query("SELECT * FROM crypto ORDER BY price")
                assert len(result) == 3
                assert list(result["symbol"]) == ["SOL", "ETH", "BTC"]

    def test_register_parquet_folder(self):
        """Test registering multiple parquet files in a folder."""
        # Create test parquet files
        df1 = pd.DataFrame({"id": [1, 2], "value": [10, 20]})
        df2 = pd.DataFrame({"id": [3, 4], "value": [30, 40]})

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            df1.to_parquet(folder / "file1.parquet")
            df2.to_parquet(folder / "file2.parquet")

            with LakeClient(":memory:") as client:
                # Register folder
                client.register_parquet_folder(folder, "data", glob_pattern="*.parquet")

                # Query across all files
                result = client.query("SELECT * FROM data ORDER BY id")
                assert len(result) == 4
                assert list(result["id"]) == [1, 2, 3, 4]
                assert list(result["value"]) == [10, 20, 30, 40]

    def test_persistent_database(self):
        """Test creating a persistent database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.duckdb")

            # Create database and insert data
            with LakeClient(db_path) as client:
                client.execute("CREATE TABLE test (id INTEGER, name TEXT)")
                client.execute("INSERT INTO test VALUES (1, 'persistent')")

            # Reopen and verify data persisted
            with LakeClient(db_path) as client:
                result = client.query("SELECT * FROM test")
                assert len(result) == 1
                assert result.iloc[0]["name"] == "persistent"

    def test_query_error_handling(self):
        """Test error handling for invalid queries."""
        with LakeClient(":memory:") as client:
            with pytest.raises(LakeQueryError) as exc_info:
                client.query("SELECT * FROM nonexistent_table")

            assert "Query failed" in str(exc_info.value)

    def test_connection_error_handling(self):
        """Test error handling for operations on closed connection."""
        client = LakeClient(":memory:")
        client.close()

        with pytest.raises(LakeConnectionError) as exc_info:
            client.query("SELECT 1")

        assert "closed" in str(exc_info.value).lower()

    def test_if_exists_replace(self):
        """Test if_exists='replace' overwrites existing table."""
        df1 = pd.DataFrame({"id": [1, 2]})
        df2 = pd.DataFrame({"id": [3, 4]})

        with LakeClient(":memory:") as client:
            client.create_table_from_df(df1, "test", if_exists="replace")
            result1 = client.query("SELECT COUNT(*) as n FROM test")
            assert result1.iloc[0]["n"] == 2

            # Replace with new data
            client.create_table_from_df(df2, "test", if_exists="replace")
            result2 = client.query("SELECT * FROM test ORDER BY id")
            assert len(result2) == 2
            assert list(result2["id"]) == [3, 4]

    def test_if_exists_append(self):
        """Test if_exists='append' adds to existing table."""
        df1 = pd.DataFrame({"id": [1, 2]})
        df2 = pd.DataFrame({"id": [3, 4]})

        with LakeClient(":memory:") as client:
            client.create_table_from_df(df1, "test", if_exists="replace")
            client.create_table_from_df(df2, "test", if_exists="append")

            result = client.query("SELECT * FROM test ORDER BY id")
            assert len(result) == 4
            assert list(result["id"]) == [1, 2, 3, 4]


# ============================================================================
# Test 3: Edge Cases
# ============================================================================


@pytest.mark.skipif(not DUCKDB_INSTALLED, reason="duckdb not installed")
def test_register_nonexistent_parquet_file():
    """Test error handling when registering non-existent file."""
    with LakeClient(":memory:") as client:
        with pytest.raises(LakeQueryError) as exc_info:
            client.register_parquet_file("/nonexistent/file.parquet", "test")

        assert "not found" in str(exc_info.value).lower()


@pytest.mark.skipif(not DUCKDB_INSTALLED, reason="duckdb not installed")
def test_is_lake_available_returns_true():
    """Test is_lake_available() returns True when duckdb installed."""
    assert is_lake_available() is True


@pytest.mark.skipif(not DUCKDB_INSTALLED, reason="duckdb not installed")
def test_repr():
    """Test __repr__ method."""
    client = LakeClient(":memory:")
    repr_str = repr(client)
    assert "LakeClient" in repr_str
    assert ":memory:" in repr_str
    assert "open" in repr_str

    client.close()
    repr_str = repr(client)
    assert "closed" in repr_str
