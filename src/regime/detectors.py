# src/regime/detectors.py
"""
Peak_Trade Regime Detectors (Phase 28)
======================================

Konkrete Implementierungen von RegimeDetector und RegimeSeriesDetector.

Verfuegbare Detectors:
- VolatilityRegimeDetector: ATR/Range-basierte Regime-Erkennung
- RangeCompressionRegimeDetector: Erkennt Range-Kompression vor Breakouts

Factory:
- make_regime_detector(): Erstellt Detector aus Config
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import logging

import numpy as np
import pandas as pd

from .base import (
    RegimeLabel,
    RegimeContext,
    RegimeDetector,
    RegimeSeriesDetector,
)
from .config import RegimeDetectorConfig

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ============================================================================
# VOLATILITY REGIME DETECTOR
# ============================================================================


class VolatilityRegimeDetector:
    """
    Volatilitaets-basierter Regime-Detector.

    Erkennt Regime basierend auf:
    1. ATR (Average True Range) fuer Volatilitaets-Niveau
    2. ATR-Perzentil fuer relative Volatilitaet
    3. Optional: MA-Slope fuer Trending-Erkennung

    Regime-Logik:
    - breakout: Hohe Volatilitaet (ATR-Perzentil > vol_percentile_breakout)
    - ranging: Niedrige Volatilitaet (ATR-Perzentil < vol_percentile_ranging)
    - trending: Mittlere Vol + signifikanter MA-Slope
    - unknown: Zu wenig Historie oder unklare Signale

    Attributes:
        config: RegimeDetectorConfig mit allen Parametern

    Example:
        >>> config = RegimeDetectorConfig(
        ...     enabled=True,
        ...     vol_window=20,
        ...     vol_percentile_breakout=0.75,
        ... )
        >>> detector = VolatilityRegimeDetector(config)
        >>> regimes = detector.detect_regimes(df)
    """

    def __init__(self, config: RegimeDetectorConfig) -> None:
        self.config = config

    def _compute_atr(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet Average True Range (ATR).

        Args:
            data: DataFrame mit high, low, close

        Returns:
            ATR als pd.Series
        """
        high = data["high"]
        low = data["low"]
        close = data["close"]

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR (EMA des True Range)
        atr = tr.ewm(
            span=self.config.vol_window, min_periods=self.config.vol_window, adjust=False
        ).mean()

        return atr

    def _compute_atr_percentile(self, atr: pd.Series) -> pd.Series:
        """
        Berechnet das Rolling-Perzentil der ATR.

        Args:
            atr: ATR-Serie

        Returns:
            Perzentil-Rang (0.0 bis 1.0)
        """
        window = self.config.lookback_window

        def percentile_rank(x: pd.Series) -> float:
            if len(x) < 2:
                return 0.5
            return x.rank(pct=True).iloc[-1]

        return atr.rolling(window=window, min_periods=self.config.vol_window).apply(
            percentile_rank, raw=False
        )

    def _compute_ma_slope(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet den Slope des Moving Average.

        Args:
            data: DataFrame mit close

        Returns:
            Normalisierter MA-Slope
        """
        close = data["close"]
        ma = close.rolling(window=self.config.trending_ma_window).mean()

        # Slope = prozentuale Aenderung des MA
        slope = ma.pct_change(periods=5)  # 5-Bar Slope fuer Stabilitaet

        return slope

    def detect_regimes(self, df: pd.DataFrame) -> pd.Series:
        """
        Erkennt Regime fuer eine komplette OHLCV-Serie.

        Args:
            df: OHLCV-DataFrame mit DatetimeIndex

        Returns:
            pd.Series mit RegimeLabels (Index = df.index)
        """
        # Validierung
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(
                    f"Spalte '{col}' nicht in DataFrame. Verfuegbar: {list(df.columns)}"
                )

        n_bars = len(df)

        # Initialisiere alle als "unknown"
        regimes = pd.Series("unknown", index=df.index, dtype="object")

        # Pruefe Mindest-Historie
        if n_bars < self.config.min_history_bars:
            logger.debug(
                f"Zu wenig Historie ({n_bars} < {self.config.min_history_bars}), "
                f"alle Bars als 'unknown' markiert"
            )
            return regimes.astype("string")

        # ATR und Perzentil berechnen
        atr = self._compute_atr(df)
        atr_percentile = self._compute_atr_percentile(atr)

        # MA-Slope fuer Trending
        ma_slope = self._compute_ma_slope(df)

        # Regime-Klassifikation
        # 1. Breakout: Hohe Volatilitaet
        high_vol_mask = atr_percentile >= self.config.vol_percentile_breakout
        regimes[high_vol_mask] = "breakout"

        # 2. Ranging: Niedrige Volatilitaet
        low_vol_mask = atr_percentile <= self.config.vol_percentile_ranging
        regimes[low_vol_mask] = "ranging"

        # 3. Trending: Mittlere Vol + signifikanter Slope
        mid_vol_mask = (~high_vol_mask) & (~low_vol_mask)
        strong_trend_mask = abs(ma_slope) > self.config.trending_slope_threshold
        trending_mask = mid_vol_mask & strong_trend_mask
        regimes[trending_mask] = "trending"

        # 4. Unknown: Zu wenig Daten (erste Bars)
        warmup_mask = pd.isna(atr_percentile)
        regimes[warmup_mask] = "unknown"

        regimes.name = "regime"
        return regimes.astype("string")

    def detect_regime(self, context: RegimeContext) -> RegimeLabel:
        """
        Erkennt das Regime fuer einen einzelnen Zeitpunkt.

        Args:
            context: RegimeContext mit aktuellen Daten

        Returns:
            RegimeLabel
        """
        window = context.window

        if len(window) < self.config.min_history_bars:
            return "unknown"

        # Berechne Regime fuer das gesamte Window
        regimes = self.detect_regimes(window)

        # Nimm das letzte Regime
        if not regimes.empty:
            last_regime = regimes.iloc[-1]
            if last_regime in ("breakout", "ranging", "trending", "unknown"):
                return last_regime  # type: ignore

        return "unknown"


# ============================================================================
# RANGE COMPRESSION REGIME DETECTOR
# ============================================================================


class RangeCompressionRegimeDetector:
    """
    Range-Compression-basierter Regime-Detector.

    Erkennt Regime basierend auf Range-Kompression/-Expansion:
    1. Range-Ratio: aktuelle Range / historische Range
    2. Kompressionsphase: Range schrumpft (potentieller Pre-Breakout)
    3. Expansionsphase: Range expandiert (Breakout laeuft)

    Regime-Logik:
    - breakout: Range-Ratio hoch (Expansion nach Kompression)
    - ranging: Range-Ratio niedrig (Kompressionsphase)
    - trending: Mittlere Range mit direktionalem Bias
    - unknown: Zu wenig Historie

    Attributes:
        config: RegimeDetectorConfig mit allen Parametern

    Example:
        >>> config = RegimeDetectorConfig(
        ...     enabled=True,
        ...     range_compression_window=20,
        ...     compression_threshold=0.3,
        ... )
        >>> detector = RangeCompressionRegimeDetector(config)
        >>> regimes = detector.detect_regimes(df)
    """

    def __init__(self, config: RegimeDetectorConfig) -> None:
        self.config = config

    def _compute_range_ratio(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet das Verhaeltnis von aktueller Range zu historischer Range.

        Args:
            data: DataFrame mit high, low

        Returns:
            Range-Ratio als pd.Series
        """
        high = data["high"]
        low = data["low"]

        # Aktuelle Bar-Range
        current_range = high - low

        # Historische Range (Rolling)
        window = self.config.range_compression_window
        historical_high = high.rolling(window=window).max()
        historical_low = low.rolling(window=window).min()
        historical_range = historical_high - historical_low

        # Range-Ratio (aktuell / historisch)
        # Hoher Wert = Expansion, niedriger Wert = Kompression
        range_ratio = current_range / historical_range.replace(0, np.nan)

        return range_ratio.fillna(0.5)

    def _compute_directional_bias(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet den direktionalen Bias (Trend-Richtung).

        Args:
            data: DataFrame mit close

        Returns:
            Bias (-1 bis +1)
        """
        close = data["close"]
        ma = close.rolling(window=self.config.trending_ma_window).mean()

        # Position relativ zum MA
        bias = (close - ma) / ma

        return bias.fillna(0.0)

    def detect_regimes(self, df: pd.DataFrame) -> pd.Series:
        """
        Erkennt Regime fuer eine komplette OHLCV-Serie.

        Args:
            df: OHLCV-DataFrame mit DatetimeIndex

        Returns:
            pd.Series mit RegimeLabels (Index = df.index)
        """
        # Validierung
        required_cols = ["high", "low", "close"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(
                    f"Spalte '{col}' nicht in DataFrame. Verfuegbar: {list(df.columns)}"
                )

        n_bars = len(df)

        # Initialisiere alle als "unknown"
        regimes = pd.Series("unknown", index=df.index, dtype="object")

        if n_bars < self.config.min_history_bars:
            logger.debug(
                f"Zu wenig Historie ({n_bars} < {self.config.min_history_bars}), "
                f"alle Bars als 'unknown' markiert"
            )
            return regimes.astype("string")

        # Range-Ratio und Bias berechnen
        range_ratio = self._compute_range_ratio(df)
        directional_bias = self._compute_directional_bias(df)

        # Perzentile der Range-Ratio
        ratio_percentile = range_ratio.rolling(
            window=self.config.lookback_window, min_periods=self.config.range_compression_window
        ).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False)

        # Regime-Klassifikation
        # 1. Breakout: Hohe Range-Expansion
        expansion_mask = ratio_percentile >= 0.7
        regimes[expansion_mask] = "breakout"

        # 2. Ranging: Starke Range-Kompression
        compression_mask = ratio_percentile <= self.config.compression_threshold
        regimes[compression_mask] = "ranging"

        # 3. Trending: Mittlere Range mit Bias
        mid_range_mask = (~expansion_mask) & (~compression_mask)
        strong_bias_mask = abs(directional_bias) > 0.02
        trending_mask = mid_range_mask & strong_bias_mask
        regimes[trending_mask] = "trending"

        # 4. Unknown: Warmup-Phase
        warmup_mask = pd.isna(ratio_percentile)
        regimes[warmup_mask] = "unknown"

        regimes.name = "regime"
        return regimes.astype("string")

    def detect_regime(self, context: RegimeContext) -> RegimeLabel:
        """
        Erkennt das Regime fuer einen einzelnen Zeitpunkt.

        Args:
            context: RegimeContext mit aktuellen Daten

        Returns:
            RegimeLabel
        """
        window = context.window

        if len(window) < self.config.min_history_bars:
            return "unknown"

        regimes = self.detect_regimes(window)

        if not regimes.empty:
            last_regime = regimes.iloc[-1]
            if last_regime in ("breakout", "ranging", "trending", "unknown"):
                return last_regime  # type: ignore

        return "unknown"


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


def make_regime_detector(
    config: RegimeDetectorConfig,
) -> Optional[RegimeSeriesDetector]:
    """
    Factory-Funktion: Erstellt einen RegimeDetector aus Config.

    Args:
        config: RegimeDetectorConfig

    Returns:
        RegimeSeriesDetector-Instanz oder None (wenn disabled)

    Raises:
        ValueError: Bei unbekanntem detector_name

    Example:
        >>> config = RegimeDetectorConfig(enabled=True, detector_name="volatility_breakout")
        >>> detector = make_regime_detector(config)
        >>> if detector:
        ...     regimes = detector.detect_regimes(df)
    """
    if not config.enabled:
        logger.debug("Regime Detection ist deaktiviert (enabled=false)")
        return None

    detector_name = config.detector_name.lower()

    if detector_name in ("volatility_breakout", "volatility", "vol"):
        logger.info(f"Erstelle VolatilityRegimeDetector mit window={config.vol_window}")
        return VolatilityRegimeDetector(config)

    elif detector_name in ("range_compression", "range", "compression"):
        logger.info(
            f"Erstelle RangeCompressionRegimeDetector mit window={config.range_compression_window}"
        )
        return RangeCompressionRegimeDetector(config)

    else:
        raise ValueError(
            f"Unbekannter Regime-Detector: '{config.detector_name}'. "
            f"Verfuegbar: 'volatility_breakout', 'range_compression'"
        )
