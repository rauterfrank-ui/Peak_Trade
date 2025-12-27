# src/strategies/breakout.py
"""
Peak_Trade Breakout/Momentum Strategy (Phase 40+)
==================================================

Trend-Following Breakout-Strategie mit Stop-Loss, Take-Profit und Trailing-Stop.
Erweitert um ATR-Filter und erweiterte Breakout-Logik.

Konzept:
- Long Entry: Close > N-Bars-High (Breakout nach oben)
- Short Entry: Close < N-Bars-Low (Breakout nach unten)
- Optional: ATR-Filter zur Vermeidung von Noise-Breakouts
- Exit: Stop-Loss, Take-Profit, Trailing-Stop oder opposite Breakout

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
    Breakout/Momentum Trend-Following Strategy (Phase 40+).

    Signale:
    - 1 (long): Close > N-Bars-High (Upward Breakout)
    - -1 (short): Close < N-Bars-Low (Downward Breakout)
    - 0: Flat / keine Position

    Features:
    - Konfigurierbares Lookback-Fenster für Breakout-Levels
    - Separate Lookback-Perioden für Long/Short möglich
    - Optional: ATR-Filter zur Vermeidung von Noise-Breakouts
    - Stop-Loss als prozentualer Abstand vom Entry
    - Take-Profit als prozentualer Abstand vom Entry
    - Optional: Trailing-Stop (nachlaufender Stop)
    - Exit bei gegenteiligem Breakout optional
    - Long-Only, Short-Only oder Symmetric Mode

    Args:
        lookback_breakout: Lookback-Fenster für Hoch/Tief (default: 20)
        lookback_high: Separates Lookback für Long-Breakout (default: None = lookback_breakout)
        lookback_low: Separates Lookback für Short-Breakout (default: None = lookback_breakout)
        atr_lookback: ATR-Fenster für Filter (default: 14)
        atr_multiplier: Mindest-ATR-Level für validen Breakout (default: None = kein Filter)
        use_atr_filter: ATR-Filter an-/abschalten (default: False)
        exit_on_opposite_breakout: Exit bei gegenteiligem Breakout (default: True)
        risk_mode: Trading-Modus ("symmetric", "long_only", "short_only") (default: "symmetric")
        side: Legacy-Parameter für Trading-Richtung ("long", "short", "both") (default: None)
        stop_loss_pct: Stop-Loss in % vom Entry (default: None = kein SL)
        take_profit_pct: Take-Profit in % vom Entry (default: None = kein TP)
        trailing_stop_pct: Trailing-Stop in % vom Peak (default: None)
        price_col: Spalte für Close-Preis (default: "close")
        config: Optional Config-Dict
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = BreakoutStrategy(lookback_breakout=20, stop_loss_pct=0.03)
        >>> signals = strategy.generate_signals(df)

        >>> # Mit ATR-Filter und separaten Lookbacks
        >>> strategy = BreakoutStrategy(
        ...     lookback_high=20,
        ...     lookback_low=15,
        ...     use_atr_filter=True,
        ...     atr_multiplier=1.0,
        ...     risk_mode="symmetric"
        ... )
    """

    KEY = "breakout"

    def __init__(
        self,
        lookback_breakout: int = 20,
        lookback_high: Optional[int] = None,
        lookback_low: Optional[int] = None,
        atr_lookback: int = 14,
        atr_multiplier: Optional[float] = None,
        use_atr_filter: bool = False,
        exit_on_opposite_breakout: bool = True,
        risk_mode: str = "symmetric",
        side: Optional[str] = None,
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
        trailing_stop_pct: Optional[float] = None,
        price_col: str = "close",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Breakout Strategy.

        Args:
            lookback_breakout: Standard-Fenster für Breakout-Level-Berechnung
            lookback_high: Separates Lookback für Long-Breakout
            lookback_low: Separates Lookback für Short-Breakout
            atr_lookback: ATR-Fenster für Filter
            atr_multiplier: Mindest-ATR-Level für validen Breakout
            use_atr_filter: ATR-Filter aktivieren
            exit_on_opposite_breakout: Exit bei gegenteiligem Breakout
            risk_mode: "symmetric", "long_only", "short_only"
            side: Legacy-Parameter für Kompatibilität
            stop_loss_pct: Stop-Loss als Dezimalzahl (0.03 = 3%)
            take_profit_pct: Take-Profit als Dezimalzahl (0.06 = 6%)
            trailing_stop_pct: Trailing-Stop als Dezimalzahl
            price_col: Name der Close-Spalte
            config: Optional Config-Dict
            metadata: Optional Metadata
        """
        base_cfg: Dict[str, Any] = {
            "lookback_breakout": lookback_breakout,
            "lookback_high": lookback_high,
            "lookback_low": lookback_low,
            "atr_lookback": atr_lookback,
            "atr_multiplier": atr_multiplier,
            "use_atr_filter": use_atr_filter,
            "exit_on_opposite_breakout": exit_on_opposite_breakout,
            "risk_mode": risk_mode,
            "side": side,  # Legacy support
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
            "trailing_stop_pct": trailing_stop_pct,
            "price_col": price_col,
        }
        if config:
            base_cfg.update(config)

        meta = metadata or StrategyMetadata(
            name="Breakout Strategy",
            description="Trend-Following Breakout-Strategie mit SL/TP/ATR-Filter (Phase 40+)",
            version="2.0.0",
            author="Peak_Trade",
            regime="trending",
            tags=["breakout", "trend_following", "momentum", "atr_filter"],
        )

        super().__init__(config=base_cfg, metadata=meta)

        # Parameter extrahieren
        self.lookback_breakout = int(self.config.get("lookback_breakout", 20))
        self.lookback_high = self.config.get("lookback_high")
        self.lookback_low = self.config.get("lookback_low")
        self.atr_lookback = int(self.config.get("atr_lookback", 14))
        self.atr_multiplier = self.config.get("atr_multiplier")
        self.use_atr_filter = bool(self.config.get("use_atr_filter", False))
        self.exit_on_opposite_breakout = bool(self.config.get("exit_on_opposite_breakout", True))
        self.risk_mode = str(self.config.get("risk_mode", "symmetric")).lower()
        self.stop_loss_pct = self.config.get("stop_loss_pct")
        self.take_profit_pct = self.config.get("take_profit_pct")
        self.trailing_stop_pct = self.config.get("trailing_stop_pct")
        self.price_col = str(self.config.get("price_col", "close"))

        # Legacy: side -> risk_mode Mapping
        legacy_side = self.config.get("side")
        if legacy_side and self.risk_mode == "symmetric":
            legacy_side = str(legacy_side).lower()
            if legacy_side == "long":
                self.risk_mode = "long_only"
            elif legacy_side == "short":
                self.risk_mode = "short_only"
            elif legacy_side == "both":
                self.risk_mode = "symmetric"

        # Lookbacks setzen (wenn nicht separat angegeben, verwende lookback_breakout)
        if self.lookback_high is None:
            self.lookback_high = self.lookback_breakout
        else:
            self.lookback_high = int(self.lookback_high)

        if self.lookback_low is None:
            self.lookback_low = self.lookback_breakout
        else:
            self.lookback_low = int(self.lookback_low)

        # Optional: Als float konvertieren wenn nicht None
        if self.stop_loss_pct is not None:
            self.stop_loss_pct = float(self.stop_loss_pct)
        if self.take_profit_pct is not None:
            self.take_profit_pct = float(self.take_profit_pct)
        if self.trailing_stop_pct is not None:
            self.trailing_stop_pct = float(self.trailing_stop_pct)
        if self.atr_multiplier is not None:
            self.atr_multiplier = float(self.atr_multiplier)

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.lookback_breakout < 2:
            raise ValueError(f"lookback_breakout ({self.lookback_breakout}) muss >= 2 sein")
        if self.lookback_high < 2:
            raise ValueError(f"lookback_high ({self.lookback_high}) muss >= 2 sein")
        if self.lookback_low < 2:
            raise ValueError(f"lookback_low ({self.lookback_low}) muss >= 2 sein")
        if self.risk_mode not in ("symmetric", "long_only", "short_only"):
            raise ValueError(
                f"risk_mode ({self.risk_mode}) muss 'symmetric', 'long_only' oder 'short_only' sein"
            )
        if self.atr_lookback < 2:
            raise ValueError(f"atr_lookback ({self.atr_lookback}) muss >= 2 sein")
        if self.use_atr_filter and self.atr_multiplier is not None and self.atr_multiplier <= 0:
            raise ValueError(
                f"atr_multiplier ({self.atr_multiplier}) muss > 0 sein wenn use_atr_filter=True"
            )
        if self.stop_loss_pct is not None and self.stop_loss_pct <= 0:
            raise ValueError(f"stop_loss_pct ({self.stop_loss_pct}) muss > 0 sein")
        if self.take_profit_pct is not None and self.take_profit_pct <= 0:
            raise ValueError(f"take_profit_pct ({self.take_profit_pct}) muss > 0 sein")
        if self.trailing_stop_pct is not None and self.trailing_stop_pct <= 0:
            raise ValueError(f"trailing_stop_pct ({self.trailing_stop_pct}) muss > 0 sein")

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
        lookback_high = cfg.get(f"{section}.lookback_high", None)
        lookback_low = cfg.get(f"{section}.lookback_low", None)
        atr_lookback = cfg.get(f"{section}.atr_lookback", 14)
        atr_multiplier = cfg.get(f"{section}.atr_multiplier", None)
        use_atr_filter = cfg.get(f"{section}.use_atr_filter", False)
        exit_on_opposite_breakout = cfg.get(f"{section}.exit_on_opposite_breakout", True)
        risk_mode = cfg.get(f"{section}.risk_mode", None)
        side = cfg.get(f"{section}.side", None)  # Legacy support
        stop_loss = cfg.get(f"{section}.stop_loss_pct", None)
        take_profit = cfg.get(f"{section}.take_profit_pct", None)
        trailing = cfg.get(f"{section}.trailing_stop_pct", None)
        price = cfg.get(f"{section}.price_col", "close")

        # Legacy: side -> risk_mode
        if risk_mode is None:
            if side == "long":
                risk_mode = "long_only"
            elif side == "short":
                risk_mode = "short_only"
            elif side == "both":
                risk_mode = "symmetric"
            else:
                risk_mode = "symmetric"

        return cls(
            lookback_breakout=lookback,
            lookback_high=lookback_high,
            lookback_low=lookback_low,
            atr_lookback=atr_lookback,
            atr_multiplier=atr_multiplier,
            use_atr_filter=use_atr_filter,
            exit_on_opposite_breakout=exit_on_opposite_breakout,
            risk_mode=risk_mode,
            side=side,
            stop_loss_pct=stop_loss,
            take_profit_pct=take_profit,
            trailing_stop_pct=trailing,
            price_col=price,
        )

    def _compute_atr(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet Average True Range (ATR).

        Args:
            data: DataFrame mit high, low, close

        Returns:
            ATR als pd.Series
        """
        if "high" not in data.columns or "low" not in data.columns:
            # Fallback: verwende Close-Volatilität
            close = data[self.price_col]
            return (
                close.diff()
                .abs()
                .rolling(window=self.atr_lookback, min_periods=self.atr_lookback)
                .mean()
            )

        high = data["high"]
        low = data["low"]
        close = data[self.price_col]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Wilder-Smoothing (EMA mit alpha=1/n)
        atr = tr.ewm(
            alpha=1 / self.atr_lookback, min_periods=self.atr_lookback, adjust=False
        ).mean()

        return atr

    def _compute_breakout_levels(self, data: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
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

        # Rolling High/Low mit separaten Lookbacks
        # (exklusive aktuelle Bar für sauberes Signal)
        upper_level = (
            high.shift(1).rolling(window=self.lookback_high, min_periods=self.lookback_high).max()
        )

        lower_level = (
            low.shift(1).rolling(window=self.lookback_low, min_periods=self.lookback_low).min()
        )

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
                f"Spalte '{self.price_col}' nicht in DataFrame. Verfügbar: {list(data.columns)}"
            )

        # Mindestanzahl Bars berechnen
        min_bars = max(self.lookback_high, self.lookback_low, self.atr_lookback) + 5
        if len(data) < min_bars:
            raise ValueError(f"Brauche mind. {min_bars} Bars, habe nur {len(data)}")

        close = data[self.price_col].astype(float)

        # Breakout-Levels berechnen
        upper_level, lower_level = self._compute_breakout_levels(data)

        # ATR für Filter berechnen (falls aktiviert)
        atr = None
        atr_baseline = None
        if self.use_atr_filter:
            atr = self._compute_atr(data)
            if self.atr_multiplier is not None:
                # ATR-Baseline als Rolling-Mean der ATR
                atr_baseline = atr.rolling(
                    window=self.atr_lookback * 2, min_periods=self.atr_lookback
                ).mean()

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

            # ATR-Filter-Check für Entry-Signale
            atr_valid = True
            if self.use_atr_filter and atr is not None:
                current_atr = atr.iloc[i]
                if pd.isna(current_atr):
                    atr_valid = False
                elif self.atr_multiplier is not None and atr_baseline is not None:
                    baseline = atr_baseline.iloc[i]
                    if pd.isna(baseline):
                        atr_valid = False
                    else:
                        # Breakout nur valid wenn ATR > multiplier * baseline
                        atr_valid = current_atr >= (self.atr_multiplier * baseline)
                elif self.atr_multiplier is not None:
                    # Fallback: absolute Threshold (wenn kein Baseline)
                    # Hier könnte man auch einfach prüfen ob ATR > 0
                    atr_valid = True

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
                if self.exit_on_opposite_breakout:
                    if self.risk_mode in ("symmetric", "short_only") and current_close < lower:
                        exit_trade = True
                        # Wenn symmetric: Wechsel zu Short
                        if self.risk_mode == "symmetric":
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
                if self.exit_on_opposite_breakout:
                    if self.risk_mode in ("symmetric", "long_only") and current_close > upper:
                        exit_trade = True
                        # Wenn symmetric: Wechsel zu Long
                        if self.risk_mode == "symmetric":
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
                # Long Entry (mit ATR-Filter)
                if self.risk_mode in ("symmetric", "long_only") and current_close > upper:
                    if atr_valid:
                        state = 1
                        entry_price = current_close
                        peak_price = current_close

                # Short Entry (mit ATR-Filter)
                elif self.risk_mode in ("symmetric", "short_only") and current_close < lower:
                    if atr_valid:
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

    sl_str = f"{sl * 100:.1f}%" if sl else "Deaktiviert"
    tp_str = f"{tp * 100:.1f}%" if tp else "Deaktiviert"
    ts_str = f"{ts * 100:.1f}%" if ts else "Deaktiviert"

    return f"""
Breakout/Momentum Strategy (Phase 40)
======================================
Lookback Breakout: {params.get("lookback_breakout", 20)} Bars
Stop-Loss:         {sl_str}
Take-Profit:       {tp_str}
Trailing-Stop:     {ts_str}
Side:              {params.get("side", "both")}

Konzept:
- Entry Long:  Close > {params.get("lookback_breakout", 20)}-Bar High
- Entry Short: Close < {params.get("lookback_breakout", 20)}-Bar Low
- Exit:        Stop-Loss, Take-Profit oder Trailing-Stop
"""
