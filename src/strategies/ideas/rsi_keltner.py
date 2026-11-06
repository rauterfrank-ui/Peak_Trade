"""
RSI + Keltner Reversion
=======================

Author notes — describe your strategy idea (concept, indicators, parameters).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

from ..base import BaseStrategy, StrategyMetadata


class RsiKeltnerStrategy(BaseStrategy):
    """
    RSI + Keltner Reversion Strategy.

    Add a detailed description (entry, exit, parameters).

    Args:
        param1: e.g. window length — document in your implementation
        param2: e.g. threshold — document in your implementation
        price_col: Spalte für Preisdaten (default: "close")
        config: Optional Config-Dict (überschreibt Konstruktor-Parameter)
        metadata: Optional StrategyMetadata

    Example:
        >>> strategy = RsiKeltnerStrategy(param1=20, param2=0.02)
        >>> signals = strategy.generate_signals(df)
    """

    def __init__(
        self,
        param1: int = 20,
        param2: float = 0.02,
        price_col: str = "close",
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert RSI + Keltner Reversion Strategy.

        Args:
            param1: Primary numeric parameter (see class docstring).
            param2: Secondary parameter (see class docstring).
            price_col: Preis-Spalte
            config: Optional Config-Dict (überschreibt Parameter)
            metadata: Optional Metadata
        """
        # Config zusammenbauen
        initial_config = {
            "param1": param1,
            "param2": param2,
            "price_col": price_col,
        }

        # Config-Override falls übergeben
        if config:
            initial_config.update(config)

        # Default Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="RSI + Keltner Reversion",
                description="RSI + Keltner Reversion Strategy",
                version="0.1.0",
                author="Peak_Trade",
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Parameter extrahieren
        self.param1 = self.config.get("param1", param1)
        self.param2 = self.config.get("param2", param2)
        self.price_col = self.config.get("price_col", price_col)

        # Optional: Parameter validieren
        self._validate_params()

    def validate(self) -> None:
        """Validiert Parameter (expliziter Aufruf für Backtests/CLI)."""
        self._validate_params()

    def _validate_params(self) -> None:
        """
        Validiert Parameter.

        Extend validation as needed for your strategy (ranges, combinations).
        """
        if self.param1 < 1:
            raise ValueError(f"param1 muss >= 1 sein, ist {self.param1}")
        if self.param2 <= 0:
            raise ValueError(f"param2 muss > 0 sein, ist {self.param2}")

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.ideas.rsi_keltner",
    ) -> RsiKeltnerStrategy:
        """Erstellt die Strategie aus einem Config-Objekt mit ``cfg.get(path, default)``."""
        p1 = cfg.get(section + ".param1", 20)
        p2 = cfg.get(section + ".param2", 0.02)
        price = cfg.get(section + ".price_col", "close")
        return cls(param1=p1, param2=p2, price_col=price)

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Implement your strategy logic (indicators, entry/exit, event→state).

        Args:
            data: DataFrame mit OHLCV-Daten (mindestens self.price_col)

        Returns:
            ``pd.Series`` (int), typischerweise Werte in ``{-1, 0, 1}``; Index wie ``data.index``.

        Raises:
            ValueError: Wenn zu wenig Daten oder Spalte fehlt
        """
        # Validierung
        if self.price_col not in data.columns:
            raise ValueError(
                f"Spalte '{self.price_col}' nicht in DataFrame. Verfügbar: {list(data.columns)}"
            )

        min_bars = self.param1  # Beispiel: Mindestens param1 Bars benötigt
        if len(data) < min_bars:
            raise ValueError(f"Brauche mindestens {min_bars} Bars, habe nur {len(data)}")

        # Kopie für Berechnungen
        df = data.copy()

        # ====================================================================
        # Author implementation: strategy logic
        # ====================================================================

        # Beispiel: Indikatoren berechnen
        # df["rsi"] = compute_rsi(df[self.price_col], window=14)
        # df["upper_band"], df["lower_band"] = compute_keltner_channels(df, atr_mult=2.0)

        # Beispiel: Entry-/Exit-Bedingungen
        # long_entry = (df["rsi"] < 30) & (df["close"] < df["lower_band"])
        # long_exit = df["rsi"] > 70

        # Beispiel: Signale aus Events erzeugen
        # events = pd.Series(0, index=df.index, dtype=int)
        # events[long_entry] = 1
        # events[long_exit] = -1

        # Beispiel: Event → State (1=long, 0=flat)
        # state = events.replace({-1: 0})
        # state = state.replace(0, pd.NA).ffill().fillna(0)
        # state = state.infer_objects(copy=False).astype(int)

        # ====================================================================
        # PLACEHOLDER: Gib erstmal nur 0 (flat) zurück
        # ====================================================================
        signals = pd.Series(0, index=df.index, dtype=int)

        return signals

    def get_config_dict(self) -> Dict[str, Any]:
        """
        Gibt Config als Dict zurück (nützlich für Logging/Experiment-Tracking).

        Returns:
            Dict mit allen relevanten Parametern
        """
        return {
            "param1": self.param1,
            "param2": self.param2,
            "price_col": self.price_col,
        }


# ============================================================================
# HELPER (Optional)
# ============================================================================


def create_strategy_from_params(**kwargs) -> RsiKeltnerStrategy:
    """
    Helper-Funktion zum Erstellen einer Strategie aus Keyword-Args.

    Beispiel:
        >>> strat = create_strategy_from_params(param1=10, param2=0.01)
    """
    return RsiKeltnerStrategy(**kwargs)
