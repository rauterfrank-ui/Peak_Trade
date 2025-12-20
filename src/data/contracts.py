"""
Data Contracts: Strict validation for OHLCV DataFrames.

Wave A (Stability & Resilience Plan): Data Contract Gate
=========================================================
Provides strict validation of OHLCV data to ensure correctness and determinism.

Usage:
    from src.data.contracts import validate_ohlcv, OHLCVContract, StrictnessLevel

    # Basic validation (returns tuple)
    is_valid, errors = validate_ohlcv(df, strict=True, require_tz=True)
    
    # Using OHLCVContract class
    contract = OHLCVContract(strictness=StrictnessLevel.STRICT)
    is_valid, errors = contract.validate(df)
    
    # Check-based validation (raises exception)
    from src.data.contracts import check_ohlcv
    check_ohlcv(df, strict=True)  # Raises DataContractError if invalid
"""
from enum import Enum
from typing import Optional
import logging

import pandas as pd

from . import REQUIRED_OHLCV_COLUMNS
from src.core.errors import DataContractError

logger = logging.getLogger(__name__)

# Contract version for cache manifest
CONTRACT_VERSION = "1.0.0"

# Optional columns that can be validated if present
OPTIONAL_OHLCV_COLUMNS = ["trades", "vwap"]


class StrictnessLevel(Enum):
    """
    Validation strictness levels.
    
    PERMISSIVE: Only check required columns and basic types
    NORMAL: PERMISSIVE + check for sorted data and basic constraints
    STRICT: NORMAL + check for NaNs, duplicates, OHLC relationships
    """
    PERMISSIVE = "permissive"
    NORMAL = "normal"
    STRICT = "strict"


class OHLCVContract:
    """
    OHLCV Data Contract with configurable strictness.
    
    Attributes:
        strictness: Validation strictness level
        require_tz: Require timezone-aware index
        allow_partial_nans: Allow NaNs in volume column
        check_ohlc_relationships: Check high>=open/close/low, low<=open/close
        optional_columns: Additional columns to validate if present
        
    Example:
        >>> contract = OHLCVContract(strictness=StrictnessLevel.STRICT)
        >>> is_valid, errors = contract.validate(df)
        >>> if not is_valid:
        ...     print(f"Validation failed: {errors}")
    """
    
    def __init__(
        self,
        strictness: StrictnessLevel = StrictnessLevel.STRICT,
        require_tz: bool = True,
        allow_partial_nans: bool = False,
        check_ohlc_relationships: bool = True,
        optional_columns: Optional[list[str]] = None,
    ):
        self.strictness = strictness
        self.require_tz = require_tz
        self.allow_partial_nans = allow_partial_nans
        self.check_ohlc_relationships = check_ohlc_relationships
        self.optional_columns = optional_columns or []
        self.version = CONTRACT_VERSION
    
    def validate(self, df: pd.DataFrame) -> tuple[bool, list[str]]:
        """
        Validate DataFrame against contract.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (is_valid, errors) where errors contains human-readable messages
        """
        return validate_ohlcv(
            df,
            strict=(self.strictness == StrictnessLevel.STRICT),
            require_tz=self.require_tz,
            allow_partial_nans=self.allow_partial_nans,
            check_ohlc_relationships=self.check_ohlc_relationships,
            strictness_level=self.strictness,
        )


