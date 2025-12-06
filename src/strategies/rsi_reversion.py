# src/strategies/rsi_reversion.py
"""
Peak_Trade RSI Reversion Strategy (Phase 27 Enhanced)
=====================================================

RSI Mean-Reversion-Strategie mit optionalem Trendfilter.

Konzept:
- Long Entry: RSI < lower_threshold (überverkauft → erwarte Reversion nach oben)
- Short Entry: RSI > upper_threshold (überkauft → erwarte Reversion nach unten)
- Optional: Trendfilter über MA (nur Long wenn Preis > MA, nur Short wenn Preis < MA)

Diese Strategie eignet sich für seitwärts laufende (ranging) Märkte
und nutzt Übertreibungen (Oversold/Overbought) für Einstiege.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


class RsiReversionStrategy(BaseStrategy):
    """
    RSI Mean-Reversion Strategie (OOP-Version, Phase 27 erweitert).

    Signale:
    - 1 (long): RSI < lower (überverkauft → erwarte Reversion nach oben)
    - -1 (short): RSI > upper (überkauft → erwarte Reversion nach unten)
    - 0: Position halten / neutral

    Optionale Features:
    - Trendfilter: Nur Long wenn Preis > MA, nur Short wenn Preis < MA
    - Exit bei RSI-Neutralzone: Exit wenn RSI in neutralem Bereich
    - Wilder-Smoothing für stabilere RSI-Berechnung

    Args:
        rsi_window: Periode für RSI-Berechnung (default: 14)
        lower: Oversold-Level für Long-Entry (default: 30)
        upper: Overbought-Level für Short-Entry (default: 70)
        exit_lower: RSI-Level für Long-Exit (default: 50)
        exit_upper: RSI-Level für Short-Exit (default: 50)
        use_trend_filter: Ob MA-Trendfilter verwendet wird (default: False)
        trend_ma_window: Periode für Trend-MA (default: 50)
        use_wilder: Ob Wilder-Smoothing für RSI (default: True)
        price_col: Spalte für Preisdaten (default: "close")
        config: Optional Config-Dict (überschreibt Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = RsiReversionStrategy(rsi_window=14, lower=30, upper=70)
        >>> signals = strategy.generate_signals(df)

        >>> # Mit Trendfilter
        >>> strategy = RsiReversionStrategy(use_trend_filter=True, trend_ma_window=50)
    """

    KEY = "rsi_reversion"

    def __init__(
        self,
        rsi_window: int = 14,
        lower: float = 30.0,
        upper: float = 70.0,
        exit_lower: float = 50.0,
        exit_upper: float = 50.0,
        use_trend_filter: bool = False,
        trend_ma_window: int = 50,
        use_wilder: bool = True,
        price_col: str = "close",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert RSI Reversion Strategy.

        Args:
            rsi_window: RSI-Berechnungsperiode
            lower: Oversold-Level (Long Entry)
            upper: Overbought-Level (Short Entry)
            exit_lower: RSI-Level für Long-Exit
            exit_upper: RSI-Level für Short-Exit
            use_trend_filter: Aktiviert MA-Trendfilter
            trend_ma_window: MA-Periode für Trendfilter
            use_wilder: Verwendet Wilder-Smoothing (stabiler)
            price_col: Preis-Spalte
            config: Optional Config-Dict
            metadata: Optional Metadata
        """
        base_cfg: Dict[str, Any] = {
            "rsi_window": rsi_window,
            "lower": lower,
            "upper": upper,
            "exit_lower": exit_lower,
            "exit_upper": exit_upper,
            "use_trend_filter": use_trend_filter,
            "trend_ma_window": trend_ma_window,
            "use_wilder": use_wilder,
            "price_col": price_col,
        }
        if config:
            base_cfg.update(config)

        meta = metadata or StrategyMetadata(
            name="RSI Reversion",
            description="RSI Mean-Reversion-Strategie mit optionalem Trendfilter (Phase 27)",
            version="2.0.0",
            author="Peak_Trade",
            regime="ranging",
            tags=["mean_reversion", "rsi", "oversold", "overbought"],
        )

        super().__init__(config=base_cfg, metadata=meta)

        # Parameter extrahieren
        self.rsi_window = int(self.config["rsi_window"])
        self.lower = float(self.config["lower"])
        self.upper = float(self.config["upper"])
        self.exit_lower = float(self.config.get("exit_lower", 50.0))
        self.exit_upper = float(self.config.get("exit_upper", 50.0))
        self.use_trend_filter = bool(self.config.get("use_trend_filter", False))
        self.trend_ma_window = int(self.config.get("trend_ma_window", 50))
        self.use_wilder = bool(self.config.get("use_wilder", True))
        self.price_col = str(self.config["price_col"])

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.rsi_window < 2:
            raise ValueError(f"rsi_window ({self.rsi_window}) muss >= 2 sein")
        if not (0 <= self.lower < self.upper <= 100):
            raise ValueError(
                f"lower ({self.lower}) und upper ({self.upper}) müssen "
                "0 <= lower < upper <= 100 erfüllen"
            )
        if self.trend_ma_window < 2:
            raise ValueError(f"trend_ma_window ({self.trend_ma_window}) muss >= 2 sein")

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.rsi_reversion",
    ) -> "RsiReversionStrategy":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            RsiReversionStrategy-Instanz
        """
        window = cfg.get(f"{section}.rsi_window", 14)
        lower = cfg.get(f"{section}.lower", 30.0)
        upper = cfg.get(f"{section}.upper", 70.0)
        exit_lower = cfg.get(f"{section}.exit_lower", 50.0)
        exit_upper = cfg.get(f"{section}.exit_upper", 50.0)
        use_trend_filter = cfg.get(f"{section}.use_trend_filter", False)
        trend_ma_window = cfg.get(f"{section}.trend_ma_window", 50)
        use_wilder = cfg.get(f"{section}.use_wilder", True)
        price = cfg.get(f"{section}.price_col", "close")

        return cls(
            rsi_window=window,
            lower=lower,
            upper=upper,
            exit_lower=exit_lower,
            exit_upper=exit_upper,
            use_trend_filter=use_trend_filter,
            trend_ma_window=trend_ma_window,
            use_wilder=use_wilder,
            price_col=price,
        )

    def _compute_rsi(self, price: pd.Series) -> pd.Series:
        """
        Berechnet den RSI (Relative Strength Index).

        Unterstützt:
        - Wilder-Smoothing (EMA-basiert, stabiler)
        - Simple Rolling (schneller, aber volatiler)

        Args:
            price: Preis-Serie

        Returns:
            RSI-Serie (0-100)
        """
        delta = price.diff()

        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)

        if self.use_wilder:
            # Wilder-Smoothing (EMA mit alpha=1/n)
            avg_gain = gain.ewm(
                alpha=1/self.rsi_window,
                min_periods=self.rsi_window,
                adjust=False
            ).mean()
            avg_loss = loss.ewm(
                alpha=1/self.rsi_window,
                min_periods=self.rsi_window,
                adjust=False
            ).mean()
        else:
            # Simple Rolling Mean
            avg_gain = gain.rolling(self.rsi_window, min_periods=self.rsi_window).mean()
            avg_loss = loss.rolling(self.rsi_window, min_periods=self.rsi_window).mean()

        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit price_col (default: close)

        Returns:
            Series mit Signalen (1=long, -1=short, 0=flat)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        if self.price_col not in data.columns:
            raise ValueError(
                f"Spalte '{self.price_col}' nicht im DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        min_bars = max(self.rsi_window, self.trend_ma_window if self.use_trend_filter else 0) + 5
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mind. {min_bars} Bars, habe nur {len(data)}"
            )

        price = data[self.price_col].astype(float)
        rsi = self._compute_rsi(price)

        # Trend-MA für optionalen Filter
        if self.use_trend_filter:
            trend_ma = price.rolling(window=self.trend_ma_window).mean()
            price_above_ma = price > trend_ma
            price_below_ma = price < trend_ma
        else:
            price_above_ma = pd.Series(True, index=data.index)
            price_below_ma = pd.Series(True, index=data.index)

        # Entry-Bedingungen
        # Long: RSI < lower UND (kein Trendfilter ODER Preis > MA)
        long_entry = (rsi < self.lower) & price_above_ma

        # Short: RSI > upper UND (kein Trendfilter ODER Preis < MA)
        short_entry = (rsi > self.upper) & price_below_ma

        # Exit-Bedingungen (RSI zurück in neutralen Bereich)
        exit_long = rsi >= self.exit_lower
        exit_short = rsi <= self.exit_upper

        # State-Tracking
        state = pd.Series(0, index=data.index, dtype=int)
        current_state = 0

        for i in range(len(data)):
            # Prüfe Entry/Exit
            if current_state == 0:
                # Neutral → prüfe Entry
                if long_entry.iloc[i]:
                    current_state = 1
                elif short_entry.iloc[i]:
                    current_state = -1
            elif current_state == 1:
                # Long → prüfe Exit oder Umkehr
                if exit_long.iloc[i]:
                    current_state = 0
                if short_entry.iloc[i]:
                    current_state = -1
            elif current_state == -1:
                # Short → prüfe Exit oder Umkehr
                if exit_short.iloc[i]:
                    current_state = 0
                if long_entry.iloc[i]:
                    current_state = 1

            state.iloc[i] = current_state

        state.name = "signal"
        return state


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte RsiReversionStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (1=long, -1=short, 0=flat)
    """
    config = {
        "rsi_window": params.get("rsi_window", params.get("rsi_period", 14)),
        "lower": params.get("lower", params.get("oversold", 30.0)),
        "upper": params.get("upper", params.get("overbought", 70.0)),
        "exit_lower": params.get("exit_lower", 50.0),
        "exit_upper": params.get("exit_upper", 50.0),
        "use_trend_filter": params.get("use_trend_filter", False),
        "trend_ma_window": params.get("trend_ma_window", 50),
        "use_wilder": params.get("use_wilder", True),
        "price_col": params.get("price_col", "close"),
    }

    strategy = RsiReversionStrategy(config=config)
    return strategy.generate_signals(df)


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    trend_filter = "Aktiv" if params.get('use_trend_filter', False) else "Inaktiv"
    return f"""
RSI Mean-Reversion Strategy (Phase 27)
======================================
RSI Window:        {params.get('rsi_window', 14)} Bars
Lower (Oversold):  {params.get('lower', 30.0)}
Upper (Overbought):{params.get('upper', 70.0)}
Exit Lower:        {params.get('exit_lower', 50.0)}
Exit Upper:        {params.get('exit_upper', 50.0)}
Trend-Filter:      {trend_filter}
Trend-MA Window:   {params.get('trend_ma_window', 50)} Bars
Wilder-Smoothing:  {'Ja' if params.get('use_wilder', True) else 'Nein'}

Konzept:
- Entry Long:  RSI < {params.get('lower', 30.0)} (überverkauft)
- Entry Short: RSI > {params.get('upper', 70.0)} (überkauft)
- Exit:        RSI zurück in neutralen Bereich
"""
