"""
Tests for Data Contract Gate (Wave A - Stability Plan)
"""
import pandas as pd
import pytest

from src.data.contracts import (
    validate_ohlcv,
    check_ohlcv,
    OHLCVContract,
    StrictnessLevel,
    CONTRACT_VERSION,
)
from src.core.errors import DataContractError


@pytest.fixture
def valid_ohlcv_df():
    """Valid OHLCV DataFrame for testing."""
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [105.0, 106.0, 107.0],
            "low": [99.0, 100.0, 101.0],
            "close": [103.0, 104.0, 105.0],
            "volume": [1000.0, 1100.0, 1200.0],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="1h", tz="UTC"),
    )


# ============================================================================
# Tests for validate_ohlcv (tuple return API)
# ============================================================================


@pytest.mark.smoke
def test_validate_ohlcv_valid_strict(valid_ohlcv_df):
    """Valid OHLCV passes strict validation."""
    is_valid, errors = validate_ohlcv(valid_ohlcv_df, strict=True, require_tz=True)
    assert is_valid
    assert errors == []


@pytest.mark.smoke
def test_validate_ohlcv_missing_columns(valid_ohlcv_df):
    """Missing OHLCV columns returns error."""
    df = valid_ohlcv_df.drop(columns=["volume"])
    is_valid, errors = validate_ohlcv(df)
    
    assert not is_valid
    assert len(errors) > 0
    assert "Missing required OHLCV columns" in errors[0]
    assert "volume" in errors[0]


def test_validate_ohlcv_tz_naive(valid_ohlcv_df):
    """Timezone-naive index returns error when require_tz=True."""
    df = valid_ohlcv_df.copy()
    df.index = df.index.tz_localize(None)

    is_valid, errors = validate_ohlcv(df, require_tz=True)
    assert not is_valid
    assert "timezone-aware" in errors[0].lower()


def test_validate_ohlcv_tz_naive_allowed(valid_ohlcv_df):
    """Timezone-naive index passes when require_tz=False."""
    df = valid_ohlcv_df.copy()
    df.index = df.index.tz_localize(None)

    is_valid, errors = validate_ohlcv(df, require_tz=False)
    assert is_valid
    assert errors == []


def test_validate_ohlcv_unsorted(valid_ohlcv_df):
    """Unsorted index returns error in strict mode."""
    df = valid_ohlcv_df.iloc[::-1]  # Reverse order

    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert "sorted" in errors[0].lower()


def test_validate_ohlcv_unsorted_non_strict(valid_ohlcv_df):
    """Unsorted index passes in permissive mode only."""
    df = valid_ohlcv_df.iloc[::-1]

    # strict=False defaults to PERMISSIVE which only checks basic requirements
    is_valid, errors = validate_ohlcv(
        df, 
        strict=False,
        strictness_level=StrictnessLevel.PERMISSIVE
    )
    # Should pass in PERMISSIVE mode
    assert is_valid


def test_validate_ohlcv_duplicates(valid_ohlcv_df):
    """Duplicate timestamps return error in strict mode."""
    df = pd.concat([valid_ohlcv_df, valid_ohlcv_df.iloc[[0]]])  # Duplicate first row
    df = df.sort_index()  # Ensure sorted so we reach duplicate check

    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert "duplicate" in errors[0].lower()


def test_validate_ohlcv_object_dtype(valid_ohlcv_df):
    """Object dtype columns return error."""
    df = valid_ohlcv_df.copy()
    df["close"] = df["close"].astype(str)  # Convert to object

    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert "object dtype" in errors[0].lower()
    assert "close" in errors[0]


def test_validate_ohlcv_nans_in_ohlc(valid_ohlcv_df):
    """NaNs in OHLC columns return error in strict mode."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "close"] = float("nan")

    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert "NaN" in " ".join(errors)
    assert "close" in " ".join(errors)


def test_validate_ohlcv_nans_in_volume_allowed(valid_ohlcv_df):
    """NaNs in volume pass when allow_partial_nans=True."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "volume"] = float("nan")

    is_valid, errors = validate_ohlcv(df, strict=True, allow_partial_nans=True)
    assert is_valid
    assert errors == []


