"""
Data Lake Error Types
======================
Custom exceptions for data lake operations.
"""


class LakeNotAvailableError(Exception):
    """
    Raised when DuckDB is not installed or lake features are unavailable.

    This is a graceful degradation error - the system can continue
    without data lake functionality.
    """

    def __init__(self, message: str = None):
        if message is None:
            message = (
                "Data lake features are not available. "
                "Install optional dependencies: pip install 'peak_trade[lake]' "
                "or pip install duckdb pyarrow"
            )
        super().__init__(message)


class LakeConnectionError(Exception):
    """Raised when connection to DuckDB database fails."""
    pass


class LakeQueryError(Exception):
    """Raised when a SQL query execution fails."""
    pass
