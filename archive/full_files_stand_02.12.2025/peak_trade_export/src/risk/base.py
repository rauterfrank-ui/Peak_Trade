"""
BaseRiskModule: Abstrakte Basis für alle Risk-Module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class BaseRiskModule(ABC):
    """
    Abstrakte Basis für alle Risk-Module.

    Risk-Module transformieren Signale (z.B. Exposure -1..+1) in
    tatsächliche Positionsgrößen oder wenden Risk-Constraints an.

    Jedes Modul erhält:
    - df: vollständige Marktdaten
    - signals: ursprüngliche oder bereits transformierte Signale
    - prices: Serie der verwendeten Preise (z.B. df["close"])
    - initial_capital: Startkapital für Skalierung

    und gibt eine neue pd.Series zurück (gleicher Index).
    """

    @abstractmethod
    def apply(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        prices: pd.Series,
        initial_capital: float,
    ) -> pd.Series:
        """
        Wendet Risk-Logik auf Signale an.

        Args:
            df: Vollständige Marktdaten
            signals: Input-Signale (Exposure oder bereits Stückzahl)
            prices: Preis-Serie für Berechnungen
            initial_capital: Startkapital

        Returns:
            Transformierte Signale/Positionen (pd.Series)
        """
        ...
