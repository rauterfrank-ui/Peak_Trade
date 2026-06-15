# tests/test_regime_detection.py
"""
Tests fuer Regime Detection (Phase 28)
======================================

Testet VolatilityRegimeDetector und RangeCompressionRegimeDetector.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.regime import (
    RegimeLabel,
    RegimeContext,
    RegimeDetectorConfig,
    VolatilityRegimeDetector,
    RangeCompressionRegimeDetector,
    make_regime_detector,
)
from src.strategies.vol_breakout import _rolling_last_pct_rank


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Erstellt ein einfaches OHLCV-DataFrame fuer Tests."""
    np.random.seed(42)
    n_bars = 200

    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="1h")

    # Synthetischer Preis mit Trend und Volatilitaet
    base_price = 50000.0
    returns = np.random.normal(0.0001, 0.01, n_bars)
    prices = base_price * np.cumprod(1 + returns)

    # OHLCV erstellen
    high = prices * (1 + np.abs(np.random.normal(0, 0.005, n_bars)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.005, n_bars)))
    open_prices = prices * (1 + np.random.normal(0, 0.002, n_bars))
    volume = np.random.randint(100, 1000, n_bars)

    df = pd.DataFrame(
        {
            "open": open_prices,
            "high": high,
            "low": low,
            "close": prices,
            "volume": volume,
        },
        index=dates,
    )

    return df


@pytest.fixture
def high_volatility_data() -> pd.DataFrame:
    """Erstellt Daten mit klar hoher Volatilitaet (breakout-tauglich)."""
    np.random.seed(123)
    n_bars = 200

    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="1h")

    # Erste 100 Bars: niedrige Vol
    # Letzte 100 Bars: hohe Vol (Breakout)
    base_price = 50000.0
    prices = np.zeros(n_bars)
    prices[0] = base_price

    for i in range(1, n_bars):
        if i < 100:
            # Niedrige Volatilitaet
            prices[i] = prices[i - 1] * (1 + np.random.normal(0, 0.002))
        else:
            # Hohe Volatilitaet
            prices[i] = prices[i - 1] * (1 + np.random.normal(0.001, 0.03))

    high = prices * 1.01
    low = prices * 0.99
    open_prices = prices * 1.001
    volume = np.random.randint(100, 1000, n_bars)

    df = pd.DataFrame(
        {
            "open": open_prices,
            "high": high,
            "low": low,
            "close": prices,
            "volume": volume,
        },
        index=dates,
    )

    return df


@pytest.fixture
def low_volatility_data() -> pd.DataFrame:
    """Erstellt Daten mit konstant niedriger Volatilitaet (ranging)."""
    np.random.seed(456)
    n_bars = 200

    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="1h")

    # Konstant niedrige Volatilitaet (seitwaerts)
    base_price = 50000.0
    prices = base_price + np.random.normal(0, 50, n_bars).cumsum() * 0.1

    # Sehr enge Range
    high = prices + 50
    low = prices - 50
    open_prices = prices + np.random.normal(0, 10, n_bars)
    volume = np.random.randint(100, 1000, n_bars)

    df = pd.DataFrame(
        {
            "open": open_prices,
            "high": high,
            "low": low,
            "close": prices,
            "volume": volume,
        },
        index=dates,
    )

    return df


@pytest.fixture
def default_config() -> RegimeDetectorConfig:
    """Standard-Konfiguration fuer Tests."""
    return RegimeDetectorConfig(
        enabled=True,
        detector_name="volatility_breakout",
        lookback_window=50,
        min_history_bars=100,
        vol_window=20,
        vol_percentile_breakout=0.75,
        vol_percentile_ranging=0.30,
    )


# ============================================================================
# VOLATILITY REGIME DETECTOR TESTS
# ============================================================================


