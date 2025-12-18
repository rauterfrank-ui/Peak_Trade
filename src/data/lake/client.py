"""
Data Lake Client
================
Minimal LakeClient for DuckDB + Parquet operations.

Features:
- Optional dependency on duckdb + pyarrow (graceful degradation)
- Create/open database connections
- Register parquet folders/tables
- Execute SQL queries and return DataFrames
- Clean, typed API

Usage:
    from src.data.lake import LakeClient, is_lake_available

    if not is_lake_available():
        print("Lake features disabled - install duckdb")
    else:
        client = LakeClient(":memory:")
        client.register_parquet_folder("data/cache/", "ohlcv")
        df = client.query("SELECT * FROM ohlcv LIMIT 10")
"""

import warnings
from pathlib import Path
from typing import Optional, Union

from .errors import LakeNotAvailableError, LakeConnectionError, LakeQueryError

# Optional imports - graceful degradation
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    duckdb = None  # type: ignore

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None  # type: ignore


def is_lake_available() -> bool:
    """
    Check if data lake features are available.

    Returns:
        True if duckdb and pandas are installed, False otherwise.
    """
    return DUCKDB_AVAILABLE and PANDAS_AVAILABLE


class LakeClient:
    """
    Minimal DuckDB client for data lake operations.

    Provides:
    - Connection management (in-memory or persistent)
    - Parquet folder/file registration
    - SQL query execution with DataFrame results
    - Graceful error handling

    Args:
        db_path: Path to database file, or ":memory:" for in-memory database.
                 Defaults to ":memory:".
        read_only: If True, open database in read-only mode. Defaults to False.

    Raises:
        LakeNotAvailableError: If duckdb or pandas not installed.
        LakeConnectionError: If database connection fails.

    Example:
        >>> client = LakeClient(":memory:")
        >>> client.register_parquet_folder("data/", "my_table")
        >>> df = client.query("SELECT * FROM my_table LIMIT 10")
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        read_only: bool = False,
    ):
        if not is_lake_available():
            raise LakeNotAvailableError()

        self._db_path = db_path
        self._read_only = read_only
        self._connection: Optional["duckdb.DuckDBPyConnection"] = None

        try:
            self._connection = duckdb.connect(
                database=db_path,
                read_only=read_only,
            )
        except Exception as e:
            raise LakeConnectionError(
                f"Failed to connect to database '{db_path}': {e}"
            ) from e

    def __enter__(self) -> "LakeClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes connection."""
        self.close()

    def close(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception as e:
                warnings.warn(f"Error closing connection: {e}")
            finally:
                self._connection = None

    def register_parquet_folder(
        self,
        folder_path: Union[str, Path],
        table_name: str,
        glob_pattern: str = "**/*.parquet",
    ) -> None:
        """
        Register all parquet files in a folder as a single table.

        DuckDB will scan all matching files and union them into one virtual table.

        Args:
            folder_path: Path to folder containing parquet files.
            table_name: Name to register the table as.
            glob_pattern: Glob pattern for matching files. Default: "**/*.parquet"

        Raises:
            LakeConnectionError: If connection is closed.
            LakeQueryError: If registration fails.

        Example:
            >>> client.register_parquet_folder("data/cache/", "ohlcv")
            >>> df = client.query("SELECT COUNT(*) FROM ohlcv")
        """
        if self._connection is None:
            raise LakeConnectionError("Connection is closed")

        folder_path = Path(folder_path).resolve()
        pattern = str(folder_path / glob_pattern)

        try:
            # Use DuckDB's read_parquet with glob pattern
            sql = f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{pattern}')"
            self._connection.execute(sql)
        except Exception as e:
            raise LakeQueryError(
                f"Failed to register parquet folder '{folder_path}' as '{table_name}': {e}"
            ) from e

    def register_parquet_file(
        self,
        file_path: Union[str, Path],
        table_name: str,
    ) -> None:
        """
        Register a single parquet file as a table.

        Args:
            file_path: Path to parquet file.
            table_name: Name to register the table as.

        Raises:
            LakeConnectionError: If connection is closed.
            LakeQueryError: If registration fails.

        Example:
            >>> client.register_parquet_file("data/ohlcv.parquet", "ohlcv")
            >>> df = client.query("SELECT * FROM ohlcv LIMIT 10")
        """
        if self._connection is None:
            raise LakeConnectionError("Connection is closed")

        file_path = Path(file_path).resolve()

        if not file_path.exists():
            raise LakeQueryError(f"Parquet file not found: {file_path}")

        try:
            sql = f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{file_path}')"
            self._connection.execute(sql)
        except Exception as e:
            raise LakeQueryError(
                f"Failed to register parquet file '{file_path}' as '{table_name}': {e}"
            ) from e

    def query(self, sql: str) -> "pd.DataFrame":
        """
        Execute a SQL query and return results as a DataFrame.

        Args:
            sql: SQL query string.

        Returns:
            pandas DataFrame with query results.

        Raises:
            LakeConnectionError: If connection is closed.
            LakeQueryError: If query execution fails.

        Example:
            >>> df = client.query("SELECT symbol, COUNT(*) as n FROM ohlcv GROUP BY symbol")
        """
        if self._connection is None:
            raise LakeConnectionError("Connection is closed")

        try:
            result = self._connection.execute(sql)
            return result.df()
        except Exception as e:
            raise LakeQueryError(f"Query failed: {e}\nSQL: {sql}") from e

    def execute(self, sql: str) -> None:
        """
        Execute a SQL statement without returning results.

        Useful for DDL statements (CREATE TABLE, INSERT, etc.).

        Args:
            sql: SQL statement string.

        Raises:
            LakeConnectionError: If connection is closed.
            LakeQueryError: If execution fails.

        Example:
            >>> client.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        """
        if self._connection is None:
            raise LakeConnectionError("Connection is closed")

        try:
            self._connection.execute(sql)
        except Exception as e:
            raise LakeQueryError(f"Execute failed: {e}\nSQL: {sql}") from e

    def create_table_from_df(
        self,
        df: "pd.DataFrame",
        table_name: str,
        if_exists: str = "replace",
    ) -> None:
        """
        Create a table from a pandas DataFrame.

        Args:
            df: pandas DataFrame.
            table_name: Name for the new table.
            if_exists: What to do if table exists: 'replace' or 'append'.
                      Default: 'replace'.

        Raises:
            LakeConnectionError: If connection is closed.
            LakeQueryError: If table creation fails.

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
            >>> client.create_table_from_df(df, "test_table")
        """
        if self._connection is None:
            raise LakeConnectionError("Connection is closed")

        if if_exists not in ("replace", "append"):
            raise ValueError(f"if_exists must be 'replace' or 'append', got: {if_exists}")

        try:
            # DuckDB can directly create tables from pandas DataFrames
            if if_exists == "replace":
                self._connection.execute(f"DROP TABLE IF EXISTS {table_name}")
                self._connection.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
            else:  # append
                self._connection.execute(f"INSERT INTO {table_name} SELECT * FROM df")
        except Exception as e:
            raise LakeQueryError(
                f"Failed to create table '{table_name}' from DataFrame: {e}"
            ) from e

    @property
    def is_closed(self) -> bool:
        """Check if connection is closed."""
        return self._connection is None

    @property
    def db_path(self) -> str:
        """Get database path."""
        return self._db_path

    def __repr__(self) -> str:
        status = "closed" if self.is_closed else "open"
        return f"LakeClient(db_path='{self._db_path}', status='{status}')"
