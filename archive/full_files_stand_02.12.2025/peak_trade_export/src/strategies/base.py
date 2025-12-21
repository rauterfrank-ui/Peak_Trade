"""
BaseStrategy: Abstrakte Basisklasse für alle Strategien.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import pandas as pd


class BaseStrategy(ABC):
    """
    Abstrakte Basis für Handelsstrategien.

    Alle Strategien müssen:
    - ein Attribut 'name' haben (str)
    - generate_signals() implementieren
    """

    name: str = "base"

    def __init__(self) -> None:
        """Initialisiert State-Dict."""
        self._state: Dict[str, Any] = {}
        self.reset_state()

    def reset_state(self) -> None:
        """Setzt internen State zurück."""
        self._state.clear()

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """
        Generiert Handelssignale aus Marktdaten.

        Args:
            df: DataFrame mit Marktdaten (mindestens 'close')
            params: Strategy-spezifische Parameter

        Returns:
            pd.Series mit Signals (-1, 0, +1)
        """
        ...

    def get_state(self) -> Dict[str, Any]:
        """Gibt Kopie des aktuellen State zurück."""
        return dict(self._state)
