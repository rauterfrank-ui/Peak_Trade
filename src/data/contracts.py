"""
Data Contracts: Strict validation for OHLCV DataFrames.

Wave A (Stability & Resilience Plan): Data Contract Gate
=========================================================
Provides strict validation of OHLCV data to ensure correctness and determinism.

Usage:
    from src.data.contracts import validate_ohlcv

    # Basic validation
    validate_ohlcv(df)

    # Strict validation (fail on NaNs, unsorted, duplicates, etc.)
    validate_ohlcv(df, strict=True, require_tz=True)
"""

from typing import Optional

import pandas as pd

from . import REQUIRED_OHLCV_COLUMNS
from src.core.errors import DataContractError


def validate_ohlcv(
    df: pd.DataFrame,
    strict: bool = True,
    require_tz: bool = True,
    allow_partial_nans: bool = False,
) -> None:
    """
    Validates an OHLCV DataFrame against the Peak_Trade data contract.

    Args:
        df: DataFrame to validate
        strict: If True, enforce strict validation (no NaNs, sorted, no duplicates)
        require_tz: If True, require timezone-aware DatetimeIndex
        allow_partial_nans: If True, allow NaNs in volume (common in some sources)

    Raises:
        DataContractError: If validation fails

    Validation Rules:
        1. Index must be DatetimeIndex
        2. If require_tz: Index must be timezone-aware
        3. Must contain all REQUIRED_OHLCV_COLUMNS
        4. If strict:
            - Index must be sorted (ascending)
            - No duplicate timestamps
            - No NaNs in OHLC (volume allowed if allow_partial_nans=True)
            - All columns must be numeric (float/int, not object)
            - open/high/low/close must be > 0
            - high >= low
            - volume >= 0
    """
    # Rule 1: DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        raise DataContractError(
            f"Index must be DatetimeIndex, got: {type(df.index).__name__}",
            hint="Ensure the index is converted to datetime before validation",
            context={"index_type": type(df.index).__name__},
        )

    # Rule 2: Timezone-aware
    if require_tz and df.index.tz is None:
        raise DataContractError(
            "Index must be timezone-aware (require_tz=True)",
            hint="Use df.index.tz_localize('UTC') or df.index.tz_convert('UTC')",
            context={"index_tz": str(df.index.tz)},
        )

    # Rule 3: Required columns
    missing_cols = set(REQUIRED_OHLCV_COLUMNS) - set(df.columns)
    if missing_cols:
        raise DataContractError(
            f"Missing required OHLCV columns: {sorted(missing_cols)}",
            hint=f"Required columns: {REQUIRED_OHLCV_COLUMNS}",
            context={
                "missing_columns": sorted(missing_cols),
                "available_columns": sorted(df.columns.tolist()),
            },
        )

    if not strict:
        return  # Basic validation passed

    # STRICT MODE: Additional checks
    # Rule 4: Sorted index
    if not df.index.is_monotonic_increasing:
        raise DataContractError(
            "Index must be sorted in ascending order (strict=True)",
            hint="Use df.sort_index() before validation",
            context={"is_sorted": False},
        )

    # Rule 5: No duplicates
    if df.index.duplicated().any():
        dup_indices = df.index[df.index.duplicated()].tolist()
        raise DataContractError(
            f"Index contains {len(dup_indices)} duplicate timestamps (strict=True)",
            hint="Use df[~df.index.duplicated(keep='last')] to remove duplicates",
            context={
                "duplicate_count": len(dup_indices),
                "duplicate_timestamps": [str(ts) for ts in dup_indices[:5]],  # First 5
            },
        )

    # Coerce numeric strings to numeric for checks (pandas 3 / pyarrow string columns)
    _df = df.copy()
    for col in REQUIRED_OHLCV_COLUMNS:
        d = _df[col].dtype
        if getattr(d, "kind", None) in ("O", "U", "S"):
            _df[col] = pd.to_numeric(_df[col], errors="coerce")

    # Rule 6: Check for object dtypes or non-numeric strings (all NaN after coerce)
    object_cols = [
        col
        for col in REQUIRED_OHLCV_COLUMNS
        if _df[col].dtype.kind not in ("i", "u", "f", "c") or _df[col].isna().all()
    ]
    if object_cols:
        raise DataContractError(
            f"Columns have object dtype or non-numeric values (strict=True): {object_cols}",
            hint="Ensure columns are numeric. Use pd.to_numeric() or astype(float)",
            context={"object_columns": object_cols},
        )

    # Rule 7: Check for NaNs
    nan_cols = []
    for col in REQUIRED_OHLCV_COLUMNS:
        if col == "volume" and allow_partial_nans:
            continue
        if _df[col].isna().any():
            nan_cols.append(col)

    if nan_cols:
        raise DataContractError(
            f"Columns contain NaN values (strict=True): {nan_cols}",
            hint="Fill or drop NaNs before validation",
            context={
                "nan_columns": nan_cols,
                "nan_counts": {col: int(_df[col].isna().sum()) for col in nan_cols},
            },
        )

    # Rule 8: OHLC values must be positive
    for col in ["open", "high", "low", "close"]:
        if (_df[col] <= 0).any():
            bad_rows = _df[_df[col] <= 0].index.tolist()
            raise DataContractError(
                f"Column '{col}' contains non-positive values (strict=True)",
                hint="OHLC prices must be > 0",
                context={
                    "column": col,
                    "bad_row_count": len(bad_rows),
                    "bad_timestamps": [str(ts) for ts in bad_rows[:5]],
                },
            )

    # Rule 9: high >= low
    if (_df["high"] < _df["low"]).any():
        bad_rows = _df[_df["high"] < _df["low"]].index.tolist()
        raise DataContractError(
            "high < low detected (strict=True)",
            hint="Check data source for corruption",
            context={
                "bad_row_count": len(bad_rows),
                "bad_timestamps": [str(ts) for ts in bad_rows[:5]],
            },
        )

    # Rule 10: volume >= 0
    if (_df["volume"] < 0).any():
        bad_rows = _df[_df["volume"] < 0].index.tolist()
        raise DataContractError(
            "Volume contains negative values (strict=True)",
            hint="Volume must be >= 0",
            context={
                "bad_row_count": len(bad_rows),
                "bad_timestamps": [str(ts) for ts in bad_rows[:5]],
            },
        )
