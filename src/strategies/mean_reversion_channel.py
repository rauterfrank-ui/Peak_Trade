# src/strategies/mean_reversion_channel.py
"""
Peak_Trade Mean Reversion Channel Strategy (Phase 27)
=====================================================

Kanal-basierte Mean-Reversion-Strategie (Bollinger-ähnlich).

Konzept:
- Berechne einen Preiskanal basierend auf MA ± k*Std
- Long Entry: Preis schließt unter dem unteren Band (Übertreibung nach unten)
- Short Entry: Preis schließt über dem oberen Band (Übertreibung nach oben)
- Exit: Rückkehr in Richtung Mitte (optional: Timeout)

Diese Strategie eignet sich für seitwärts laufende (ranging) Märkte
und nutzt die Tendenz von Preisen, zu ihrem Mittelwert zurückzukehren.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from .base import BaseStrategy, StrategyMetadata


class MeanReversionChannelStrategy(BaseStrategy):
    """
    Mean Reversion Channel Strategy (Bollinger-ähnlich).

    Signale:
    - 1 (long): Close < lower_band (überverkauft → erwarte Reversion nach oben)
    - -1 (short): Close > upper_band (überkauft → erwarte Reversion nach unten)
    - 0: Position schließen wenn zurück im Kanal (zwischen bands)

    Args:
        window: Lookback für MA und Std-Berechnung (default: 20)
        num_std: Anzahl Standardabweichungen für Bänder (default: 2.0)
        exit_at_mean: Ob Exit bei Rückkehr zum Mean (default: True)
        max_holding_bars: Max. Haltedauer in Bars (default: None = unbegrenzt)
        price_col: Spalte für Preisdaten (default: "close")
        config: Optional Config-Dict (überschreibt Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = MeanReversionChannelStrategy(window=20, num_std=2.0)
        >>> signals = strategy.generate_signals(df)

        >>> # Oder aus Config
        >>> strategy = MeanReversionChannelStrategy.from_config(config)
    """

    KEY = "mean_reversion_channel"

    def __init__(
        self,
        window: int = 20,
        num_std: float = 2.0,
        exit_at_mean: bool = True,
        max_holding_bars: int | None = None,
        price_col: str = "close",
        config: dict[str, Any] | None = None,
        metadata: StrategyMetadata | None = None,
    ) -> None:
        """
        Initialisiert Mean Reversion Channel Strategy.

        Args:
            window: Lookback für MA und Std
            num_std: Anzahl Standardabweichungen für Bänder
            exit_at_mean: Exit bei Rückkehr zum Mean
            max_holding_bars: Maximale Haltedauer (None = unbegrenzt)
            price_col: Preis-Spalte
            config: Optional Config-Dict
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "window": window,
            "num_std": num_std,
            "exit_at_mean": exit_at_mean,
            "max_holding_bars": max_holding_bars,
            "price_col": price_col,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Mean Reversion Channel",
                description="Bollinger-ähnliche Mean-Reversion-Strategie",
                version="1.0.0",
                author="Peak_Trade",
                regime="ranging",
                tags=["mean_reversion", "bollinger", "channel", "ranging"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.window = int(self.config.get("window", window))
        self.num_std = float(self.config.get("num_std", num_std))
        self.exit_at_mean = bool(self.config.get("exit_at_mean", exit_at_mean))
        self.max_holding_bars = self.config.get("max_holding_bars", max_holding_bars)
        if self.max_holding_bars is not None:
            self.max_holding_bars = int(self.max_holding_bars)
        self.price_col = str(self.config.get("price_col", price_col))

        # Validierung
        self.validate()

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.window < 2:
            raise ValueError(f"window ({self.window}) muss >= 2 sein")
        if self.num_std <= 0:
            raise ValueError(f"num_std ({self.num_std}) muss > 0 sein")
        if self.max_holding_bars is not None and self.max_holding_bars < 1:
            raise ValueError(f"max_holding_bars ({self.max_holding_bars}) muss >= 1 sein")

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.mean_reversion_channel",
    ) -> MeanReversionChannelStrategy:
        """
        Fabrikmethode für Core-Config.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            MeanReversionChannelStrategy-Instanz
        """
        window = cfg.get(f"{section}.window", 20)
        num_std = cfg.get(f"{section}.num_std", 2.0)
        exit_at_mean = cfg.get(f"{section}.exit_at_mean", True)
        max_holding = cfg.get(f"{section}.max_holding_bars", None)
        price_col = cfg.get(f"{section}.price_col", "close")

        return cls(
            window=window,
            num_std=num_std,
            exit_at_mean=exit_at_mean,
            max_holding_bars=max_holding,
            price_col=price_col,
        )

    def _compute_bands(self, data: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        Berechnet Bollinger-ähnliche Bänder.

        Args:
            data: DataFrame mit price_col

        Returns:
            (middle, upper, lower) als pd.Series
        """
        price = data[self.price_col]

        # Rolling Mean und Std
        middle = price.rolling(window=self.window, min_periods=self.window).mean()
        std = price.rolling(window=self.window, min_periods=self.window).std()

        # Bänder
        upper = middle + self.num_std * std
        lower = middle - self.num_std * std

        return middle, upper, lower

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
        # Validierung
        if self.price_col not in data.columns:
            raise ValueError(
                f"Spalte '{self.price_col}' nicht in DataFrame. "
                f"Verfügbar: {list(data.columns)}"
            )

        min_bars = self.window + 10
        if len(data) < min_bars:
            raise ValueError(
                f"Brauche mind. {min_bars} Bars, habe nur {len(data)}"
            )

        # Bänder berechnen
        middle, upper, lower = self._compute_bands(data)
        price = data[self.price_col]

        # Signale initialisieren
        signals = pd.Series(0, index=data.index, dtype=int)

        # Entry-Bedingungen
        # Long: Preis unter dem unteren Band (überverkauft)
        long_entry = price < lower

        # Short: Preis über dem oberen Band (überkauft)
        short_entry = price > upper

        # Exit-Bedingung: Zurück in den Kanal / zum Mean
        if self.exit_at_mean:
            # Exit Long: Preis >= middle (zurück zum Mean)
            exit_long = price >= middle
            # Exit Short: Preis <= middle (zurück zum Mean)
            exit_short = price <= middle
        else:
            # Exit: Zurück in den Kanal (zwischen den Bändern)
            exit_long = price >= lower
            exit_short = price <= upper

        # Signale setzen
        # Entry Long: Neu unter lower
        prev_long = long_entry.shift(1).fillna(False).astype(bool)
        long_trigger = long_entry & ~prev_long
        signals[long_trigger] = 1

        # Entry Short: Neu über upper
        prev_short = short_entry.shift(1).fillna(False).astype(bool)
        short_trigger = short_entry & ~prev_short
        signals[short_trigger] = -1

        # State-Logik für Position-Tracking
        state = pd.Series(0, index=data.index, dtype=int)
        current_state = 0
        bars_in_position = 0

        for i in range(len(data)):
            data.index[i]
            signal = signals.iloc[i]

            if signal != 0:
                # Neuer Entry
                current_state = signal
                bars_in_position = 0
            elif current_state != 0:
                bars_in_position += 1

                # Check Exit-Bedingungen
                should_exit = False

                if current_state == 1:  # Long Position
                    if exit_long.iloc[i]:
                        should_exit = True
                elif current_state == -1:  # Short Position
                    if exit_short.iloc[i]:
                        should_exit = True

                # Timeout-Exit
                if self.max_holding_bars is not None and bars_in_position >= self.max_holding_bars:
                    should_exit = True

                if should_exit:
                    current_state = 0
                    bars_in_position = 0

            state.iloc[i] = current_state

        return state


# ============================================================================
# LEGACY API (Backwards Compatibility)
# ============================================================================


def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Legacy-Funktion für Backwards Compatibility mit alter API.

    DEPRECATED: Bitte MeanReversionChannelStrategy verwenden.

    Args:
        df: OHLCV-DataFrame
        params: Parameter-Dict

    Returns:
        Signal-Series (1=long, -1=short, 0=flat)
    """
    config = {
        "window": params.get("window", 20),
        "num_std": params.get("num_std", 2.0),
        "exit_at_mean": params.get("exit_at_mean", True),
        "max_holding_bars": params.get("max_holding_bars"),
        "price_col": params.get("price_col", "close"),
    }

    strategy = MeanReversionChannelStrategy(config=config)
    return strategy.generate_signals(df)


def get_strategy_description(params: dict) -> str:
    """Gibt Strategie-Beschreibung zurück."""
    max_hold = params.get('max_holding_bars', 'unbegrenzt')
    return f"""
Mean Reversion Channel Strategy (Bollinger-ähnlich)
===================================================
Window:            {params.get('window', 20)} Bars
Num Std:           {params.get('num_std', 2.0)}x
Exit at Mean:      {'Ja' if params.get('exit_at_mean', True) else 'Nein'}
Max Holding Bars:  {max_hold}
Price Column:      {params.get('price_col', 'close')}

Konzept:
- Entry Long:  Close < MA - {params.get('num_std', 2.0)} * Std (überverkauft)
- Entry Short: Close > MA + {params.get('num_std', 2.0)} * Std (überkauft)
- Exit:        Rückkehr zum {'Mean' if params.get('exit_at_mean', True) else 'Kanal'}
"""
