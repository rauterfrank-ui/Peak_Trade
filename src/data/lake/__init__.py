"""
Peak_Trade Data Lake Module
============================
Optional DuckDB-based data lake for long-term storage and SQL queries.

This module provides graceful degradation when DuckDB is not installed.
"""

from .errors import LakeNotAvailableError, LakeConnectionError, LakeQueryError
from .client import LakeClient, is_lake_available

__all__ = [
    "LakeClient",
    "is_lake_available",
    "LakeNotAvailableError",
    "LakeConnectionError",
    "LakeQueryError",
]