class TestVolatilityRegimeDetector:
    """Tests fuer VolatilityRegimeDetector."""

    def test_detect_regimes_returns_series(
        self, sample_ohlcv_data: pd.DataFrame, default_config: RegimeDetectorConfig
    ):
        """detect_regimes() gibt eine Series mit korrektem Index zurueck."""
        detector = VolatilityRegimeDetector(default_config)
        regimes = detector.detect_regimes(sample_ohlcv_data)

        assert isinstance(regimes, pd.Series)
        assert len(regimes) == len(sample_ohlcv_data)
        assert regimes.index.equals(sample_ohlcv_data.index)

    def test_detect_regimes_valid_labels(
        self, sample_ohlcv_data: pd.DataFrame, default_config: RegimeDetectorConfig
    ):
        """Alle Regime-Labels sind gueltige Werte."""
        detector = VolatilityRegimeDetector(default_config)
        regimes = detector.detect_regimes(sample_ohlcv_data)

        valid_labels = {"breakout", "ranging", "trending", "unknown"}
        unique_labels = set(regimes.unique())

        assert unique_labels.issubset(valid_labels)

    def test_detect_regimes_high_vol_breakout(
        self, high_volatility_data: pd.DataFrame, default_config: RegimeDetectorConfig
    ):
        """Hohe Volatilitaet wird als 'breakout' erkannt."""
        detector = VolatilityRegimeDetector(default_config)
        regimes = detector.detect_regimes(high_volatility_data)

        # Letzte Bars sollten breakout sein (hohe Vol)
        last_50_regimes = regimes.iloc[-50:]
        breakout_count = (last_50_regimes == "breakout").sum()

        # Mindestens 30% der letzten Bars sollten breakout sein
        assert breakout_count >= 15, f"Nur {breakout_count} breakout-Bars in high-vol Daten"

    def test_detect_regimes_low_vol_not_breakout(
        self, low_volatility_data: pd.DataFrame, default_config: RegimeDetectorConfig
    ):
        """Niedrige Volatilitaet sollte NICHT als 'breakout' erkannt werden."""
        detector = VolatilityRegimeDetector(default_config)
        regimes = detector.detect_regimes(low_volatility_data)

        # Letzte Bars sollten NICHT breakout sein (niedrige Vol)
        last_50_regimes = regimes.iloc[-50:]
        breakout_count = (last_50_regimes == "breakout").sum()

        # Weniger als 20% der letzten Bars sollten breakout sein
        # (da die Daten konstant niedrige Volatilitaet haben)
        assert breakout_count < 10, f"Zu viele breakout-Bars ({breakout_count}) in low-vol Daten"

    def test_detect_regimes_insufficient_history(self, default_config: RegimeDetectorConfig):
        """Bei zu wenig Historie werden alle Bars als 'unknown' markiert."""
        # Nur 50 Bars (weniger als min_history_bars=100)
        short_data = pd.DataFrame(
            {
                "open": [100] * 50,
                "high": [101] * 50,
                "low": [99] * 50,
                "close": [100] * 50,
                "volume": [1000] * 50,
            },
            index=pd.date_range("2024-01-01", periods=50, freq="1h"),
        )

        detector = VolatilityRegimeDetector(default_config)
        regimes = detector.detect_regimes(short_data)

        # Alle sollten unknown sein
        assert (regimes == "unknown").all()

    def test_detect_regime_single_context(
        self, sample_ohlcv_data: pd.DataFrame, default_config: RegimeDetectorConfig
    ):
        """detect_regime() funktioniert fuer einzelnen Kontext."""
        detector = VolatilityRegimeDetector(default_config)

        context = RegimeContext(
            timestamp=sample_ohlcv_data.index[-1],
            window=sample_ohlcv_data,
            symbol="BTC/EUR",
        )

        regime = detector.detect_regime(context)
        assert regime in ("breakout", "ranging", "trending", "unknown")

    def test_missing_columns_raises_error(self, default_config: RegimeDetectorConfig):
        """Fehlende Spalten loesen ValueError aus."""
        invalid_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
                "volume": [1000, 1000, 1000],
            },
            index=pd.date_range("2024-01-01", periods=3, freq="1h"),
        )

        detector = VolatilityRegimeDetector(default_config)

        with pytest.raises(ValueError, match="Spalte 'high' nicht in DataFrame"):
            detector.detect_regimes(invalid_data)


