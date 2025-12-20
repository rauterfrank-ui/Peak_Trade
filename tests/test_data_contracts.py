"""
Tests for Data Contract Gate (Wave A - Stability Plan)
"""
import pandas as pd
import pytest

from src.data.contracts import DataContractError, validate_ohlcv


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


@pytest.mark.smoke
def test_validate_ohlcv_valid_strict(valid_ohlcv_df):
    """Valid OHLCV passes strict validation."""
    validate_ohlcv(valid_ohlcv_df, strict=True, require_tz=True)  # Should not raise


@pytest.mark.smoke
def test_validate_ohlcv_missing_columns(valid_ohlcv_df):
    """Missing OHLCV columns raises DataContractError."""
    df = valid_ohlcv_df.drop(columns=["volume"])

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df)

    assert "Missing required OHLCV columns" in str(exc_info.value)
    assert exc_info.value.context["missing_columns"] == ["volume"]
    assert exc_info.value.hint is not None


def test_validate_ohlcv_tz_naive(valid_ohlcv_df):
    """Timezone-naive index raises error when require_tz=True."""
    df = valid_ohlcv_df.copy()
    df.index = df.index.tz_localize(None)

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, require_tz=True)

    assert "timezone-aware" in str(exc_info.value).lower()
    assert "tz_localize" in exc_info.value.hint


def test_validate_ohlcv_tz_naive_allowed(valid_ohlcv_df):
    """Timezone-naive index passes when require_tz=False."""
    df = valid_ohlcv_df.copy()
    df.index = df.index.tz_localize(None)

    validate_ohlcv(df, require_tz=False)  # Should not raise


def test_validate_ohlcv_unsorted(valid_ohlcv_df):
    """Unsorted index raises error in strict mode."""
    df = valid_ohlcv_df.iloc[::-1]  # Reverse order

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, strict=True)

    assert "sorted" in str(exc_info.value).lower()
    assert "sort_index" in exc_info.value.hint


def test_validate_ohlcv_unsorted_non_strict(valid_ohlcv_df):
    """Unsorted index passes in non-strict mode."""
    df = valid_ohlcv_df.iloc[::-1]

    validate_ohlcv(df, strict=False)  # Should not raise


def test_validate_ohlcv_duplicates(valid_ohlcv_df):
    """Duplicate timestamps raise error in strict mode."""
    df = pd.concat([valid_ohlcv_df, valid_ohlcv_df.iloc[[0]]])  # Duplicate first row
    df = df.sort_index()  # Ensure sorted so we reach duplicate check

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, strict=True)

    assert "duplicate" in str(exc_info.value).lower()
    assert exc_info.value.context["duplicate_count"] == 1


def test_validate_ohlcv_object_dtype(valid_ohlcv_df):
    """Object dtype columns raise error in strict mode."""
    df = valid_ohlcv_df.copy()
    df["close"] = df["close"].astype(str)  # Convert to object

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, strict=True)

    assert "object dtype" in str(exc_info.value).lower()
    assert "close" in exc_info.value.context["object_columns"]


def test_validate_ohlcv_nans_in_ohlc(valid_ohlcv_df):
    """NaNs in OHLC columns raise error in strict mode."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "close"] = float("nan")

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, strict=True)

    assert "NaN" in str(exc_info.value)
    assert "close" in exc_info.value.context["nan_columns"]


def test_validate_ohlcv_nans_in_volume_allowed(valid_ohlcv_df):
    """NaNs in volume pass when allow_partial_nans=True."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "volume"] = float("nan")

    validate_ohlcv(df, strict=True, allow_partial_nans=True)  # Should not raise


def test_validate_ohlcv_nans_in_volume_forbidden(valid_ohlcv_df):
    """NaNs in volume raise error when allow_partial_nans=False."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "volume"] = float("nan")

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, strict=True, allow_partial_nans=False)

    assert "volume" in exc_info.value.context["nan_columns"]


def test_validate_ohlcv_negative_price(valid_ohlcv_df):
    """Negative/zero prices raise error in strict mode."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "low"] = -1.0

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, strict=True)

    assert "non-positive" in str(exc_info.value).lower()
    assert exc_info.value.context["column"] == "low"


def test_validate_ohlcv_high_less_than_low(valid_ohlcv_df):
    """high < low raises error in strict mode."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "high"] = 90.0
    df.loc[df.index[1], "low"] = 95.0

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, strict=True)

    assert "high < low" in str(exc_info.value)


def test_validate_ohlcv_negative_volume(valid_ohlcv_df):
    """Negative volume raises error in strict mode."""
    df = valid_ohlcv_df.copy()
    df.loc[df.index[1], "volume"] = -100.0

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df, strict=True)

    assert "negative" in str(exc_info.value).lower()
    assert "volume" in str(exc_info.value).lower()


def test_validate_ohlcv_non_datetime_index():
    """Non-DatetimeIndex raises error."""
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

    with pytest.raises(DataContractError) as exc_info:
        validate_ohlcv(df)

    assert "DatetimeIndex" in str(exc_info.value)
    assert exc_info.value.context["index_type"] == "Index"


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
