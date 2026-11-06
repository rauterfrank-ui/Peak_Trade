from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple, Union

from .errors import LakeExecuteError, LakeQueryError

logger = logging.getLogger(__name__)


class LakeClient:
    """
    Minimal DuckDB-backed client for local, read-only friendly analytics.

    Notes:
    - This client is used by OTel instrumentation tests under `tests/obs/test_otel.py`.
    - It is intentionally small: query/execute/register parquet helpers + DataFrame ingest.
    - No network, no secrets, no trading paths.
    """

    def __init__(self, database: str = ":memory:") -> None:
        try:
            import duckdb  # type: ignore
        except ImportError as e:
            raise ImportError("duckdb is required for LakeClient") from e

        self._duckdb = duckdb
        self._database = database
        self._conn = duckdb.connect(database=database)

    @property
    def database(self) -> str:
        return self._database

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    def execute(self, sql: str) -> None:
        try:
            self._conn.execute(sql)
        except Exception as e:
            raise LakeExecuteError(str(e)) from e

    def query(self, sql: str) -> List[Tuple[Any, ...]]:
        try:
            cur = self._conn.execute(sql)
            return cur.fetchall()
        except Exception as e:
            raise LakeQueryError(str(e)) from e

    def register_parquet_file(self, file_path: Union[str, Path], table_name: str) -> None:
        path = str(file_path)
        sql = f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{path}')"
        self.execute(sql)

    def register_parquet_folder(
        self,
        folder_path: Union[str, Path],
        table_name: str,
        glob_pattern: str = "**/*.parquet",
    ) -> None:
        folder = Path(folder_path)
        pattern = str(folder / glob_pattern)
        sql = f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{pattern}')"
        self.execute(sql)

    def create_table_from_df(
        self,
        df: Any,
        table_name: str,
        if_exists: str = "replace",
    ) -> None:
        """
        Create a DuckDB table from a pandas DataFrame.

        Args:
            df: pandas.DataFrame-like.
            table_name: target table name.
            if_exists: "replace" (default) or "append".
        """
        try:
            # DuckDB can query from a registered DataFrame reference.
            self._conn.register("_pt_df", df)
            if if_exists == "append":
                self._conn.execute(f"INSERT INTO {table_name} SELECT * FROM _pt_df")
            else:
                self._conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM _pt_df")
        except Exception as e:
            raise LakeExecuteError(str(e)) from e
        finally:
            try:
                self._conn.unregister("_pt_df")
            except Exception:
                pass
