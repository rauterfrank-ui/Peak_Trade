# src/strategies/breakout.py
"""
Peak_Trade Breakout/Momentum Strategy (Phase 40)
=================================================

Trend-Following Breakout-Strategie mit Stop-Loss, Take-Profit und Trailing-Stop.

Konzept:
- Long Entry: Close > N-Bars-High (Breakout nach oben)
- Short Entry: Close < N-Bars-Low (Breakout nach unten)
- Exit: Stop-Loss, Take-Profit oder Trailing-Stop

Diese Strategie eignet sich für Trending-Märkte und nutzt
Breakouts aus Konsolidierungsphasen.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


class BreakoutStrategy(BaseStrategy):
    """
    Breakout/Momentum Trend-Following Strategy (Phase 40).

    Signale:
    - 1 (long): Close > N-Bars-High (Upward Breakout)
    - -1 (short): Close < N-Bars-Low (Downward Breakout)
    - 0: Flat / keine Position

    Features:
    - Konfigurierbares Lookback-Fenster für Breakout-Levels
    - Stop-Loss als prozentualer Abstand vom Entry
    - Take-Profit als prozentualer Abstand vom Entry
    - Optional: Trailing-Stop (nachlaufender Stop)
    - Long-Only oder Short-Only Mode möglich

    Args:
        lookback_breakout: Lookback-Fenster für Hoch/Tief (default: 20)
        stop_loss_pct: Stop-Loss in % vom Entry (default: None = kein SL)
        take_profit_pct: Take-Profit in % vom Entry (default: None = kein TP)
        trailing_stop_pct: Trailing-Stop in % vom Peak (default: None)
        side: Trading-Richtung ("long", "short", "both") (default: "both")
        price_col: Spalte für Close-Preis (default: "close")
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = BreakoutStrategy(lookback_breakout=20, stop_loss_pct=0.03)
        >>> signals = strategy.generate_signals(df)

        >>> # Long-Only mit Trailing-Stop
        >>> strategy = BreakoutStrategy(
        ...     lookback_breakout=15,
        ...     trailing_stop_pct=0.02,
        ...     side="long"
        ... )
    """

    KEY = "breakout"

    def __init__(
        self,
        lookback_breakout: int = 20,
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
        trailing_stop_pct: Optional[float] = None,
        side: str = "both",
        price_col: str = "close",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Breakout Strategy.

        Args:
            lookback_breakout: Fenster für Breakout-Level-Berechnung
            stop_loss_pct: Stop-Loss als Dezimalzahl (0.03 = 3%)
            take_profit_pct: Take-Profit als Dezimalzahl (0.06 = 6%)
            trailing_stop_pct: Trailing-Stop als Dezimalzahl
            side: "long", "short", oder "both"
            price_col: Name der Close-Spalte
            config: Optional Config-Dict
            metadata: Optional Metadata
        """
        base_cfg: Dict[str, Any] = {
            "lookback_breakout": lookback_breakout,
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
            "trailing_stop_pct": trailing_stop_pct,
            "side": side,
            "price_col": price_col,
        }
        if config:
            base_cfg.update(config)

        meta = metadata or StrategyMetadata(
            name="Breakout Strategy",
            description="Trend-Following Breakout-Strategie mit SL/TP (Phase 40)",
            version="1.0.0",
            author="Peak_Trade",
            regime="trending",
            tags=["breakout", "trend_following", "momentum"],
        )

        super().__init__(config=base_cfg, metadata=meta)

        # Parameter extrahieren
        self.lookback_breakout = int(self.config["lookback_breakout"])
        self.stop_loss_pct = self.config.get("stop_loss_pct")
        self.take_profit_pct = self.config.get("take_profit_pct")
        self.trailing_stop_pct = self.config.get("trailing_stop_pct")
        self.side = str(self.config.get("side", "both")).lower()
        self.price_col = str(self.config["price_col"])

        # Optional: Als float konvertieren wenn nicht None
        if self.stop_loss_pct is not None:
            self.stop_loss_pct = float(self.stop_loss_pct)
        if self.take_profit_pct is not None:
            self.take_profit_pct = float(self.take_profit_pct)
        if self.trailing_stop_pct is not None:
            self.trailing_stop_pct = float(self.trailing_stop_pct)

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.lookback_breakout < 2:
            raise ValueError(
                f"lookback_breakout ({self.lookback_breakout}) muss >= 2 sein"
            )
        if self.side not in ("long", "short", "both"):
            raise ValueError(
                f"side ({self.side}) muss 'long', 'short' oder 'both' sein"
            )
        if self.stop_loss_pct is not None and self.stop_loss_pct <= 0:
            raise ValueError(
                f"stop_loss_pct ({self.stop_loss_pct}) muss > 0 sein"
            )
        if self.take_profit_pct is not None and self.take_profit_pct <= 0:
            raise ValueError(
                f"take_profit_pct ({self.take_profit_pct}) muss > 0 sein"
            )
        if self.trailing_stop_pct is not None and self.trailing_stop_pct <= 0:
            raise ValueError(
                f"trailing_stop_pct ({self.trailing_stop_pct}) muss > 0 sein"
            )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.breakout",
    ) -> "BreakoutStrategy":
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            BreakoutStrategy-Instanz
        """
        lookback = cfg.get(f"{section}.lookback_breakout", 20)
        stop_loss = cfg.get(f"{section}.stop_loss_pct", None)
        take_profit = cfg.get(f"{section}.take_profit_pct", None)
        trailing = cfg.get(f"{section}.trailing_stop_pct", None)
        side = cfg.get(f"{section}.side", "both")
        price = cfg.get(f"{section}.price_col", "close")

        return cls(
            lookback_breakout=lookback,
            stop_loss_pct=stop_loss,
            take_profit_pct=take_profit,
            trailing_stop_pct=trailing,
            side=side,
            price_col=price,
        )

    def _compute_breakout_levels(
        self, data: pd.DataFrame
    ) -> tuple[pd.Series, pd.Series]:
        """
        Berechnet Breakout-Levels (N-Bar Hoch und Tief).

        Args:
            data: DataFrame mit high, low Spalten

        Returns:
            (upper_level, lower_level) als pd.Series
        """
        # Verwende high/low wenn verfügbar, sonst close
        if "high" in data.columns and "low" in data.columns:
            high = data["high"]
            low = data["low"]
        else:
            high = data[self.price_col]
            low = data[self.price_col]

        # Rolling High/Low (exklusive aktuelle Bar für sauberes Signal)
        upper_level = high.shift(1).rolling(
            window=self.lookback_breakout,
            min_periods=self.lookback_breakout
        ).max()

        lower_level = low.shift(1).rolling(
            window=self.lookback_breakout,
            min_periods=self.lookback_breakout
        ).min()

        return upper_level, lower_level

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Diese Methode implementiert:
        1. Breakout-Erkennung über N-Bar Hoch/Tief
        2. Stop-Loss-Exits bei Unterschreitung
        3. Take-Profit-Exits bei Zielerreichung
        4. Trailing-Stop-Logik

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens close)

        Returns:
            Series mit Signalen (1=long, -1=short, 0=flat)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        # Validierung
        if self.price_col not in data.columns:
            raise ValueError(
                f"Spalte '{self.price_col}' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        min_bars = self.lookback_breakout + 5
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mind. {min_bars} Bars, habe nur {len(data)}"
            )

        close = data[self.price_col].astype(float)

        # Breakout-Levels berechnen
        upper_level, lower_level = self._compute_breakout_levels(data)

        # Für Stop-Loss/Take-Profit brauchen wir low/high
        if "low" in data.columns:
            low = data["low"].astype(float)
        else:
            low = close
        if "high" in data.columns:
            high = data["high"].astype(float)
        else:
            high = close

        # State-Machine für Position-Tracking mit SL/TP/Trailing
        signals = pd.Series(0, index=data.index, dtype=int)
        state = 0  # 0=flat, 1=long, -1=short
        entry_price = 0.0
        peak_price = 0.0  # Für Trailing-Stop

        for i in range(len(data)):
            current_close = close.iloc[i]
            current_high = high.iloc[i]
            current_low = low.iloc[i]
            upper = upper_level.iloc[i]
            lower = lower_level.iloc[i]

            # Skip wenn keine gültigen Levels (Warmup-Phase)
            if pd.isna(upper) or pd.isna(lower):
                signals.iloc[i] = state
                continue

            # Exit-Logik zuerst prüfen (wichtiger als Entry)
            if state == 1:  # Long Position
                exit_trade = False

                # Stop-Loss Check
                if self.stop_loss_pct is not None:
                    stop_price = entry_price * (1 - self.stop_loss_pct)
                    if current_low <= stop_price:
                        exit_trade = True

                # Take-Profit Check
                if self.take_profit_pct is not None and not exit_trade:
                    tp_price = entry_price * (1 + self.take_profit_pct)
                    if current_high >= tp_price:
                        exit_trade = True

                # Trailing-Stop Check
                if self.trailing_stop_pct is not None and not exit_trade:
                    # Peak aktualisieren
                    if current_high > peak_price:
                        peak_price = current_high
                    trailing_stop_price = peak_price * (1 - self.trailing_stop_pct)
                    if current_low <= trailing_stop_price:
                        exit_trade = True

                # Breakout in Gegenrichtung (Short-Signal)
                if self.side in ("short", "both") and current_close < lower:
                    exit_trade = True
                    # Wechsel zu Short
                    state = -1
                    entry_price = current_close
                    peak_price = current_close
                    signals.iloc[i] = state
                    continue

                if exit_trade:
                    state = 0
                    entry_price = 0.0
                    peak_price = 0.0

            elif state == -1:  # Short Position
                exit_trade = False

                # Stop-Loss Check (für Short: Preis steigt)
                if self.stop_loss_pct is not None:
                    stop_price = entry_price * (1 + self.stop_loss_pct)
                    if current_high >= stop_price:
                        exit_trade = True

                # Take-Profit Check (für Short: Preis fällt)
                if self.take_profit_pct is not None and not exit_trade:
                    tp_price = entry_price * (1 - self.take_profit_pct)
                    if current_low <= tp_price:
                        exit_trade = True

                # Trailing-Stop Check (für Short: Peak = niedrigster Preis)
                if self.trailing_stop_pct is not None and not exit_trade:
                    if current_low < peak_price:
                        peak_price = current_low
                    trailing_stop_price = peak_price * (1 + self.trailing_stop_pct)
                    if current_high >= trailing_stop_price:
                        exit_trade = True

                # Breakout in Gegenrichtung (Long-Signal)
                if self.side in ("long", "both") and current_close > upper:
                    exit_trade = True
                    # Wechsel zu Long
                    state = 1
                    entry_price = current_close
                    peak_price = current_close
                    signals.iloc[i] = state
                    continue

                if exit_trade:
                    state = 0
                    entry_price = 0.0
                    peak_price = 0.0

            # Entry-Logik wenn flat
            if state == 0:
                # Long Entry
                if self.side in ("long", "both") and current_close > upper:
                    state = 1
                    entry_price = current_close
                    peak_price = current_close

                # Short Entry
                elif self.side in ("short", "both") and current_close < lower:
                    state = -1
                    entry_price = current_close
                    peak_price = current_close

            signals.iloc[i] = state

        signals.name = "signal"
        return signals


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte BreakoutStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (1=long, -1=short, 0=flat)
    """
    config = {
        "lookback_breakout": params.get("lookback_breakout", 20),
        "stop_loss_pct": params.get("stop_loss_pct", None),
        "take_profit_pct": params.get("take_profit_pct", None),
        "trailing_stop_pct": params.get("trailing_stop_pct", None),
        "side": params.get("side", "both"),
        "price_col": params.get("price_col", "close"),
    }

    strategy = BreakoutStrategy(config=config)
    return strategy.generate_signals(df)


def get_strategy_description(params: Dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    sl = params.get("stop_loss_pct")
    tp = params.get("take_profit_pct")
    ts = params.get("trailing_stop_pct")

    sl_str = f"{sl*100:.1f}%" if sl else "Deaktiviert"
    tp_str = f"{tp*100:.1f}%" if tp else "Deaktiviert"
    ts_str = f"{ts*100:.1f}%" if ts else "Deaktiviert"

    return f"""
Breakout/Momentum Strategy (Phase 40)
======================================
Lookback Breakout: {params.get('lookback_breakout', 20)} Bars
Stop-Loss:         {sl_str}
Take-Profit:       {tp_str}
Trailing-Stop:     {ts_str}
Side:              {params.get('side', 'both')}

Konzept:
- Entry Long:  Close > {params.get('lookback_breakout', 20)}-Bar High
- Entry Short: Close < {params.get('lookback_breakout', 20)}-Bar Low
- Exit:        Stop-Loss, Take-Profit oder Trailing-Stop
"""