def test_validate_ohlcv_nans_in_volume_forbidden(valid_ohlcv_df):
    """NaNs in volume return error when allow_partial_nans=False."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "volume"] = float("nan")

    is_valid, errors = validate_ohlcv(df, strict=True, allow_partial_nans=False)
    assert not is_valid
    assert "volume" in " ".join(errors)


def test_validate_ohlcv_negative_price(valid_ohlcv_df):
    """Negative/zero prices return error."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "low"] = -1.0

    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert "non-positive" in errors[0].lower() or "must be > 0" in errors[0]
    assert "low" in errors[0]


def test_validate_ohlcv_high_less_than_low(valid_ohlcv_df):
    """high < low returns error."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "high"] = 90.0
    df.loc[df.index[1], "low"] = 95.0

    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert "high < low" in " ".join(errors).lower()


def test_validate_ohlcv_negative_volume(valid_ohlcv_df):
    """Negative volume returns error."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "volume"] = -100.0

    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert "negative" in " ".join(errors).lower()
    assert "volume" in " ".join(errors).lower()


def test_validate_ohlcv_non_datetime_index():
    """Non-DatetimeIndex returns error."""
    df = pd.DataFrame(
        {
            "open": [100.0],
            "high": [105.0],
            "low": [99.0],
            "close": [103.0],
            "volume": [1000.0],
        },
        index=[0],  # Integer index
    )

    is_valid, errors = validate_ohlcv(df)
    assert not is_valid
    assert "DatetimeIndex" in errors[0]


def test_validate_ohlcv_empty_dataframe():
    """Empty DataFrame returns error."""
    df = pd.DataFrame(
        columns=["open", "high", "low", "close", "volume"],
        index=pd.DatetimeIndex([], tz="UTC"),
    )

    is_valid, errors = validate_ohlcv(df)
    assert not is_valid
    assert "empty" in errors[0].lower()


# ============================================================================
# Tests for check_ohlcv (exception-raising API)
# ============================================================================


def test_check_ohlcv_valid(valid_ohlcv_df):
    """check_ohlcv doesn't raise for valid data."""
    check_ohlcv(valid_ohlcv_df, strict=True)  # Should not raise


def test_check_ohlcv_invalid_raises(valid_ohlcv_df):
    """check_ohlcv raises DataContractError for invalid data."""
    df = valid_ohlcv_df.drop(columns=["volume"])

    with pytest.raises(DataContractError) as exc_info:
        check_ohlcv(df)

    assert "Missing required OHLCV columns" in str(exc_info.value)
    assert exc_info.value.context is not None
    assert "errors" in exc_info.value.context
    assert exc_info.value.hint is not None


# ============================================================================
# Tests for OHLCVContract class
# ============================================================================


def test_contract_class_strict(valid_ohlcv_df):
    """OHLCVContract with strict mode validates correctly."""
    contract = OHLCVContract(strictness=StrictnessLevel.STRICT)
    
    is_valid, errors = contract.validate(valid_ohlcv_df)
    assert is_valid
    assert errors == []
    assert contract.version == CONTRACT_VERSION


def test_contract_class_permissive(valid_ohlcv_df):
    """OHLCVContract with permissive mode allows unsorted data."""
    contract = OHLCVContract(strictness=StrictnessLevel.PERMISSIVE)
    
    df = valid_ohlcv_df.iloc[::-1]  # Reverse order
    is_valid, errors = contract.validate(df)
    assert is_valid  # Permissive mode doesn't check sorting
    assert errors == []


