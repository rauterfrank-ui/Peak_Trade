# src/strategies/my_strategy.py
"""
Peak_Trade Volatility Breakout Strategy
========================================
Volatility-Breakout-Strategie basierend auf ATR (Average True Range).

Konzept:
- Long-Entry: Preis durchbricht obere Volatilitätsband (Close > MA + ATR * multiplier)
- Exit: Preis fällt unter untere Schwelle (Close < MA - ATR * exit_multiplier)

ATR misst die durchschnittliche Handelsspanne und dient als dynamisches
Volatilitätsmaß. Breakouts über das ATR-Band signalisieren potenzielle
Trendbewegungen.

Diese Strategie eignet sich für Märkte mit klaren Ausbrüchen nach
Konsolidierungsphasen.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseStrategy, StrategyMetadata


class MyStrategy(BaseStrategy):
    """
    ATR-basierte Volatility-Breakout-Strategie (OOP-Version).

    Signale:
    - 1 (long): Close > MA + (ATR * entry_multiplier) (Breakout nach oben)
    - -1 (exit): Close < MA - (ATR * exit_multiplier) (Rückfall unter Band)
    - 0: Keine Änderung

    Die Strategie nutzt ATR als dynamisches Volatilitätsmaß, um
    Breakout-Signale zu generieren, die sich automatisch an die
    aktuelle Marktvolatilität anpassen.

    Args:
        lookback_window: Periode für MA und ATR-Berechnung (default: 20)
        entry_multiplier: ATR-Multiplikator für Entry-Band (default: 1.5)
        exit_multiplier: ATR-Multiplikator für Exit-Band (default: 0.5)
        use_close_only: Wenn True, nur Close für ATR verwenden (default: False)
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = MyStrategy(lookback_window=20, entry_multiplier=1.5)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = MyStrategy.from_config(config, "strategy.my_strategy")
    """

    KEY = "my_strategy"

    def __init__(
        self,
        lookback_window: int = 20,
        entry_multiplier: float = 1.5,
        exit_multiplier: float = 0.5,
        use_close_only: bool = False,
        config: dict[str, Any] | None = None,
        metadata: StrategyMetadata | None = None,
    ) -> None:
        """
        Initialisiert Volatility-Breakout-Strategie.

        Args:
            lookback_window: Periode für gleitenden Durchschnitt und ATR
            entry_multiplier: ATR-Multiplikator für Entry (höher = konservativer)
            exit_multiplier: ATR-Multiplikator für Exit (niedriger = enger Stop)
            use_close_only: Wenn True, vereinfachte Volatilität nur aus Close
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "lookback_window": lookback_window,
            "entry_multiplier": entry_multiplier,
            "exit_multiplier": exit_multiplier,
            "use_close_only": use_close_only,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Volatility Breakout",
                description="ATR-basierte Volatility-Breakout-Strategie",
                version="1.0.0",
                author="Peak_Trade",
                regime="trending",
                tags=["breakout", "volatility", "atr", "momentum"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.lookback_window = int(self.config.get("lookback_window", lookback_window))
        self.entry_multiplier = float(self.config.get("entry_multiplier", entry_multiplier))
        self.exit_multiplier = float(self.config.get("exit_multiplier", exit_multiplier))
        self.use_close_only = bool(self.config.get("use_close_only", use_close_only))

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.lookback_window <= 1:
            raise ValueError(f"lookback_window ({self.lookback_window}) muss > 1 sein")
        if self.entry_multiplier <= 0:
            raise ValueError(f"entry_multiplier ({self.entry_multiplier}) muss > 0 sein")
        if self.exit_multiplier < 0:
            raise ValueError(f"exit_multiplier ({self.exit_multiplier}) muss >= 0 sein")
        if self.exit_multiplier >= self.entry_multiplier:
            raise ValueError(
                f"exit_multiplier ({self.exit_multiplier}) muss < entry_multiplier ({self.entry_multiplier}) sein"
            )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.my_strategy",
    ) -> MyStrategy:
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            MyStrategy-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> config = load_config()
            >>> strategy = MyStrategy.from_config(config)
        """
        lookback_window = cfg.get(f"{section}.lookback_window", 20)
        entry_multiplier = cfg.get(f"{section}.entry_multiplier", 1.5)
        exit_multiplier = cfg.get(f"{section}.exit_multiplier", 0.5)
        use_close_only = cfg.get(f"{section}.use_close_only", False)

        return cls(
            lookback_window=lookback_window,
            entry_multiplier=entry_multiplier,
            exit_multiplier=exit_multiplier,
            use_close_only=use_close_only,
        )

    def _compute_atr(self, data: pd.DataFrame) -> pd.Series:
        """
        Berechnet Average True Range (ATR).

        True Range = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )

        ATR = Rolling Mean von True Range

        Args:
            data: DataFrame mit high, low, close

        Returns:
            ATR als pd.Series
        """
        if self.use_close_only:
            # Vereinfachte Volatilität nur aus Close
            return data["close"].rolling(window=self.lookback_window).std()

        high = data["high"]
        low = data["low"]
        close = data["close"]
        prev_close = close.shift(1)

        # True Range Komponenten
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)

        # True Range = Maximum der drei Komponenten
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR = Rolling Mean
        atr = true_range.rolling(window=self.lookback_window, min_periods=self.lookback_window).mean()

        return atr

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit OHLCV-Daten (high, low, close erforderlich)

        Returns:
            Series mit Signalen (1=long, -1=exit, 0=neutral, Index=data.index)

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalten fehlen
        """
        # Validierung
        if "close" not in data.columns:
            raise ValueError(
                f"Spalte 'close' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        if not self.use_close_only:
            for col in ["high", "low"]:
                if col not in data.columns:
                    raise ValueError(
                        f"Spalte '{col}' nicht in DataFrame. "
                        f"Verfügbar: {list(data.columns)}"
                    )

        min_bars = self.lookback_window + 10
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mind. {min_bars} Bars, habe nur {len(data)}"
            )

        # MA und ATR berechnen
        ma = data["close"].rolling(window=self.lookback_window, min_periods=self.lookback_window).mean()
        atr = self._compute_atr(data)

        # Volatilitätsbänder
        upper_band = ma + (atr * self.entry_multiplier)
        lower_band = ma - (atr * self.exit_multiplier)

        # Signale initialisieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Entry-Bedingung: Close durchbricht obere Band
        entry_condition = data["close"] > upper_band

        # Exit-Bedingung: Close fällt unter untere Band
        exit_condition = data["close"] < lower_band

        # Entry: Vorherige Bar kein Entry, aktuelle Bar Entry
        prev_entry = entry_condition.shift(1).fillna(False).astype(bool)
        entry_trigger = entry_condition & ~prev_entry
        signals.loc[entry_trigger] = 1

        # Exit: Vorherige Bar kein Exit, aktuelle Bar Exit
        prev_exit = exit_condition.shift(1).fillna(False).astype(bool)
        exit_trigger = exit_condition & ~prev_exit
        signals.loc[exit_trigger] = -1

        return signals


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte MyStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (1=long, -1=exit, 0=neutral)

    Example:
        >>> signals = generate_signals(df, {"lookback_window": 20, "entry_multiplier": 1.5})
    """
    config = {
        "lookback_window": params.get("lookback_window", 20),
        "entry_multiplier": params.get("entry_multiplier", 1.5),
        "exit_multiplier": params.get("exit_multiplier", 0.5),
        "use_close_only": params.get("use_close_only", False),
    }

    strategy = MyStrategy(config=config)
    return strategy.generate_signals(df)


def get_strategy_description(params: dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    return f"""
Volatility Breakout Strategy (ATR-basiert)
===========================================
Lookback-Window:     {params.get('lookback_window', 20)} Bars
Entry-Multiplier:    {params.get('entry_multiplier', 1.5)} x ATR
Exit-Multiplier:     {params.get('exit_multiplier', 0.5)} x ATR
Close-Only:          {'Ja' if params.get('use_close_only', False) else 'Nein'}

Konzept:
- Entry: Close > MA + ({params.get('entry_multiplier', 1.5)} x ATR) (Breakout)
- Exit: Close < MA - ({params.get('exit_multiplier', 0.5)} x ATR) (Stop)

Geeignet für: Märkte mit klaren Breakouts nach Konsolidierung
"""
