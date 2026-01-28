# src/strategies/base.py
"""
Peak_Trade Strategy Baseclass
=============================
Abstrakte Basis für alle Trading-Strategien.

Contract:
- input: DataFrame mit OHLCV (mindestens 'close')
- output: pd.Series mit Ziel-Position (-1, 0, +1)

Jede Strategie MUSS implementieren:
- generate_signals(data: pd.DataFrame) -> pd.Series
- from_config(cfg, section: str) -> Self (Classmethod)

Jede Strategie KANN überschreiben:
- prepare(data: pd.DataFrame) -> None
- validate() -> None
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import pandas as pd

from ..core.errors import StrategyError

if TYPE_CHECKING:
    from typing_extensions import Self


@dataclass
class StrategyMetadata:
    """
    Metadaten für Strategien – gut für Logging, Doku, UI.

    Attributes:
        name: Kurzname der Strategie
        description: Ausführliche Beschreibung
        version: Versionsstring (SemVer)
        author: Autor/Team
        regime: Für welches Marktregime geeignet ("trending", "ranging", "any")
        tags: Optionale Tags für Kategorisierung
    """

    name: str
    description: str = ""
    version: str = "0.1.0"
    author: str = "Peak_Trade"
    regime: str = "any"
    tags: List[str] = field(default_factory=list)


class BaseStrategy(ABC):
    """
    Abstrakte Basis-Strategie.

    Contract:
    - input: DataFrame mit OHLCV (mindestens 'close')
    - output: pd.Series mit Ziel-Position:
        - 1  = long
        - -1 = short
        - 0  = flat

    Example:
        >>> class MyStrategy(BaseStrategy):
        ...     def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        ...         return pd.Series(0, index=data.index)
        ...
        ...     @classmethod
        ...     def from_config(cls, cfg, section: str = "strategy.my"):
        ...         return cls()
        ...
        >>> strategy = MyStrategy()
        >>> signals = strategy.generate_signals(df)
    """

    # Eindeutiger Registry-Key (wird von Subklassen überschrieben)
    KEY: str = ""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        self.config: Dict[str, Any] = config or {}
        self.meta: StrategyMetadata = metadata or StrategyMetadata(name=self.__class__.__name__)
        # Internal: Track whether prepare() was already run for a given DataFrame object.
        # We deliberately key by object identity (id(data)) to keep this lightweight and
        # avoid expensive hashing of large DataFrames.
        self._prepared_data_id: Optional[int] = None

    @property
    def key(self) -> str:
        """Eindeutiger Registry-Key der Strategie."""
        return self.KEY or self.__class__.__name__.lower()

    @classmethod
    @abstractmethod
    def from_config(cls, cfg: Any, section: str) -> "BaseStrategy":
        """
        Factory-Methode: Erstellt Strategie-Instanz aus Config.

        Args:
            cfg: Config-Objekt (PeakConfig oder kompatibel)
            section: Dotted-Path zum Config-Abschnitt (z.B. "strategy.ma_crossover")

        Returns:
            Strategie-Instanz

        Example:
            >>> from src.core.peak_config import load_config
            >>> cfg = load_config()
            >>> strategy = MACrossoverStrategy.from_config(cfg, "strategy.ma_crossover")
        """
        raise NotImplementedError

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert Handelssignale aus OHLCV-Daten.

        Args:
            data: DataFrame mit OHLCV-Daten (open, high, low, close, volume)

        Returns:
            Series mit Index = data.index, Werten in {-1, 0, 1}
            - 1 = Long-Position anstreben
            - -1 = Short-Position anstreben
            - 0 = Flat (keine Position)

        Raises:
            StrategyError: Bei fehlenden Spalten oder zu wenig Daten
        """
        raise NotImplementedError

    def prepare(self, data: pd.DataFrame) -> None:
        """
        Optionaler Pre-Processing-Schritt (z.B. teure Indikator-Berechnung).
        Kann von Subklassen überschrieben werden.

        Args:
            data: OHLCV-DataFrame
        """
        return

    def prepare_once(self, data: pd.DataFrame) -> None:
        """
        Führt `prepare()` höchstens einmal pro DataFrame-Objekt aus.

        Motivation:
        - `prepare()` ist für teure Vorberechnungen gedacht (Caching von Indikatoren, etc.).
        - Viele Call-Sites generieren Signale genau einmal für einen kompletten DataFrame.
          In solchen Flows soll `prepare()` genau einmal laufen, nicht mehrfach.

        Hinweis:
        - Das "Once" bezieht sich auf die *Objekt-Identität* des DataFrames (`id(data)`).
          Wenn Call-Sites einen neuen DataFrame erstellen (copy/slice), läuft `prepare()`
          erneut – das ist gewollt.
        """
        data_id = id(data)
        if self._prepared_data_id == data_id:
            return
        self.prepare(data)
        self._prepared_data_id = data_id

    def run(self, data: pd.DataFrame) -> pd.Series:
        """
        Empfohlener Entry-Point für Strategie-Ausführung:
        - ruft `prepare_once(data)` auf
        - ruft danach `generate_signals(data)` auf
        """
        self.prepare_once(data)
        return self.generate_signals(data)

    def validate(self) -> None:
        """
        Optionale Validierung der Strategie-Parameter.
        Kann von Subklassen überschrieben werden.

        Raises:
            StrategyError: Bei ungültigen Parametern
        """
        return

    def __repr__(self) -> str:
        params = ", ".join(f"{k}={v!r}" for k, v in self.config.items())
        return f"<{self.__class__.__name__}({params})>"
