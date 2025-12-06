# src/strategies/vol_regime_filter.py
"""
Peak_Trade Volatility Regime Filter (Phase 40)
==============================================

Volatilitäts-basierter Filter für Trading-Strategien.

Konzept:
- Berechnet ATR oder realized Volatility
- Erlaubt Trades nur wenn Volatilität in einem definierten Bereich liegt
- Kann mit anderen Strategien kombiniert werden (als Filter)

Verwendung:
1. Als standalone Filter für Signal-Modifikation
2. Als Komponente in CompositeStrategy
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


class VolRegimeFilter(BaseStrategy):
    """
    Volatility Regime Filter (Phase 40).

    Kein Trading-Strategie im klassischen Sinne, sondern ein Filter der
    bestimmt, ob gehandelt werden darf basierend auf der aktuellen Volatilität.

    Signale:
    - 1: Trading erlaubt (Volatilität im akzeptablen Bereich)
    - 0: Trading blockiert (Volatilität außerhalb des Bereichs)
    - -1: Optional für "inverse" Filter (nur bei hoher Vol handeln)

    Kann auf zwei Arten verwendet werden:
    1. Als Filter für andere Strategien (multipliziert mit deren Signal)
    2. Als eigenständiger Indikator für Regime-Erkennung

    Args:
        vol_window: Fenster für Volatilitäts-Berechnung (default: 20)
        vol_method: Methode ("atr", "std", "realized") (default: "atr")
        min_vol: Minimale Volatilität für Trading (default: None)
        max_vol: Maximale Volatilität für Trading (default: None)
        atr_threshold: Alternative: ATR muss > Threshold sein (default: None)
        vol_percentile_low: Trading bei Vol > X. Perzentil (default: None)
        vol_percentile_high: Trading bei Vol < X. Perzentil (default: None)
        lookback_percentile: Lookback für Perzentil-Berechnung (default: 100)
        invert: Wenn True, invertiert die Logik (default: False)
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> # Nur handeln wenn ATR im mittleren Bereich
        >>> filter = VolRegimeFilter(
        ...     vol_window=14,
        ...     vol_percentile_low=25,
        ...     vol_percentile_high=75
        ... )
        >>> mask = filter.generate_signals(df)
        >>> filtered_signals = original_signals * mask

        >>> # Mit ATR-Threshold
        >>> filter = VolRegimeFilter(vol_window=14, atr_threshold=100.0)
    """

    KEY = "vol_regime_filter"

    def __init__(
        self,
        vol_window: int = 20,
        vol_method: str = "atr",
        min_vol: Optional[float] = None,
        max_vol: Optional[float] = None,
        atr_threshold: Optional[float] = None,
        vol_percentile_low: Optional[float] = None,
        vol_percentile_high: Optional[float] = None,
        lookback_percentile: int = 100,
        invert: bool = False,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Vol Regime Filter.

        Args:
            vol_window: Fenster für Volatilitäts-Berechnung
            vol_method: "atr" (Average True Range), "std" (Standard Dev),
                        oder "realized" (realized volatility)
            min_vol: Minimale absolute Volatilität
            max_vol: Maximale absolute Volatilität
            atr_threshold: ATR muss über diesem Wert liegen
            vol_percentile_low: Untere Perzentil-Grenze (0-100)
            vol_percentile_high: Obere Perzentil-Grenze (0-100)
            lookback_percentile: Lookback für Perzentil-Berechnung
            invert: Invertiert die Filter-Logik
            config: Optional Config-Dict
            metadata: Optional Metadata
        """
        base_cfg: Dict[str, Any] = {
            "vol_window": vol_window,
            "vol_method": vol_method,
            "min_vol": min_vol,
            "max_vol": max_vol,
            "atr_threshold": atr_threshold,
            "vol_percentile_low": vol_percentile_low,
            "vol_percentile_high": vol_percentile_high,
            "lookback_percentile": lookback_percentile,
            "invert": invert,
        }
        if config:
            base_cfg.update(config)

        meta = metadata or StrategyMetadata(
            name="Volatility Regime Filter",
            description="Volatilitäts-basierter Trading-Filter (Phase 40)",
            version="1.0.0",
            author="Peak_Trade",
            regime="any",
            tags=["filter", "volatility", "regime", "atr"],
        )

        super().__init__(config=base_cfg, metadata=meta)

        # Parameter extrahieren
        self.vol_window = int(self.config["vol_window"])
        self.vol_method = str(self.config["vol_method"]).lower()
        self.min_vol = self.config.get("min_vol")
        self.max_vol = self.config.get("max_vol")
        self.atr_threshold = self.config.get("atr_threshold")
        self.vol_percentile_low = self.config.get("vol_percentile_low")
        self.vol_percentile_high = self.config.get("vol_percentile_high")
        self.lookback_percentile = int(self.config.get("lookback_percentile", 100))
        self.invert = bool(self.config.get("invert", False))

        # Als float konvertieren wenn nicht None
        if self.min_vol is not None:
            self.min_vol = float(self.min_vol)
        if self.max_vol is not None:
            self.max_vol = float(self.max_vol)
        if self.atr_threshold is not None:
            self.atr_threshold = float(self.atr_threshold)
        if self.vol_percentile_low is not None:
            self.vol_percentile_low = float(self.vol_percentile_low)
        if self.vol_percentile_high is not None:
            self.vol_percentile_high = float(self.vol_percentile_high)

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.vol_window < 2:
            raise ValueError(f"vol_window ({self.vol_window}) muss >= 2 sein")

        if self.vol_method not in ("atr", "std", "realized"):
            raise ValueError(
                f"vol_method ({self.vol_method}) muss 'atr', 'std' oder 'realized' sein"
            )

        if self.lookback_percentile < self.vol_window:
            raise ValueError(
                f"lookback_percentile ({self.lookback_percentile}) muss >= vol_window ({self.vol_window}) sein"
            )

        if self.vol_percentile_low is not None:
            if not (0 <= self.vol_percentile_low <= 100):
                raise ValueError(
                    f"vol_percentile_low ({self.vol_percentile_low}) muss zwischen 0 und 100 liegen"
                )

        if self.vol_percentile_high is not None:
            if not (0 <= self.vol_percentile_high <= 100):
                raise ValueError(
                    f"vol_percentile_high ({self.vol_percentile_high}) muss zwischen 0 und 100 liegen"
                )

        if (self.vol_percentile_low is not None and
            self.vol_percentile_high is not None and
            self.vol_percentile_low >= self.vol_percentile_high):
            raise ValueError(
                f"vol_percentile_low ({self.vol_percentile_low}) muss < vol_percentile_high ({self.vol_percentile_high}) sein"
            )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.vol_regime_filter",
    ) -> "VolRegimeFilter":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            VolRegimeFilter-Instanz
        """
        vol_window = cfg.get(f"{section}.vol_window", 20)
        vol_method = cfg.get(f"{section}.vol_method", "atr")
        min_vol = cfg.get(f"{section}.min_vol", None)
        max_vol = cfg.get(f"{section}.max_vol", None)
        atr_threshold = cfg.get(f"{section}.atr_threshold", None)
        vol_percentile_low = cfg.get(f"{section}.vol_percentile_low", None)
        vol_percentile_high = cfg.get(f"{section}.vol_percentile_high", None)
        lookback_percentile = cfg.get(f"{section}.lookback_percentile", 100)
        invert = cfg.get(f"{section}.invert", False)

        return cls(
            vol_window=vol_window,
            vol_method=vol_method,
            min_vol=min_vol,
            max_vol=max_vol,
            atr_threshold=atr_threshold,
            vol_percentile_low=vol_percentile_low,
            vol_percentile_high=vol_percentile_high,
            lookback_percentile=lookback_percentile,
            invert=invert,
        )

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

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.ewm(span=self.vol_window, min_periods=self.vol_window, adjust=False).mean()
        return atr

    def _compute_std(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet Standard-Abweichung der Returns.

        Args:
            data: DataFrame mit close

        Returns:
            Rolling Std als pd.Series
        """
        returns = data["close"].pct_change()
        vol = returns.rolling(window=self.vol_window, min_periods=self.vol_window).std()
        return vol

    def _compute_realized_vol(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet annualisierte Realized Volatility.

        Args:
            data: DataFrame mit close

        Returns:
            Realized Vol als pd.Series (annualisiert)
        """
        returns = data["close"].pct_change()
        # Rolling variance * sqrt(252) für annualisierung
        variance = returns.rolling(window=self.vol_window, min_periods=self.vol_window).var()
        realized_vol = np.sqrt(variance * 252)
        return realized_vol

    def _compute_volatility(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet Volatilität basierend auf vol_method.

        Args:
            data: DataFrame

        Returns:
            Volatilitäts-Serie
        """
        if self.vol_method == "atr":
            if "high" not in data.columns or "low" not in data.columns:
                # Fallback zu std wenn keine HLC-Daten
                return self._compute_std(data)
            return self._compute_atr(data)
        elif self.vol_method == "std":
            return self._compute_std(data)
        elif self.vol_method == "realized":
            return self._compute_realized_vol(data)
        else:
            raise ValueError(f"Unbekannte vol_method: {self.vol_method}")

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Filter-Signale basierend auf Volatilität.

        Args:
            data: DataFrame mit OHLCV-Daten

        Returns:
            Series mit Filter (1=Trading erlaubt, 0=blockiert)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        if "close" not in data.columns:
            raise ValueError(
                f"Spalte 'close' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        min_bars = max(self.vol_window, self.lookback_percentile) + 5
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mind. {min_bars} Bars, habe nur {len(data)}"
            )

        # Volatilität berechnen
        vol = self._compute_volatility(data)

        # Filter initialisieren (default: Trading erlaubt)
        filter_signal = pd.Series(1, index=data.index, dtype=int)

        # Perzentil-basierter Filter
        if self.vol_percentile_low is not None or self.vol_percentile_high is not None:
            # Rolling Perzentil berechnen
            vol_percentile = vol.rolling(
                window=self.lookback_percentile,
                min_periods=self.vol_window
            ).apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100,
                raw=False
            )

            if self.vol_percentile_low is not None:
                # Blockiere wenn Vol-Perzentil unter dem Minimum
                filter_signal = filter_signal.where(
                    vol_percentile >= self.vol_percentile_low, 0
                )

            if self.vol_percentile_high is not None:
                # Blockiere wenn Vol-Perzentil über dem Maximum
                filter_signal = filter_signal.where(
                    vol_percentile <= self.vol_percentile_high, 0
                )

        # Absoluter Schwellwert-Filter
        if self.min_vol is not None:
            filter_signal = filter_signal.where(vol >= self.min_vol, 0)

        if self.max_vol is not None:
            filter_signal = filter_signal.where(vol <= self.max_vol, 0)

        # ATR-Threshold-Filter
        if self.atr_threshold is not None:
            if self.vol_method != "atr":
                # Berechne ATR separat wenn andere Methode gewählt
                if "high" in data.columns and "low" in data.columns:
                    atr = self._compute_atr(data)
                    filter_signal = filter_signal.where(atr >= self.atr_threshold, 0)
            else:
                filter_signal = filter_signal.where(vol >= self.atr_threshold, 0)

        # Invertieren wenn gewünscht
        if self.invert:
            filter_signal = 1 - filter_signal

        # NaN am Anfang auf 0 setzen (während Warmup kein Trading)
        filter_signal = filter_signal.fillna(0).astype(int)

        filter_signal.name = "vol_filter"
        return filter_signal

    def apply_to_signals(
        self,
        data: pd.DataFrame,
        signals: pd.Series
    ) -> pd.Series:
        """
        Wendet den Filter auf existierende Trading-Signale an.

        Convenience-Methode die generate_signals() aufruft und
        mit den übergebenen Signalen multipliziert.

        Args:
            data: OHLCV-DataFrame
            signals: Trading-Signale einer anderen Strategie

        Returns:
            Gefilterte Signale (original * filter)

        Example:
            >>> breakout = BreakoutStrategy()
            >>> vol_filter = VolRegimeFilter(vol_percentile_low=25, vol_percentile_high=75)
            >>>
            >>> raw_signals = breakout.generate_signals(df)
            >>> filtered_signals = vol_filter.apply_to_signals(df, raw_signals)
        """
        filter_mask = self.generate_signals(data)

        # Signale und Filter auf gleichen Index bringen
        aligned_filter = filter_mask.reindex(signals.index, fill_value=0)

        # Multiplikation: Signal * Filter (0 blockiert, 1 erlaubt)
        filtered_signals = signals * aligned_filter

        return filtered_signals


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte VolRegimeFilter verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Filter-Series (1=erlaubt, 0=blockiert)
    """
    config = {
        "vol_window": params.get("vol_window", params.get("atr_window", 20)),
        "vol_method": params.get("vol_method", "atr"),
        "min_vol": params.get("min_vol", None),
        "max_vol": params.get("max_vol", None),
        "atr_threshold": params.get("atr_threshold", None),
        "vol_percentile_low": params.get("vol_percentile_low", None),
        "vol_percentile_high": params.get("vol_percentile_high", None),
        "lookback_percentile": params.get("lookback_percentile", 100),
        "invert": params.get("invert", False),
    }

    strategy = VolRegimeFilter(config=config)
    return strategy.generate_signals(df)


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    method = params.get("vol_method", "atr")
    min_vol = params.get("min_vol")
    max_vol = params.get("max_vol")
    p_low = params.get("vol_percentile_low")
    p_high = params.get("vol_percentile_high")

    return f"""
Volatility Regime Filter (Phase 40)
====================================
Vol Window:         {params.get('vol_window', 20)} Bars
Vol Method:         {method.upper()}
Min Vol:            {min_vol if min_vol else 'Deaktiviert'}
Max Vol:            {max_vol if max_vol else 'Deaktiviert'}
Percentile Low:     {p_low if p_low else 'Deaktiviert'}
Percentile High:    {p_high if p_high else 'Deaktiviert'}
Invert:             {'Ja' if params.get('invert', False) else 'Nein'}

Konzept:
- Berechnet Volatilität via {method.upper()}
- Trading erlaubt wenn Vol im konfigurierten Bereich
- Kann mit anderen Strategien kombiniert werden
"""