def _legacy_atr_percentile_reference(
    series: pd.Series,
    window: int,
    min_periods: int,
) -> pd.Series:
    """Test-only reference for legacy VolatilityRegimeDetector._compute_atr_percentile (0-1 scale)."""

    def percentile_rank(x: pd.Series) -> float:
        if len(x) < 2:
            return 0.5
        return x.rank(pct=True).iloc[-1]

    return series.rolling(window=window, min_periods=min_periods).apply(percentile_rank, raw=False)


def _assert_atr_percentile_series_equal(actual: pd.Series, expected: pd.Series) -> None:
    pd.testing.assert_series_equal(actual, expected, check_names=False)
    assert actual.index.equals(expected.index)
    pd.testing.assert_index_equal(actual.index, expected.index)
    assert actual.dtype == expected.dtype
    assert actual.isna().equals(expected.isna())


def _reference_volatility_detect_regimes(
    detector: VolatilityRegimeDetector,
    df: pd.DataFrame,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Independent legacy reference for VolatilityRegimeDetector.detect_regimes."""
    n_bars = len(df)
    regimes = pd.Series("unknown", index=df.index, dtype="object")

    if n_bars < detector.config.min_history_bars:
        return (
            pd.Series(dtype=float, index=df.index),
            pd.Series(dtype=float, index=df.index),
            regimes.astype("string"),
        )

    atr = detector._compute_atr(df)
    atr_percentile = _legacy_atr_percentile_reference(
        atr,
        window=detector.config.lookback_window,
        min_periods=detector.config.vol_window,
    )
    ma_slope = detector._compute_ma_slope(df)

    high_vol_mask = atr_percentile >= detector.config.vol_percentile_breakout
    regimes[high_vol_mask] = "breakout"

    low_vol_mask = atr_percentile <= detector.config.vol_percentile_ranging
    regimes[low_vol_mask] = "ranging"

    mid_vol_mask = (~high_vol_mask) & (~low_vol_mask)
    strong_trend_mask = abs(ma_slope) > detector.config.trending_slope_threshold
    trending_mask = mid_vol_mask & strong_trend_mask
    regimes[trending_mask] = "trending"

    warmup_mask = pd.isna(atr_percentile)
    regimes[warmup_mask] = "unknown"

    regimes.name = "regime"
    return atr, atr_percentile, regimes.astype("string")


class TestVolatilityRollingPercentileGolden:
    """Golden-reference contracts for ATR rolling percentile semantics (0-1 scale)."""

    @pytest.mark.parametrize(
        ("values", "window", "min_periods"),
        [
            pytest.param([1.0, 2.0, 3.0, 4.0, 5.0], 3, 2, id="normal_ascending"),
            pytest.param([5.0, 4.0, 3.0, 2.0, 1.0], 3, 2, id="descending"),
            pytest.param([1.0, 2.0, 2.0, 2.0, 3.0], 4, 2, id="ties"),
            pytest.param([1.0, np.nan, 3.0, 4.0, 5.0], 3, 2, id="nan_in_window"),
            pytest.param([1.0, 2.0], 5, 2, id="partial_window"),
            pytest.param([2.0, 2.0, 2.0], 3, 3, id="exact_window"),
            pytest.param(list(range(1, 9)), 4, 2, id="multi_window"),
            pytest.param([7.0] * 6, 4, 2, id="constant_input"),
            pytest.param([0.1, 0.2, 0.3, 0.4, 0.5, 0.6], 3, 3, id="monotone_values"),
            pytest.param([1.0, 1.0, 2.0, 2.0, 3.0, 3.0], 4, 2, id="repeated_values"),
        ],
    )
    def test_atr_percentile_matches_legacy_reference(
        self,
        values: list[float],
        window: int,
        min_periods: int,
    ) -> None:
        idx = pd.date_range("2024-01-01", periods=len(values), freq="h", tz="UTC")
        series = pd.Series(values, index=idx, dtype=float)
        expected = _legacy_atr_percentile_reference(series, window, min_periods)
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="volatility_breakout",
            lookback_window=window,
            vol_window=min_periods,
            min_history_bars=1,
        )
        detector = VolatilityRegimeDetector(config)
        actual = detector._compute_atr_percentile(series)
        _assert_atr_percentile_series_equal(actual, expected)

    def test_detect_regimes_matches_independent_legacy_reference(
        self,
        sample_ohlcv_data: pd.DataFrame,
        default_config: RegimeDetectorConfig,
    ) -> None:
        detector = VolatilityRegimeDetector(default_config)
        expected_atr, expected_percentile, expected_regimes = _reference_volatility_detect_regimes(
            detector, sample_ohlcv_data
        )
        actual_regimes = detector.detect_regimes(sample_ohlcv_data)
        actual_atr = detector._compute_atr(sample_ohlcv_data)
        actual_percentile = detector._compute_atr_percentile(actual_atr)

        pd.testing.assert_series_equal(actual_atr, expected_atr, check_names=False)
        _assert_atr_percentile_series_equal(actual_percentile, expected_percentile)
        pd.testing.assert_series_equal(actual_regimes, expected_regimes, check_names=True)

    def test_detect_regimes_insufficient_history_empty_input(
        self, default_config: RegimeDetectorConfig
    ) -> None:
        detector = VolatilityRegimeDetector(default_config)
        empty_df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([], name="timestamp"),
        )
        actual = detector.detect_regimes(empty_df)
        _, _, expected = _reference_volatility_detect_regimes(detector, empty_df)
        pd.testing.assert_series_equal(actual, expected, check_names=True)

    def test_detect_regimes_minimal_allowed_length(self) -> None:
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="volatility_breakout",
            lookback_window=5,
            min_history_bars=5,
            vol_window=3,
            vol_percentile_breakout=0.75,
            vol_percentile_ranging=0.30,
        )
        detector = VolatilityRegimeDetector(config)
        idx = pd.date_range("2024-01-01", periods=5, freq="h")
        df = pd.DataFrame(
            {
                "open": [1.0, 2.0, 3.0, 4.0, 5.0],
                "high": [1.5, 2.5, 3.5, 4.5, 5.5],
                "low": [0.5, 1.5, 2.5, 3.5, 4.5],
                "close": [1.0, 2.0, 3.0, 4.0, 5.0],
                "volume": [1000] * 5,
            },
            index=idx,
        )
        actual = detector.detect_regimes(df)
        _, _, expected = _reference_volatility_detect_regimes(detector, df)
        pd.testing.assert_series_equal(actual, expected, check_names=True)

    def test_detect_regimes_uses_canonical_helper(self, monkeypatch) -> None:
        df = pd.DataFrame(
            {
                "open": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "high": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5],
                "low": [0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
                "close": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "volume": [1000] * 6,
            },
            index=pd.date_range("2024-01-01", periods=6, freq="h"),
        )
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="volatility_breakout",
            lookback_window=5,
            min_history_bars=5,
            vol_window=3,
        )
        detector = VolatilityRegimeDetector(config)
        calls: list[tuple[int, int]] = []

        def _spy(series: pd.Series, window: int, min_periods: int) -> pd.Series:
            calls.append((window, min_periods))
            return _rolling_last_pct_rank(series, window=window, min_periods=min_periods)

        apply_calls: list[object] = []
        original_apply = pd.core.window.rolling.Rolling.apply

        def _apply_spy(self, func, *args, **kwargs):
            apply_calls.append(func)
            return original_apply(self, func, *args, **kwargs)

        monkeypatch.setattr("src.regime.detectors._rolling_last_pct_rank", _spy)
        monkeypatch.setattr(pd.core.window.rolling.Rolling, "apply", _apply_spy)

        regimes = detector.detect_regimes(df)

        assert regimes is not None
        assert len(calls) == 1
        assert calls[0] == (config.lookback_window, config.vol_window)
        assert not apply_calls


# ============================================================================
# RANGE COMPRESSION DETECTOR TESTS
# ============================================================================


def _legacy_range_ratio_percentile_reference(
    series: pd.Series,
    window: int,
    min_periods: int,
) -> pd.Series:
    """Test-only reference for legacy rolling().apply(rank(pct=True)) semantics (0-1 scale)."""
    return series.rolling(window=window, min_periods=min_periods).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1],
        raw=False,
    )


def _assert_range_ratio_percentile_series_equal(actual: pd.Series, expected: pd.Series) -> None:
    pd.testing.assert_series_equal(actual, expected, check_names=False)
    assert actual.index.equals(expected.index)
    pd.testing.assert_index_equal(actual.index, expected.index)
    assert actual.dtype == expected.dtype
    assert actual.isna().equals(expected.isna())


def _reference_range_compression_detect_regimes(
    detector: RangeCompressionRegimeDetector,
    df: pd.DataFrame,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Independent legacy reference for RangeCompressionRegimeDetector.detect_regimes."""
    n_bars = len(df)
    regimes = pd.Series("unknown", index=df.index, dtype="object")

    if n_bars < detector.config.min_history_bars:
        return (
            pd.Series(dtype=float, index=df.index),
            pd.Series(dtype=float, index=df.index),
            regimes.astype("string"),
        )

    range_ratio = detector._compute_range_ratio(df)
    directional_bias = detector._compute_directional_bias(df)
    ratio_percentile = _legacy_range_ratio_percentile_reference(
        range_ratio,
        window=detector.config.lookback_window,
        min_periods=detector.config.range_compression_window,
    )

    expansion_mask = ratio_percentile >= 0.7
    regimes[expansion_mask] = "breakout"

    compression_mask = ratio_percentile <= detector.config.compression_threshold
    regimes[compression_mask] = "ranging"

    mid_range_mask = (~expansion_mask) & (~compression_mask)
    strong_bias_mask = abs(directional_bias) > 0.02
    trending_mask = mid_range_mask & strong_bias_mask
    regimes[trending_mask] = "trending"

    warmup_mask = pd.isna(ratio_percentile)
    regimes[warmup_mask] = "unknown"

    regimes.name = "regime"
    return range_ratio, ratio_percentile, regimes.astype("string")


class TestRangeCompressionRegimeDetector:
    """Tests fuer RangeCompressionRegimeDetector."""

    @pytest.fixture
    def range_config(self) -> RegimeDetectorConfig:
        """Config fuer Range Compression Detector."""
        return RegimeDetectorConfig(
            enabled=True,
            detector_name="range_compression",
            lookback_window=50,
            min_history_bars=100,
            range_compression_window=20,
            compression_threshold=0.3,
        )

    def test_detect_regimes_returns_series(
        self, sample_ohlcv_data: pd.DataFrame, range_config: RegimeDetectorConfig
    ):
        """detect_regimes() gibt eine Series zurueck."""
        detector = RangeCompressionRegimeDetector(range_config)
        regimes = detector.detect_regimes(sample_ohlcv_data)

        assert isinstance(regimes, pd.Series)
        assert len(regimes) == len(sample_ohlcv_data)

    def test_detect_regimes_valid_labels(
        self, sample_ohlcv_data: pd.DataFrame, range_config: RegimeDetectorConfig
    ):
        """Alle Labels sind gueltig."""
        detector = RangeCompressionRegimeDetector(range_config)
        regimes = detector.detect_regimes(sample_ohlcv_data)

        valid_labels = {"breakout", "ranging", "trending", "unknown"}
        unique_labels = set(regimes.unique())

        assert unique_labels.issubset(valid_labels)


class TestRangeCompressionRollingPercentileGolden:
    """Golden-reference contracts for range_ratio rolling percentile semantics (0-1 scale)."""

    @pytest.mark.parametrize(
        ("values", "window", "min_periods"),
        [
            pytest.param([1.0, 2.0, 3.0, 4.0, 5.0], 3, 2, id="normal_ascending"),
            pytest.param([5.0, 4.0, 3.0, 2.0, 1.0], 3, 2, id="descending"),
            pytest.param([1.0, 2.0, 2.0, 2.0, 3.0], 4, 2, id="ties"),
            pytest.param([1.0, np.nan, 3.0, 4.0, 5.0], 3, 2, id="nan_in_window"),
            pytest.param([1.0, 2.0], 5, 2, id="partial_window"),
            pytest.param([2.0, 2.0, 2.0], 3, 3, id="exact_window"),
            pytest.param(list(range(1, 9)), 4, 2, id="multi_window"),
            pytest.param([7.0] * 6, 4, 2, id="constant_input"),
            pytest.param([0.1, 0.2, 0.3, 0.4, 0.5, 0.6], 3, 3, id="monotone_values"),
            pytest.param([1.0, 1.0, 2.0, 2.0, 3.0, 3.0], 4, 2, id="repeated_values"),
        ],
    )
    def test_range_ratio_percentile_matches_legacy_reference(
        self,
        values: list[float],
        window: int,
        min_periods: int,
    ) -> None:
        idx = pd.date_range("2024-01-01", periods=len(values), freq="h", tz="UTC")
        series = pd.Series(values, index=idx, dtype=float)
        expected = _legacy_range_ratio_percentile_reference(series, window, min_periods)
        actual = _rolling_last_pct_rank(series, window=window, min_periods=min_periods) / 100.0
        _assert_range_ratio_percentile_series_equal(actual, expected)

    def test_detect_regimes_matches_independent_legacy_reference(
        self,
        sample_ohlcv_data: pd.DataFrame,
    ) -> None:
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="range_compression",
            lookback_window=50,
            min_history_bars=100,
            range_compression_window=20,
            compression_threshold=0.3,
        )
        detector = RangeCompressionRegimeDetector(config)
        expected_range_ratio, expected_percentile, expected_regimes = (
            _reference_range_compression_detect_regimes(detector, sample_ohlcv_data)
        )
        actual_regimes = detector.detect_regimes(sample_ohlcv_data)
        actual_range_ratio = detector._compute_range_ratio(sample_ohlcv_data)
        actual_percentile = (
            _rolling_last_pct_rank(
                actual_range_ratio,
                window=config.lookback_window,
                min_periods=config.range_compression_window,
            )
            / 100.0
        )

        pd.testing.assert_series_equal(actual_range_ratio, expected_range_ratio, check_names=False)
        _assert_range_ratio_percentile_series_equal(actual_percentile, expected_percentile)
        pd.testing.assert_series_equal(actual_regimes, expected_regimes, check_names=True)

    def test_detect_regimes_insufficient_history_empty_input(self) -> None:
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="range_compression",
            lookback_window=5,
            min_history_bars=10,
            range_compression_window=3,
        )
        detector = RangeCompressionRegimeDetector(config)
        empty_df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([], name="timestamp"),
        )
        actual = detector.detect_regimes(empty_df)
        _, _, expected = _reference_range_compression_detect_regimes(detector, empty_df)
        pd.testing.assert_series_equal(actual, expected, check_names=True)

    def test_detect_regimes_minimal_allowed_length(self) -> None:
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="range_compression",
            lookback_window=5,
            min_history_bars=5,
            range_compression_window=3,
            compression_threshold=0.3,
        )
        detector = RangeCompressionRegimeDetector(config)
        idx = pd.date_range("2024-01-01", periods=5, freq="h")
        df = pd.DataFrame(
            {
                "open": [1.0, 2.0, 3.0, 4.0, 5.0],
                "high": [1.5, 2.5, 3.5, 4.5, 5.5],
                "low": [0.5, 1.5, 2.5, 3.5, 4.5],
                "close": [1.0, 2.0, 3.0, 4.0, 5.0],
                "volume": [1000] * 5,
            },
            index=idx,
        )
        actual = detector.detect_regimes(df)
        _, _, expected = _reference_range_compression_detect_regimes(detector, df)
        pd.testing.assert_series_equal(actual, expected, check_names=True)

    def test_detect_regimes_uses_canonical_helper(self, monkeypatch) -> None:
        df = pd.DataFrame(
            {
                "open": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "high": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5],
                "low": [0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
                "close": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "volume": [1000] * 6,
            },
            index=pd.date_range("2024-01-01", periods=6, freq="h"),
        )
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="range_compression",
            lookback_window=5,
            min_history_bars=5,
            range_compression_window=3,
        )
        detector = RangeCompressionRegimeDetector(config)
        calls: list[tuple[int, int]] = []

        def _spy(series: pd.Series, window: int, min_periods: int) -> pd.Series:
            calls.append((window, min_periods))
            return _rolling_last_pct_rank(series, window=window, min_periods=min_periods)

        apply_calls: list[object] = []
        original_apply = pd.core.window.rolling.Rolling.apply

        def _apply_spy(self, func, *args, **kwargs):
            apply_calls.append(func)
            return original_apply(self, func, *args, **kwargs)

        monkeypatch.setattr("src.regime.detectors._rolling_last_pct_rank", _spy)
        monkeypatch.setattr(pd.core.window.rolling.Rolling, "apply", _apply_spy)

        regimes = detector.detect_regimes(df)

        assert regimes is not None
        assert len(calls) == 1
        assert calls[0] == (config.lookback_window, config.range_compression_window)
        assert not apply_calls