def validate_ohlcv(
    df: pd.DataFrame,
    *,
    strict: bool = True,
    require_tz: bool = True,
    allow_partial_nans: bool = False,
    check_ohlc_relationships: bool = True,
    strictness_level: Optional[StrictnessLevel] = None,
) -> tuple[bool, list[str]]:
    """
    Validate OHLCV DataFrame against contract.
    
    Args:
        df: DataFrame to validate
        strict: If True, enforce strict validation (no NaNs, sorted, no duplicates)
        require_tz: If True, require timezone-aware DatetimeIndex
        allow_partial_nans: If True, allow NaNs in volume (common in some sources)
        check_ohlc_relationships: If True, check OHLC price relationships
        strictness_level: Override strict mode with explicit strictness level
        
    Returns:
        Tuple of (is_valid, errors) where errors contains human-readable messages
        
    Validation Rules:
        1. Index must be DatetimeIndex
        2. If require_tz: Index must be timezone-aware
        3. Must contain all REQUIRED_OHLCV_COLUMNS
        4. Depending on strictness level:
           PERMISSIVE: Rules 1-3 only
           NORMAL: + sorted index, positive values, high >= low
           STRICT: + no duplicates, no NaNs, OHLC relationships, numeric dtypes
    
    Example:
        >>> is_valid, errors = validate_ohlcv(df, strict=True, require_tz=True)
        >>> if not is_valid:
        ...     raise DataContractError(
        ...         f"OHLCV validation failed: {errors[0]}",
        ...         hint="Check data source for corruption",
        ...         context={"errors": errors}
        ...     )
    """
    errors = []
    
    # Determine effective strictness level
    if strictness_level is None:
        if strict:
            strictness_level = StrictnessLevel.STRICT
        else:
            strictness_level = StrictnessLevel.PERMISSIVE
    
    # Empty DataFrame check
    if df.empty:
        errors.append("DataFrame is empty")
        return False, errors
    
    # Rule 1: DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        errors.append(
            f"Index must be DatetimeIndex, got: {type(df.index).__name__}. "
            "Hint: Ensure the index is converted to datetime before validation"
        )
        return False, errors

    # Rule 2: Timezone-aware
    if require_tz and df.index.tz is None:
        errors.append(
            "Index must be timezone-aware (require_tz=True). "
            "Hint: Use df.index.tz_localize('UTC') or df.index.tz_convert('UTC')"
        )
        return False, errors

    # Rule 3: Required columns
    missing_cols = set(REQUIRED_OHLCV_COLUMNS) - set(df.columns)
    if missing_cols:
        errors.append(
            f"Missing required OHLCV columns: {sorted(missing_cols)}. "
            f"Hint: Required columns are {REQUIRED_OHLCV_COLUMNS}"
        )
        return False, errors

    # PERMISSIVE: Stop here
    if strictness_level == StrictnessLevel.PERMISSIVE:
        return True, []

    # NORMAL and STRICT: Additional checks
    
    # Rule 4: Check for object dtypes first (before numeric comparisons)
    object_cols = [col for col in REQUIRED_OHLCV_COLUMNS if df[col].dtype == object]
    if object_cols:
        errors.append(
            f"Columns have object dtype: {object_cols}. "
            "Hint: Ensure columns are numeric. Use pd.to_numeric() or astype(float)"
        )
        # Return early if object dtypes found - can't do numeric checks
        return False, errors
    
    # Rule 5: Sorted index
    if not df.index.is_monotonic_increasing:
        errors.append(
            "Index must be sorted in ascending order. "
            "Hint: Use df.sort_index() before validation"
        )

    # Rule 6: OHLC values must be positive
    for col in ["open", "high", "low", "close"]:
        if (df[col] <= 0).any():
            bad_count = (df[col] <= 0).sum()
            errors.append(
                f"Column '{col}' contains {bad_count} non-positive value(s). "
                "Hint: OHLC prices must be > 0"
            )

    # Rule 7: high >= low
    if (df["high"] < df["low"]).any():
        bad_count = (df["high"] < df["low"]).sum()
        errors.append(
            f"Found {bad_count} row(s) where high < low. "
            "Hint: Check data source for corruption"
        )

    # Rule 8: volume >= 0
    if (df["volume"] < 0).any():
        bad_count = (df["volume"] < 0).sum()
        errors.append(
            f"Volume contains {bad_count} negative value(s). "
            "Hint: Volume must be >= 0"
        )

    # STRICT only: More rigorous checks
    if strictness_level == StrictnessLevel.STRICT:
        
        # Rule 9: No duplicates
        if df.index.duplicated().any():
            dup_count = df.index.duplicated().sum()
            errors.append(
                f"Index contains {dup_count} duplicate timestamp(s). "
                "Hint: Use df[~df.index.duplicated(keep='last')] to remove duplicates"
            )

        # Rule 10: Check for NaNs
        nan_cols = []
        for col in REQUIRED_OHLCV_COLUMNS:
            if col == "volume" and allow_partial_nans:
                continue
            if df[col].isna().any():
                nan_count = df[col].isna().sum()
                nan_cols.append(f"{col} ({nan_count} NaNs)")

        if nan_cols:
            errors.append(
                f"Columns contain NaN values: {', '.join(nan_cols)}. "
                "Hint: Fill or drop NaNs before validation"
            )
        
        # Rule 11: OHLC relationships (if enabled)
        if check_ohlc_relationships:
            # high >= open
            if (df["high"] < df["open"]).any():
                bad_count = (df["high"] < df["open"]).sum()
                errors.append(
                    f"Found {bad_count} row(s) where high < open. "
                    "Hint: Check data integrity"
                )
            
            # high >= close
            if (df["high"] < df["close"]).any():
                bad_count = (df["high"] < df["close"]).sum()
                errors.append(
                    f"Found {bad_count} row(s) where high < close. "
                    "Hint: Check data integrity"
                )
            
            # low <= open
            if (df["low"] > df["open"]).any():
                bad_count = (df["low"] > df["open"]).sum()
                errors.append(
                    f"Found {bad_count} row(s) where low > open. "
                    "Hint: Check data integrity"
                )
            
            # low <= close
            if (df["low"] > df["close"]).any():
                bad_count = (df["low"] > df["close"]).sum()
                errors.append(
                    f"Found {bad_count} row(s) where low > close. "
                    "Hint: Check data integrity"
                )
    
    # Return validation result
    is_valid = len(errors) == 0
    return is_valid, errors


def check_ohlcv(
    df: pd.DataFrame,
    *,
    strict: bool = True,
    require_tz: bool = True,
    allow_partial_nans: bool = False,
    check_ohlc_relationships: bool = True,
) -> None:
    """
    Validate OHLCV DataFrame and raise exception if invalid.
    
    This is a convenience wrapper around validate_ohlcv that raises
    DataContractError instead of returning a tuple.
    
    Args:
        df: DataFrame to validate
        strict: If True, enforce strict validation
        require_tz: If True, require timezone-aware DatetimeIndex
        allow_partial_nans: If True, allow NaNs in volume
        check_ohlc_relationships: If True, check OHLC price relationships
        
    Raises:
        DataContractError: If validation fails
        
    Example:
        >>> from src.data.contracts import check_ohlcv
        >>> check_ohlcv(df, strict=True)  # Raises if invalid
    """
    is_valid, errors = validate_ohlcv(
        df,
        strict=strict,
        require_tz=require_tz,
        allow_partial_nans=allow_partial_nans,
        check_ohlc_relationships=check_ohlc_relationships,
    )
    
    if not is_valid:
        raise DataContractError(
            f"OHLCV validation failed: {errors[0]}",
            hint="Check data source for corruption or schema changes",
            context={
                "errors": errors,
                "shape": df.shape,
                "columns": list(df.columns),
            }
        )