def test_contract_class_normal(valid_ohlcv_df):
    """OHLCVContract with normal mode catches sorting issues."""
    contract = OHLCVContract(strictness=StrictnessLevel.NORMAL)
    
    df = valid_ohlcv_df.iloc[::-1]  # Reverse order
    is_valid, errors = contract.validate(df)
    assert not is_valid  # Normal mode checks sorting
    assert "sorted" in errors[0].lower()


def test_contract_ohlc_relationships(valid_ohlcv_df):
    """OHLCVContract checks OHLC relationships when enabled."""
    contract = OHLCVContract(
        strictness=StrictnessLevel.STRICT,
        check_ohlc_relationships=True
    )
    
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "high"] = 90.0  # high < open
    
    is_valid, errors = contract.validate(df)
    assert not is_valid
    assert "high < open" in " ".join(errors).lower() or "high < close" in " ".join(errors).lower()


def test_contract_ohlc_relationships_disabled(valid_ohlcv_df):
    """OHLCVContract skips OHLC relationships when disabled."""
    contract = OHLCVContract(
        strictness=StrictnessLevel.STRICT,
        check_ohlc_relationships=False
    )
    
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "high"] = 90.0  # high < open, but still > low
    
    is_valid, errors = contract.validate(df)
    # Should still fail because high < low check is always on in strict mode
    assert not is_valid


def test_strictness_level_enum():
    """StrictnessLevel enum has expected values."""
    assert StrictnessLevel.PERMISSIVE.value == "permissive"
    assert StrictnessLevel.NORMAL.value == "normal"
    assert StrictnessLevel.STRICT.value == "strict"


def test_contract_version_exists():
    """CONTRACT_VERSION is defined."""
    assert CONTRACT_VERSION == "1.0.0"


# ============================================================================
# Performance tests
# ============================================================================


def test_validate_performance_1k_rows():
    """Validation should be fast for 1K rows (< 5ms)."""
    import time
    
    df = pd.DataFrame(
        {
            "open": [100.0] * 1000,
            "high": [105.0] * 1000,
            "low": [99.0] * 1000,
            "close": [103.0] * 1000,
            "volume": [1000.0] * 1000,
        },
        index=pd.date_range("2024-01-01", periods=1000, freq="1h", tz="UTC"),
    )
    
    start = time.perf_counter()
    is_valid, errors = validate_ohlcv(df, strict=True)
    elapsed = time.perf_counter() - start
    
    assert is_valid
    assert elapsed < 0.005  # 5ms threshold


# ============================================================================
# Edge case tests
# ============================================================================


def test_validate_single_row():
    """Single row DataFrame validates correctly."""
    df = pd.DataFrame(
        {
            "open": [100.0],
            "high": [105.0],
            "low": [99.0],
            "close": [103.0],
            "volume": [1000.0],
        },
        index=pd.date_range("2024-01-01", periods=1, freq="1h", tz="UTC"),
    )
    
    is_valid, errors = validate_ohlcv(df, strict=True)
    assert is_valid
    assert errors == []


def test_validate_all_columns_object_dtype(valid_ohlcv_df):
    """All columns with object dtype returns multiple errors."""
    df = valid_ohlcv_df.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(str)
    
    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert len(errors) > 0
    assert "object dtype" in errors[0].lower()


def test_validate_multiple_violations(valid_ohlcv_df):
    """Multiple violations are all reported."""
    df = valid_ohlcv_df.copy()
    df = df.iloc[::-1]  # Unsorted
    df.loc[df.index[0], "volume"] = -100.0  # Negative volume
    df.loc[df.index[1], "close"] = float("nan")  # NaN
    
    is_valid, errors = validate_ohlcv(df, strict=True)
    assert not is_valid
    assert len(errors) >= 3  # At least 3 violations


def test_data_contract_error_formatting():
    """DataContractError formats message with hint and context."""
    error = DataContractError(
        message="Test error",
        hint="Test hint",
        context={"key": "value"},
    )

    msg = str(error)
    assert "Test error" in msg
    assert "Hint: Test hint" in msg
    assert "Context: {'key': 'value'}" in msg
