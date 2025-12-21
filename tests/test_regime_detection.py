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


# ============================================================================
# RANGE COMPRESSION DETECTOR TESTS
# ============================================================================


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