# ============================================================================
# FACTORY FUNCTION TESTS
# ============================================================================


class TestMakeRegimeDetector:
    """Tests fuer make_regime_detector Factory."""

    def test_returns_none_when_disabled(self):
        """Gibt None zurueck wenn disabled."""
        config = RegimeDetectorConfig(enabled=False)
        detector = make_regime_detector(config)

        assert detector is None

    def test_creates_volatility_detector(self):
        """Erstellt VolatilityRegimeDetector."""
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="volatility_breakout",
        )
        detector = make_regime_detector(config)

        assert detector is not None
        assert isinstance(detector, VolatilityRegimeDetector)

    def test_creates_range_compression_detector(self):
        """Erstellt RangeCompressionRegimeDetector."""
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="range_compression",
        )
        detector = make_regime_detector(config)

        assert detector is not None
        assert isinstance(detector, RangeCompressionRegimeDetector)

    def test_unknown_detector_raises_error(self):
        """Unbekannter Detector-Name loest ValueError aus."""
        config = RegimeDetectorConfig(
            enabled=True,
            detector_name="unknown_detector",
        )

        with pytest.raises(ValueError, match="Unbekannter Regime-Detector"):
            make_regime_detector(config)

    def test_accepts_alias_names(self):
        """Akzeptiert Alias-Namen fuer Detectors."""
        for alias in ["volatility", "vol", "volatility_breakout"]:
            config = RegimeDetectorConfig(enabled=True, detector_name=alias)
            detector = make_regime_detector(config)
            assert isinstance(detector, VolatilityRegimeDetector)

        for alias in ["range", "compression", "range_compression"]:
            config = RegimeDetectorConfig(enabled=True, detector_name=alias)
            detector = make_regime_detector(config)
            assert isinstance(detector, RangeCompressionRegimeDetector)


# ============================================================================
# CONFIG TESTS
# ============================================================================


class TestRegimeDetectorConfig:
    """Tests fuer RegimeDetectorConfig."""

    def test_default_values(self):
        """Prueft Default-Werte."""
        config = RegimeDetectorConfig()

        assert config.enabled is False
        assert config.detector_name == "volatility_breakout"
        assert config.lookback_window == 50
        assert config.min_history_bars == 100
        assert config.vol_window == 20

    def test_to_dict(self):
        """to_dict() gibt alle Felder zurueck."""
        config = RegimeDetectorConfig(enabled=True, vol_window=30)
        d = config.to_dict()

        assert isinstance(d, dict)
        assert d["enabled"] is True
        assert d["vol_window"] == 30

    def test_from_peak_config(self):
        """from_peak_config() liest aus PeakConfig."""

        # Mock PeakConfig
        class MockConfig:
            def get(self, path: str, default=None):
                values = {
                    "regime.enabled": True,
                    "regime.detector_name": "vol",
                    "regime.vol_window": 25,
                }
                return values.get(path, default)

        config = RegimeDetectorConfig.from_peak_config(MockConfig())

        assert config.enabled is True
        assert config.detector_name == "vol"
        assert config.vol_window == 25
